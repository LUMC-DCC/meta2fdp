import os
import requests
from pathlib import Path
import json
import subprocess
import time
import keyring
import pytest


verbose = True


# Step 1: Authenticate and get token
def get_apikey():
    """Obtain an API key for the FDP server using credentials from environment variables."""
    response = requests.post(
        f"{os.environ['FDP_BASE_URL']}/tokens",
        data=json.dumps(
            {"email": os.environ["FDP_EMAIL"], "password": os.environ["FDP_PASSWORD"]}
        ),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to obtain token from {os.environ['FDP_BASE_URL']}/tokens: {response.status_code} {response.text}"
        )
    try:
        token = response.json().get("token")
    except ValueError:
        raise RuntimeError("Invalid JSON response when obtaining token")
    if not token:
        raise RuntimeError(f"No token found in response: {response.text}")
    return set_apikey(token)


def set_apikey(token):
    """Store the obtained API key in the FDP system keyring for later retrieval."""
    response = requests.post(
        f"{os.environ['FDP_BASE_URL']}/api-keys",
        json={},
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Failed to create API key at {os.environ['FDP_BASE_URL']}/api-keys: {response.status_code} {response.text}"
        )
    try:
        return response.json()["token"]
    except Exception:
        raise RuntimeError(f"No token returned when creating API key: {response.text}")


# Step 2: Get all metadata schemas
def get_schemas(token):
    """Retrieve all metadata schemas from the FDP server using the provided API token."""
    response = requests.get(
        f"{os.environ['FDP_BASE_URL']}/metadata-schemas",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    return response.json()


# Step 3: Parse schema definitions to find UUIDs linked to resource types
def extract_schema_uuids(schemas, target_type="dcat:Catalog"):
    """Extract UUIDs of metadata schemas that are relevant to the specified target resource type."""
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
def post_schema(uuid, token, shacl_file_path, context):
    """Post an updated metadata schema to the FDP server using the provided SHACL file and context."""
    with open(shacl_file_path, "r") as f:
        shacl_data = f.read()

    attributes = context["latest"]
    body = json.dumps(
        {
            "name": attributes["name"],
            "description": attributes["description"],
            "extendsSchemaUuids": attributes["extendsSchemaUuids"],
            "suggestedResourceName": attributes["suggestedResourceName"],
            "suggestedUrlPrefix": attributes["suggestedUrlPrefix"],
            "definition": shacl_data,
            "lastVersion": "1.0.0",
        }
    )

    response = requests.put(
        f"{os.environ['FDP_BASE_URL']}/metadata-schemas/{uuid}/draft",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        data=body,
    )

    return response.status_code, response.text


def publish_schema(uuid, token, version, desc):
    """Publish the updated metadata schema on the FDP server with the specified version and description."""
    body = json.dumps(
        {"version": f"{version}", "description": f"{desc}", "published": True}
    )
    response = requests.post(
        f"{os.environ['FDP_BASE_URL']}/metadata-schemas/{uuid}/versions",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        data=body,
    )
    return response.status_code, response.text


# add a docker down command every run
# subprocess.run(["docker", "compose", "down"], cwd=compose_dir)


def update_schema(schemas, token, resource):
    """Find the schema UUID for the given resource type and update it using the corresponding SHACL file."""
    resource_schemas = extract_schema_uuids(
        schemas, f"http://www.w3.org/ns/dcat#{resource}"
    )
    if resource_schemas:
        schema_uuid, context = resource_schemas[0]

        status, message = post_schema(
            schema_uuid, token, f"tests/data/schema/{resource}.ttl", context
        )
        if __debug__:
            print(status)
            print(message)
        publish_schema(schema_uuid, token, "2.0.0", f"HRIv2.0.2{resource}")
        if verbose:
            print(f"{resource} schema updated at: {schema_uuid}")
    else:
        raise Exception(f"No matching schemas found for dcat:{resource}.")


# Main execution
def setup(compose_dir=None, config=None):
    """Set up the environment by starting the FDP server, obtaining API tokens, and updating schemas."""
    # Step 1: Set environment variables
    # use .env.test file for env vars related to the ephemeral FDP server setup
    os.environ["FDP_CLIENT_VERSION"] = os.environ["FDP_BASE_VERSION"]
    os.environ["FDP_VERSION"] = os.environ["FDP_BASE_VERSION"]

    # Step 2: Run Docker Compose to start FDP ephemeral server
    subprocess.run(["docker", "compose", "up", "-d"], cwd=compose_dir)

    # set up token secrets environment for ephemeral usecase:
    status_code = 0
    tries = 0
    max_tries = int(
        os.environ.get("FDP_START_TIMEOUT", 40)
    )  # Default to 40 seconds if not set
    while status_code != 200 and tries < max_tries:
        tries += 1
        try:
            response = requests.get(os.environ["FDP_BASE_URL"])
        except requests.exceptions.ConnectionError:
            time.sleep(1)
            continue
        status_code = response.status_code
        if status_code != 200:
            print(
                f"FDP not ready yet, status code: {status_code}. Retrying in 1 seconds..."
            )
            time.sleep(1)
    if status_code != 200:
        raise Exception("FDP server did not start within the expected time.")
    token = get_apikey()
    # keyring.delete_password(FDP_BASE_URL,EMAIL)
    keyring.set_password(os.environ["FDP_BASE_URL"], os.environ["FDP_EMAIL"], token)
    os.environ[config["FDP"]["URL"]] = os.environ["FDP_BASE_URL"]
    os.environ[config["FDP"]["username"]] = os.environ["FDP_EMAIL"]

    # update schemas to the ones in the folder tests\data\schema
    schemas = get_schemas(token)
    update_schema(schemas, token, "Resource")
    update_schema(schemas, token, "Catalog")
    update_schema(schemas, token, "Dataset")


def teardown(compose_dir, config=None):
    """Tear down the environment by stopping the FDP server and cleaning up environment variables and keyring entries."""
    subprocess.run(["docker", "compose", "down"], cwd=compose_dir)
    # cleanup env vars and keyring set by build_fdp.setup() to avoid cross-test pollution
    try:
        if config:
            env_key = config["FDP"]["URL"]
            username_key = config["FDP"]["username"]
            if env_key in os.environ:
                del os.environ[env_key]
            if username_key in os.environ:
                del os.environ[username_key]
        # remove any API token saved in keyring for the FDP base URL
        try:
            keyring.delete_password(os.environ["FDP_BASE_URL"], os.environ["FDP_EMAIL"])
        except Exception:
            pass
    except Exception:
        pass


@pytest.fixture(scope="session")
def fdp_server(config):
    """Start an ephemeral FDP server for the test session and yield control.

    This fixture wraps the existing `setup()` and `teardown()` helpers and
    uses the `config` fixture to set environment variables.
    """
    compose_dir = Path(os.environ["FDP_COMPOSE_PATH"]).resolve()

    setup(config=config, compose_dir=compose_dir)
    try:
        yield
    finally:
        teardown(compose_dir, config=config)
