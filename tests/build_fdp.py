import os
import requests
from pathlib import Path
import json
import subprocess
import time

FDP_BASE_URL = "http://localhost/"
FDP_BASE_VERSION = "1.18.1"
EMAIL = "albert.einstein@example.com"
PASSWORD = "password"


# Step 1: Authenticate and get token
def get_token():
    response = requests.post(
        f"{FDP_BASE_URL}/tokens",
        json={"email": EMAIL, "password": PASSWORD},
        headers={"Accept": "application/json", "Content-Type": "application/json"}
    )
    return response.json()["token"]

# Step 2: Get all metadata schemas
def get_schemas(token):
    response = requests.get(
        f"{FDP_BASE_URL}/metadata-schemas",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"}
    )
    return response.json()

# Step 3: Parse schema definitions to find UUIDs linked to resource types
def extract_schema_uuids(schemas, target_type="dcat:Catalog"):
    matches = []

    for schema in schemas:
        uuid = schema.get("uuid")
        latest = schema.get("latest", "")
        definition = latest.get("targetClasses", "")

        # Technique 2: Simple substring search
        if target_type in definition:
            matches.append((uuid, schema))

    return matches

# Step 4: Update schema using SHACL file
def update_schema(uuid, token, shacl_file_path, context):
    with open(shacl_file_path, "r") as f:
        shacl_data = f.read()
    
    attributes = context['latest']
    body = json.dumps({
        "name": attributes["name"],
        "description": attributes["description"],
        "extendsSchemaUuids": attributes["extendsSchemaUuids"],
        "suggestedResourceName": attributes["suggestedResourceName"],
        "suggestedUrlPrefix": attributes["suggestedUrlPrefix"],
        "definition": shacl_data,
        "lastVersion": "1.0.0"
    })

    response = requests.put(
        f"{FDP_BASE_URL}/metadata-schemas/{uuid}/draft",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        data=body
    )

    return response.status_code, response.text


def publish_schema(uuid, token, version, desc):

    body = json.dumps({"version": f"{version}","description": f"{desc}","published": True})
    response = requests.post(
        f"{FDP_BASE_URL}/metadata-schemas/{uuid}/versions",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        data=body
    )
    return response.status_code, response.text
# add a docker down command every run
#subprocess.run(["docker", "compose", "down"], cwd=compose_dir)

# Main execution
def setup():
    # Step 1: Set environment variables
    #TODO make a config
    os.environ["FDP_CLIENT_VERSION"] = FDP_BASE_VERSION
    os.environ["FDP_VERSION"] = FDP_BASE_VERSION

    #Step 2: Run Docker Compose to start FDP ephemeral server
    compose_dir = Path("tests\\test_integration\\compose\\fdp\\ephemeral\\v1")  # Update this path
    subprocess.run(["docker", "compose", "up", "-d"], cwd=compose_dir)

    status_code = 0
    while status_code != 200:
        response = requests.get(FDP_BASE_URL)
        status_code = response.status_code
    token = get_token()
    schemas = get_schemas(token)

    resource_schemas = extract_schema_uuids(schemas, "http://www.w3.org/ns/dcat#Resource")

    # print("Schemas linked to dcat:Resource:")
    uuid, context = resource_schemas[0]

    # Update the first matching schema
    if resource_schemas:
        schema_uuid = resource_schemas[0][0]
        
        status, message = update_schema(schema_uuid, token, "tests/test_files/SHACL/Resource.ttl", context)
        # print(f"Update status: {status}")
        # print(f"Response: {message}")
        time.sleep(2)
        publish_schema(schema_uuid, token, "2.0.0", "test_upload")

    else:
        raise Exception("No matching schemas found for dcat:Resource.")


    # Show different parsing methods
    catalog_schemas = extract_schema_uuids(schemas, "http://www.w3.org/ns/dcat#Catalog")
    # print("Schemas linked to dcat:Catalog:")
    uuid, context = catalog_schemas.next()

    # Update the first matching schema
    if catalog_schemas:
        schema_uuid = catalog_schemas[0][0]
        
        status, message = update_schema(schema_uuid, token, "tests/test_files/SHACL/Catalog.ttl", context)
        # print(f"Update status: {status}")
        # print(f"Response: {message}")
        time.sleep(2)
        publish_schema(schema_uuid, token, "2.0.0", "test_upload")

    else:
        raise Exception("No matching schemas found for dcat:Catalog.")

    dataset_schemas = extract_schema_uuids(schemas, target_type="http://www.w3.org/ns/dcat#Dataset")
    print("Schemas linked to dcat:Dataset:")
    uuid, context = catalog_schemas.next()

    # Update the first matching schema
    if dataset_schemas:
        schema_uuid = dataset_schemas[0][0]
        status, message = update_schema(schema_uuid, token, "tests/test_files/SHACL/Dataset.ttl", context)
        # print(f"Update status: {status}")
        # print(f"Response: {message}")
        time.sleep(2)
        publish_schema(schema_uuid, token, "2.0.0", "test_upload")

    else:
        raise Exception("No matching schemas found for dcat:Dataset.")
    
    #subprocess.run(["docker", "compose", "down"], cwd=compose_dir)