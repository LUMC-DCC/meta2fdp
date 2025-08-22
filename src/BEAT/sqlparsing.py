"""
Adapter class for MSSQL database to FDP with health-ri v2.0.0 
"""
from rdflib import URIRef, BNode, DCAT, Namespace
import yaml
import pandas as pd
import keyring
from pymssql import connect
from converter import Converter
from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))

from fdp.FDPClient import FDPClient
from os import getenv



class SQLparser(Converter):

    def __init__(self, config, client, class_map=None, debug=False):
        super().__init__(class_map, debug)
        self.config = config
        self.client = client
        self.VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")

    def dataset_sql_query(self, cursor, dataset_id):

        def dataset_sql_query_constructor(table_name, dataset_id) -> str:
            dataset_query = "select * from " + str(table_name) + " where identifier = '" + str(dataset_id) + "';"
            return dataset_query
        
        table_name = self.config["SQL"]["dataset_id"]
        dataset_query = dataset_sql_query_constructor(table_name, dataset_id)
        cursor.execute(dataset_query)
        return cursor

    def catalog_sql_query(self, cursor):

        def catalog_sql_query_constructor(table_name) -> str:
            catalog_query = "select * from "  + str(table_name) + ";"
            return catalog_query
        
        catalog_query = catalog_sql_query_constructor(self.config["SQL"]["catalog_id"])
        cursor.execute(catalog_query)
        return cursor

    def connect_to_sql(self):
        conn = connect(server=self.config["SQL"]["server_name"],user=self.config["SQL"]["username"],password=keyring.get_password(service_name=self.config["SQL"]["keyring_service"], username=self.config["SQL"]["username"]), database=self.config["SQL"]["database_name"],tds_version="7.4")
        cursor = conn.cursor(as_dict=True)
        return cursor
    
    def parse(self):
        cursor = self.connect_to_sql()
        catalog_table = self.catalog_sql_query(cursor)
        for catalog in catalog_table:
            self.sempyro_catalog(pd.Series(catalog), self.graph, url=self.client.URL + "/new")
            self.subject_replace(self.client.PURL + "new", BNode("Catalog"), DCAT.Catalog, self.graph)
            catalog_purl = client.upload_resource(self.graph, self.client.URL, resource_type=DCAT.Catalog)
            for dataset_id in catalog["datasets"].split(","):
                dataset_metadata = self.dataset_sql_query(cursor, dataset_id).__next__()
                self.sempyro_dataset(pd.Series(dataset_metadata), self.graph, self.client.PURL)
            dataset_list = self.get_dataset_nodes(self.graph)
            for node_id in dataset_list:
                dataset_graph = self.graph.cbd(node_id[0])
                self.subject_replace(self.client.PURL + "new", node_id[0], DCAT.Dataset, dataset_graph)
                dataset_graph.remove((BNode(node_id[0]), None, None))
                client.link_resource(dataset_graph, catalog_purl, DCAT.Dataset)
                client.upload_resource(dataset_graph, catalog_purl, resource_type=DCAT.Dataset, resource_name="Dataset")
        
    def dataservice_rdf(self, metadata, graph):
        return super().dataservice_rdf(metadata, graph)
    
    def dataset_rdf(self, metadata, graph):
        return super().dataset_rdf(metadata, graph)
    
    def datasetseries_rdf(self, metadata, graph):
        return super().datasetseries_rdf(metadata, graph)
    
    def distribution_rdf(self, metadata, graph):
        return super().distribution_rdf(metadata, graph)


if __name__ == "__main__":
    ## TODO should be done in the main:
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
    parser = SQLparser(config, client)
    parser.parse()

    
