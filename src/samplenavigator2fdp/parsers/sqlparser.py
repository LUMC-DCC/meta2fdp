"""Adapter class for MSSQL database to FDP with health-ri v2.0.0.

update function not yet implemented yet.

"""
from samplenavigator2fdp.parsers.abstractparser import Parser
from rdflib import URIRef, BNode, DCAT, Namespace
import yaml
import pandas as pd
import keyring
from pymssql import connect


class SQLParser(Parser):

    def __init__(self, config, client: FDPClient, class_map=None, debug=False):
        super().__init__(class_map, debug)
        self.config = config
        self.client = client
        self.VCARD = Namespace("http://www.w3.org/2006/vcard/ns#")

    def dataset_sql_query(self, cursor, dataset_id):
        """SQL dataset query generator that should result in
         the metadata related to the dataset with dataset_id

        :param cursor: connection to a mssql database
        :type cursor: Cursor object
        :param dataset_id: dataset SQL index
        :type dataset_id: str
        :return: output of mssql database
        :rtype: Cursor object
    
        """

        def dataset_sql_query_constructor(table_name, dataset_id) -> str:
            dataset_query = "select * from " + str(table_name) + " where identifier = '" + str(dataset_id) + "';"
            return dataset_query
        
        table_name = self.config["SQL"]["dataset_id"]
        dataset_query = dataset_sql_query_constructor(table_name, dataset_id)
        cursor.execute(dataset_query)
        return cursor

    def catalog_sql_query(self, cursor):
        """SQL catalog query generator that should result in
         the metadata related to the catalog or database

        :param cursor: connection to a mssql database
        :type cursor: Cursor object
        :return: output of mssql database
        :rtype: Cursor object
    
        """
        def catalog_sql_query_constructor(table_name) -> str:
            catalog_query = "select * from "  + str(table_name) + ";"
            return catalog_query
        
        catalog_query = catalog_sql_query_constructor(self.config["SQL"]["catalog_id"])
        cursor.execute(catalog_query)
        return cursor

    def connect_to_sql(self):
        """Connect to a mssql database and build an interface for it.
        Database should exists in network

        :return: mssql interface 
        :rtype: Cursor object.

        """
        conn = connect(server=self.config["SQL"]["server_name"],user=self.config["SQL"]["username"],password=keyring.get_password(service_name=self.config["SQL"]["keyring_service"], username=self.config["SQL"]["username"]), database=self.config["SQL"]["database_name"],tds_version="7.4")
        cursor = conn.cursor(as_dict=True)
        return cursor
    
    def parse(self):
        """Parses the content of the samplenavigator mssql database view
        and uses it to generate a catalog and it's associated datasets.
        These are immediately uploaded to the FDP.
        """
        # get catalog information:
        cursor = self.connect_to_sql()
        catalog_table = self.catalog_sql_query(cursor)

        for catalog in catalog_table:
            # transform catalog metadata:
            self.sempyro_catalog(pd.Series(catalog), self.graph, url=self.client.URL + "/new")
            # replace subject id with url needed to upload new data to FDP:
            subject_replace(self.client.PURL + "new", BNode("Catalog"), DCAT.Catalog, self.graph)  # util
            #upload catalog
            catalog_purl = client.upload_resource(self.graph, self.client.URL, resource_type=DCAT.Catalog)
            if self.config["mode"]["publish"]:
                self.client.publish_metadata(catalog_purl)
            # get associated dataset sql index ids
            for dataset_id in catalog["datasets"].split(","):
                # get metadata for dataset
                dataset_metadata = self.dataset_sql_query(cursor, dataset_id).__next__()
                # add dataset to graph:
                self.sempyro_dataset(pd.Series(dataset_metadata), self.graph, self.client.PURL)
            # get a list of all datasets in the graph:
            dataset_list = get_dataset_nodes(self.graph)  # util
            for node_id in dataset_list:
                # extract dataset specific information
                dataset_graph = self.graph.cbd(node_id[0])
                subject_replace(self.client.PURL + "new", node_id[0], DCAT.Dataset, dataset_graph)  # util
                # remove dataset metadata from graph
                dataset_graph.remove((BNode(node_id[0]), None, None))
                # link dataset to catalog
                self.client.link_resource(dataset_graph, catalog_purl, DCAT.Dataset)
                # upload dataset metadata
                dataset_purl = self.client.upload_resource(dataset_graph, catalog_purl, resource_type=DCAT.Dataset, resource_name="Dataset")
                if self.config["mode"]["publish"]:
                    self.client.publish_metadata(dataset_purl)
    
    def update_catalog(self):
        #TODO
        raise NotImplementedError
        


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
    parser = SQLParser(config, client)
    parser.parse()

    
