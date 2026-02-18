from rdflib import URIRef, DCTERMS, BNode, Literal, XSD, DCAT, Graph, Dataset, RDF, FOAF
from rdflib.plugins.sparql import prepareUpdate
from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

from fdp.FDPClient import FDPClient
from os import getenv
import yaml

from datetime import datetime
import pandas as pd
import keyring
from pymssql import connect

conf_path = getenv("CONF_PATH", default="config/configuration.yaml")

# get default values from config file
with open(conf_path, "r") as config_file:
    config = yaml.safe_load(config_file)

def connect_client():
    ### set up connection settings to FDP server ###
    URL = URIRef(config["FDP"]["URL"])
    PURL = URIRef(config["FDP"]["PURL"])
    client = FDPClient(URL, config["keyring"]["username"], keyring.get_password(config["keyring"]["fdp_service"], config["keyring"]["username"]), PURL)
    # ping server:
    client.check_url(URL)
    return URL, PURL, client

URL, PURL, client = connect_client()
catalog_file_path = config["file_paths"]["catalog_input_file"]
datasets_file_path = config["file_paths"]["datasets_input_file"]
catalog_shacl_path = config["file_paths"]["catalog_shacl"]
dataset_shacl_path = config["file_paths"]["dataset_shacl"]


#def dataset_sql_query()

input_format = config["mode"]["input_format"]

if input_format == "Excel":
    excel_parsing()
elif input_format == "csv":
    csv_parsing()
elif input_format == "SQL":
    conn = connect(server=config["SQL"]["server_name"],user=config["SQL"]["username"],password=keyring.get_password(service_name=config["SQL"]["keyring_service"], username=config["SQL"]["username"]), database=config["SQL"]["database_name"],tds_version="7.4")
    cursor = conn.cursor(as_dict=True)
    if config["mode"]["replace"] == True:
        parser.add_csv_catalog()
        #TODO
    elif config["mode"]["replace"] == False:
        catalog_table = catalog_sql_query(cursor)
        for catalog in catalog_table:
            parser.pydantic_catalog(pd.Series(catalog), parser.graph, url=URL + "/new")
            subject_replace(PURL + "new", BNode("Catalog"), DCAT.Catalog, parser.graph)
            catalog_purl = upload_resource(parser.graph, URL, resource_type=DCAT.Catalog)
            for dataset_id in catalog["datasets"].split(","):
                dataset_metadata = dataset_sql_query(cursor, dataset_id).__next__()
                parser.pydantic_dataset(pd.Series(dataset_metadata), parser.graph, PURL)
            dataset_list = get_dataset_nodes(parser.graph)
            for node_id in dataset_list:
                dataset_graph = parser.graph.cbd(node_id[0])
                subject_replace(PURL + "new", node_id[0], DCAT.Dataset, dataset_graph)
                dataset_graph.remove((BNode(node_id[0]), None, None))
                link_resource(dataset_graph, catalog_purl, DCAT.Dataset)
                upload_resource(dataset_graph, catalog_purl, resource_type=DCAT.Dataset, resource_name="Dataset")

    else:
        raise AttributeError("Please use either True or False for replacement mode")