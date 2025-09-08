from rdflib import URIRef, DCTERMS, BNode, Literal, XSD, DCAT, Graph, Dataset, RDF, FOAF
from rdflib.plugins.sparql import prepareUpdate
from excelparser import ExcelParser
from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

from fdp.FDPClient import FDPClient
from os import getenv
import yaml
import json
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





def excel_parsing():
    parser = ExcelParser(catalog_file_path)
    parser.parse_catalog(shacl=catalog_shacl_path)
    parser.subject_replace(PURL + "new", BNode("Catalog"), DCAT.Catalog, parser.graph)
    if config["mode"]["replace"] == True:
        catalog_purl = config["FDP"]["catalog_purl"]
        datasets_fdp_ids = update_catalog(catalog_purl, parser.graph)
    else:
        catalog_purl = client.upload_resource(parser.graph, URL, resource_type=DCAT.Catalog)
    print("datasets")
    parser.parse_dataset(datasets_file_path, shacl=dataset_shacl_path)
    catalog_description = next(parser.graph.triples((None, DCTERMS.description, None)))
    
    for dataset_node_id in parser.dataset_ids:
        dataset = parser.graph.cbd(BNode(dataset_node_id))
        dataset.remove((BNode(dataset_node_id), DCTERMS.isReferencedBy, Literal("Links to BEAT publications:")))
        dataset.remove((BNode(dataset_node_id), DCTERMS.isReferencedBy, Literal("Links to BEAT publications")))
        if catalog_file_path == "data/BEAT/Health-RI Core Metadata model v2 filled BEAT.xlsx":
            dataset.add((BNode(dataset_node_id), DCTERMS.issued, Literal(datetime(year=2024,month=2, day=4).isoformat(), datatype=XSD.dateTime)))
            dataset.add((BNode(dataset_node_id), DCTERMS.modified, Literal(datetime(year=2024,month=2, day=4).isoformat(), datatype=XSD.dateTime)))
        elif catalog_file_path == "data/BEAT/Health-RI Core Metadata model v2 filled Comodulate.xlsx":
            dataset.add((BNode(dataset_node_id), DCTERMS.issued, Literal(datetime(year=2025,month=4, day=4).isoformat(), datatype=XSD.dateTime)))
            dataset.add((BNode(dataset_node_id), DCTERMS.modified, Literal(datetime(year=2025,month=4, day=4).isoformat(), datatype=XSD.dateTime)))
        dataset.add((BNode(dataset_node_id), DCTERMS.license, URIRef(config["default_values_metadata"]["license"])))
        dataset.add((BNode(dataset_node_id), URIRef("http://data.europa.eu/r5r/applicableLegislation")  , URIRef("http://data.europa.eu/eli/reg/2025/327/oj")))
        # add catalog description:
        dataset.add((BNode(dataset_node_id), DCTERMS.description, catalog_description[2]))
        parser._merge_desc(BNode(dataset_node_id), dataset)
        parser.subject_replace(PURL + "new", BNode(dataset_node_id), DCAT.Dataset, dataset) # replace mode also assumes FDP resource PURL
        dataset_upload(dataset, datasets_fdp_ids, catalog_purl)

def csv_parsing():
    parser = 
    cat_table = pd.read_csv(catalog_file_path,sep=";",header=0)
    for catalog in cat_table.iterrows():
        parser.pydantic_catalog(catalog, parser.graph, URL + "/new")
        subject_replace(PURL + "new", BNode("Catalog"), DCAT.Catalog, parser.graph)
        # catalog_purl = "https://fdp.example.org/catalog/d66222dc-c95c-4b83-874d-7764f5475173"
        if config["mode"]["replace"] == True:
            catalog_purl = config["FDP"]["catalog_purl"]
            datasets_fdp_ids = update_catalog(catalog_purl, parser.graph)
        else:
            catalog_purl = upload_resource(parser.graph, URL, resource_type=DCAT.Catalog)
        dat_table = pd.read_csv(datasets_file_path, sep=";",header=0) # get data
        for dataset in dat_table.iterrows():
            parser.pydantic_dataset(dataset, parser.graph, PURL) # TODO ADD AGENT IDENTIFIER AS BLANK NODE ID
        dataset_list = get_dataset_nodes(parser.graph)
        for node_id in dataset_list:
            dataset_graph = parser.graph.cbd(node_id[0])
            subject_replace(PURL + "new", node_id[0], DCAT.Dataset, dataset_graph)
            dataset_graph.remove((BNode(node_id[0]), None, None))
            link_resource(dataset_graph, catalog_purl, DCAT.Dataset)
            upload_resource(dataset_graph, catalog_purl, resource_type=DCAT.Dataset, resource_name="Dataset")

def dataset_sql_query(cursor, dataset_id):

    def dataset_sql_query_constructor(table_name, dataset_id) -> str:
        dataset_query = "select * from " + str(table_name) + " where identifier = '" + str(dataset_id) + "';"
        return dataset_query
    
    table_name = config["SQL"]["dataset_id"]
    dataset_query = dataset_sql_query_constructor(table_name, dataset_id)
    cursor.execute(dataset_query)
    return cursor

def catalog_sql_query(cursor):

    def catalog_sql_query_constructor(table_name) -> str:
        catalog_query = "select * from "  + str(table_name) + ";"
        return catalog_query
    
    catalog_query = catalog_sql_query_constructor(config["SQL"]["catalog_id"])
    cursor.execute(catalog_query)
    return cursor

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