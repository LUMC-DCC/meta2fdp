"""
Adapter class from csv to FDP
"""
from rdflib import URIRef, DCTERMS, BNode, Literal, XSD, DCAT, Graph, Dataset, RDF, FOAF
import pandas as pd
from converter import Converter
import keyring
from fdp.FDPClient import FDPClient
import yaml
from os import getenv


class CSVParser(Converter):

    def __init__(self, config, client, class_map=None, debug=False):
        super().__init__(class_map, debug)
        self.client = client
        self.config = config


    def replace_catalog(self, catalog_metadata: pd.Series, targeturl: URIRef) -> list:
        catalog = self.catalog_rdf(catalog_metadata, self.graph, self.client.URL + "/new") # fix catalog generator
        self.subject_replace(self.client.PURL + "new", BNode("Catalog"), DCAT.Catalog, self.graph)
        datasets_fdp_ids = self.client.update_catalog(targeturl, catalog)
        return datasets_fdp_ids


    def replace_dataset(self, dataset targeturl=None):
        self.dataset_rdf(dataset, self.graph, URL + "/new") # fix catalog generator
        self.subject_replace(PURL + "new", BNode("Catalog"), DCAT.Catalog, self.graph)
        catalog_purl = config["FDP"]["catalog_purl"]
        datasets_fdp_ids = self.client.update_resource(catalog_purl, self.graph)


    def parse(self, catalog_file_path, datasets_file_path):
        cat_table = pd.read_csv(catalog_file_path,sep=";",header=0)
        for catalog in cat_table.iterrows():
            self.sempyro_catalog(catalog, self.graph, URL + "/new")
            self.subject_replace(PURL + "new", BNode("Catalog"), DCAT.Catalog, self.graph)
            # catalog_purl = "https://fdp.example.org/catalog/d66222dc-c95c-4b83-874d-7764f5475173"
            if self.config["mode"]["replace"] == True:
                catalog_purl = self.config["FDP"]["catalog_purl"]
                datasets_fdp_ids = self.client.update_catalog(catalog_purl, self.graph)
            else:
                catalog_purl = self.client.upload_resource(self.graph, URL, resource_type=DCAT.Catalog)
            dat_table = pd.read_csv(datasets_file_path, sep=";",header=0) # get data
            for dataset in dat_table.iterrows():
                self.sempyro_dataset(dataset, self.graph, PURL) # TODO ADD AGENT IDENTIFIER AS BLANK NODE ID
            dataset_list = self.get_dataset_nodes(self.graph)
            for node_id in dataset_list:
                dataset_graph = self.graph.cbd(node_id[0])
                self.subject_replace(PURL + "new", node_id[0], DCAT.Dataset, dataset_graph)
                dataset_graph.remove((BNode(node_id[0]), None, None))
                self.client.link_resource(dataset_graph, catalog_purl, DCAT.Dataset)
                self.client.upload_resource(dataset_graph, catalog_purl, resource_type=DCAT.Dataset, resource_name="Dataset")

    def update(self, catalog_file_path, dataset_file_path):
        raise NotImplementedError()


if __name__ == "__main__":
    ## TODO should be done in the main.py:
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
    parser = CSVParser(config, client)
    parser.parse(catalog_file_path=config["file_paths"]["catalog_input_file"],datasets_file_path=config["file_paths"]["datasets_input_file"])
