"""
Adapter class from csv to FDP
"""
from rdflib import URIRef, BNode, DCAT, DCTERMS, Graph
import pandas as pd
from samplenavigator2fdp.parsers.converter import Converter
from samplenavigator2fdp.fdp.FDPClient import FDPClient
import keyring


from pathlib import Path

from graphutils import subject_replace, get_dataset_nodes

import yaml
from os import getenv


class CSVParser(Converter):

    def __init__(self, config: dict, client: FDPClient, class_map=None, debug=False):
        super().__init__(class_map, debug)
        self.client = client
        self.config = config

    
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
            self.sempyro_catalog(catalog, self.graph, self.client.URL + "/new")
            subject_replace(self.client.PURL + "new", BNode("Catalog"), DCAT.Catalog, self.graph)
            catalog_purl = self.client.upload_resource(self.graph, self.client.URL, resource_type=DCAT.Catalog)
            if publish:
                    self.client.publish_metadata(catalog_purl)
            dat_table = pd.read_csv(datasets_file_path, sep=";",header=0) # get data
            for index, dataset in dat_table.iterrows():
                self.sempyro_dataset(dataset, self.graph, self.client.PURL) # TODO ADD AGENT IDENTIFIER AS BLANK NODE ID
            dataset_list = get_dataset_nodes(self.graph)
            for node_id in dataset_list:
                dataset_graph = self.graph.cbd(node_id[0])
                subject_replace(self.client.PURL + "new", node_id[0], DCAT.Dataset, dataset_graph)
                dataset_graph.remove((BNode(node_id[0]), None, None))
                self.client.link_resource(dataset_graph, catalog_purl, DCAT.Dataset)
                dataset_purl = self.client.upload_resource(dataset_graph, catalog_purl, resource_type=DCAT.Dataset, resource_name="Dataset")
                if publish:
                    self.client.publish_metadata(dataset_purl)


    def replace_catalog(self, catalog_metadata: pd.Series, targeturl: URIRef) -> list:
        """Use the given metadata to update a FDP catalog with the given PURL.

        :param catalog_metadata: metadata of a catalog
        :type catalog_metadata: pd.Series
        :param targeturl: PURL of a catalog (example: 
        https://app.fairdatapoint.org/catalog/60234295-e5c9-45e7-b96f-6bed7bba3134)
        :type targeturl: URIRef
        :return: The left-join graph that has been uploaded to the FDP.
        it contains the content on the FDP that has not changed and the replaced
        content from catalog_metadata.
        :rtype: list
        """
        catalog_id = self.sempyro_catalog(catalog_metadata, self.graph, self.client.URL + "/new") # fix catalog generator
        subject_replace(self.client.PURL + "new", BNode("Catalog"), DCAT.Catalog, self.graph)
        new_catalog = self.client.update_catalog(targeturl, self.graph.cbd(catalog_id)) # update catalog and retrieve a list of child nodes.
        return new_catalog


    def replace_datasets(self, targeturl):
        """Function to update the datasets that exist under a FDP catalog
        We first obtain the identifier (hopefully unique) of the datasets on the FDP.
        Then we check if the identifiers of the datasets in the local graph match
        with the ones on the FDP. If they match, the content on the FDP Is updated
        with the content in the local graph;. Otherwise a the local dataset graph
        is uploaded as a new dataset under the given target catalog.

        :param targeturl: PURL of a FDP catalog
        :type targeturl: str
        """
        # TODO This is inefficient: we get the data to get a list of identifiers to match
        # Figure out a way to reduce API calls to match parsed dataset with FDP datasets
        FDP_cat_response_body = self.client.get_metadata(targeturl)
        FDP_cat_graph = Graph()  # parse response into graph structure
        FDP_cat_graph.parse(data=FDP_cat_response_body)
        FDP_dataset_ids = self.client.get_dataset_id_purls(FDP_cat_graph)  # get FDP datsasets ids (that are published)
        id_url_map = []
        for key in FDP_dataset_ids:
            id_url_map.append(self.client.PURL + key)
        #HACK current implementation assumes that all datasets in file should
        # be updated
        for dataset_id in self.dataset_ids:  # get internal node id for datasets in local graph
            if dataset_id in id_url_map:
                dataset = self.graph.cbd(dataset_id) # extract graph related to node/dataset id
                local_dataset_identifier = dataset.value(subject=dataset_id,
                                                predicate=DCTERMS.identifier)
                matching_purl = FDP_dataset_ids[local_dataset_identifier]
                self.client.update_resource(matching_purl, DCAT.Dataset, dataset) 
            else:  # upload new dataset:
                print("new dataset {} found, adding to catalog".format(dataset_id))
                dataset_graph = self.graph.cbd(dataset_id)
                subject_replace(self.client.PURL + "new", dataset_id, DCAT.Dataset, dataset_graph)
                dataset_graph.remove((BNode(dataset_id), None, None))
                self.client.link_resource(dataset_graph, targeturl, DCAT.Dataset)
                dataset_purl = self.client.upload_resource(dataset_graph, targeturl, resource_type=DCAT.Dataset, resource_name="Dataset")
                if self.config["mode"]["publish"]:
                    self.client.publish_metadata(dataset_purl)



    def update_cat_dat(self, catalog_file_path: str, datasets_file_path:str, cat_PURL: URIRef, FDP_PURL: URIRef):
        """Update a catalog and it's datasets with the content of the given csv files.
        csv has a header and the seperator is assumed to be ;

        :param catalog_file_path: csv file containing catalog metadata with a header and ; delimiter
        :type catalog_file_path: str
        :param datasets_file_path: csv file containing metadata of datasets with a header and ; delimiter
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
        config = yaml.safe_load(config_file)  # used to obtain right value types from the yaml like booleans

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
