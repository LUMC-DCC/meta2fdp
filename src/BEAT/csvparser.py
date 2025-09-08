"""
Adapter class from csv to FDP
"""
from rdflib import URIRef, BNode, DCAT, DCTERMS
import pandas as pd
from converter import Converter
import keyring


from pathlib import Path
import sys
path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))
from fdp.FDPClient import FDPClient
from graphutils import * # TODO: figure out if utils functions should be integrated into the client and converter classes

import yaml
from os import getenv


class CSVParser(Converter):

    def __init__(self, config: dict, client: FDPClient, class_map=None, debug=False):
        super().__init__(class_map, debug)
        self.client = client
        self.config = config


    def replace_catalog(self, catalog_metadata: pd.Series, targeturl: URIRef) -> list:
        catalog_id = self.sempyro_catalog(catalog_metadata, self.graph, self.client.URL + "/new") # fix catalog generator
        subject_replace(self.client.PURL + "new", BNode("Catalog"), DCAT.Catalog, self.graph)
        new_catalog = self.client.update_catalog(targeturl, self.graph.cbd(catalog_id)) # update catalog and retrieve a list of child nodes.
        return new_catalog


    def replace_datasets(self, targeturl):
        # TODO This is inefficient: we get the data to get a list of identifiers to match
        # Figure out a way to reduce API calls to match parsed dataset with FDP datasets
        FDP_cat_content = self.client.get_metadata(targeturl)
        FDP_cat_graph = Graph()# use the internal function to generate a HRI compatible graph (take only the graph and not the prefix map made by the function) and parse the metadata on the FDP into a local graph
        FDP_cat_graph.parse(data=FDP_cat_content)
        FDP_dataset_ids = self.client.get_dataset_id_purls(FDP_cat_graph) # get FDP datsasets ids (should be published)
        #HACK current implementation assumes that all datasets in file should
        # be updated
        for dataset_id in self.dataset_ids: # get internal node id for datasets in local graph
            if dataset_id in FDP_dataset_ids.keys(): #FIXME does not work on END CURA BOT
                dataset = self.graph.cbd(dataset_id)
                local_dataset_identifier = dataset.value(subject=URIRef(PURL + "new"),
                                                predicate=DCTERMS.identifier)
                matching_purl = FDP_dataset_ids[local_dataset_identifier]
                self.client.update_resource(matching_purl, DCAT.Dataset, dataset) 
            else:
                print("new dataset {} found, adding to catalog".format(dataset_id))
                dataset_graph = self.graph.cbd(dataset_id)
                subject_replace(PURL + "new", dataset_id, DCAT.Dataset, dataset_graph)
                dataset_graph.remove((BNode(dataset_id), None, None))
                self.client.link_resource(dataset_graph, targeturl, DCAT.Dataset)
                dataset_purl = self.client.upload_resource(dataset_graph, targeturl, resource_type=DCAT.Dataset, resource_name="Dataset")
                self.client.publish_metadata(dataset_purl)


    def parse_cat_dat(self, catalog_file_path: str, datasets_file_path: str, publish: bool=False):
        """parse and upload metadata of a catalog (one) and 
        its associated datasets. Expects csv with ";" seperator
        and a header. This automatically publishes the catalog, and datasets
        when publish = True

        :param catalog_file_path: path to csv file describing a catalog
        :type catalog_file_path: str
        :param datasets_file_path: path to csv file describing datasets in the catalog
        :type datasets_file_path: str
        :param publish: if the metadata should be published or not
        :type publish: bool
        """
        cat_table = pd.read_csv(catalog_file_path, sep=";",header=0)
        for index, catalog in cat_table.iterrows():
            self.sempyro_catalog(catalog, self.graph, URL + "/new")
            subject_replace(PURL + "new", BNode("Catalog"), DCAT.Catalog, self.graph)
            catalog_purl = self.client.upload_resource(self.graph, URL, resource_type=DCAT.Catalog)
            if publish:
                    self.client.publish_metadata(catalog_purl)
            dat_table = pd.read_csv(datasets_file_path, sep=";",header=0) # get data
            for index, dataset in dat_table.iterrows():
                self.sempyro_dataset(dataset, self.graph, PURL) # TODO ADD AGENT IDENTIFIER AS BLANK NODE ID
            dataset_list = get_dataset_nodes(self.graph)
            for node_id in dataset_list:
                dataset_graph = self.graph.cbd(node_id[0])
                subject_replace(PURL + "new", node_id[0], DCAT.Dataset, dataset_graph)
                dataset_graph.remove((BNode(node_id[0]), None, None))
                self.client.link_resource(dataset_graph, catalog_purl, DCAT.Dataset)
                dataset_purl = self.client.upload_resource(dataset_graph, catalog_purl, resource_type=DCAT.Dataset, resource_name="Dataset")
                if publish:
                    self.client.publish_metadata(dataset_purl)
    
    def update_cat_dat(self, catalog_file_path: str, datasets_file_path:str, cat_PURL: URIRef, FDP_PURL: URIRef):
        """_summary_

        :param catalog_file_path: _description_
        :type catalog_file_path: str
        :param datasets_file_path: _description_
        :type datasets_file_path: str
        :param PURL: URI that points to the catalog to be updated
        :type PURL: URIRef
        """
        cat_table = pd.read_csv(catalog_file_path,sep=";",header=0)
        for index, catalog in cat_table.iterrows():
            new_catalog = self.replace_catalog(catalog, cat_PURL)
            dat_table = pd.read_csv(datasets_file_path, sep=";",header=0)
            for index, dataset in dat_table.iterrows():
                self.sempyro_dataset(dataset, self.graph, FDP_PURL)
            self.replace_datasets(cat_PURL)

            


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
    if config["mode"]["replace"]:
        parser.update_cat_dat(catalog_file_path=config["file_paths"]["catalog_input_file"],
                              datasets_file_path=config["file_paths"]["datasets_input_file"],
                              cat_PURL=config["FDP"]["catalog_purl"],
                              FDP_PURL=PURL)
    else:
        parser.parse_cat_dat(catalog_file_path=config["file_paths"]["catalog_input_file"],datasets_file_path=config["file_paths"]["datasets_input_file"], publish=config["mode"]["publish"])
