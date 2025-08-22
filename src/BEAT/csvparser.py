"""

"""
from rdflib import URIRef, DCTERMS, BNode, Literal, XSD, DCAT, Graph, Dataset, RDF, FOAF
import pandas as pd
from converter import Converter


class CSVself(Converter):

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
        datasets_fdp_ids = update_resource(catalog_purl, self.graph)


    def upload_catalog(self, ) -> URIRef:
        return catalog_purl

    def upload_dataset(self, ):
        NotImplemented()
    
    def upload_full_catalog(sef, ) -> URIRef:
        return catalog_purl

    cat_table = pd.read_csv(catalog_file_path,sep=";",header=0)
    for catalog in cat_table.iterrows():
        self.pydantic_catalog(catalog, self.graph, URL + "/new")
        subject_replace(PURL + "new", BNode("Catalog"), DCAT.Catalog, self.graph)
        # catalog_purl = "https://fdp.example.org/catalog/d66222dc-c95c-4b83-874d-7764f5475173"
        if config["mode"]["replace"] == True:
            catalog_purl = config["FDP"]["catalog_purl"]
            datasets_fdp_ids = update_catalog(catalog_purl, self.graph)
        else:
            catalog_purl = upload_resource(self.graph, URL, resource_type=DCAT.Catalog)
        dat_table = pd.read_csv(datasets_file_path, sep=";",header=0) # get data
        for dataset in dat_table.iterrows():
            self.pydantic_dataset(dataset, self.graph, PURL) # TODO ADD AGENT IDENTIFIER AS BLANK NODE ID
        dataset_list = get_dataset_nodes(self.graph)
        for node_id in dataset_list:
            dataset_graph = self.graph.cbd(node_id[0])
            subject_replace(PURL + "new", node_id[0], DCAT.Dataset, dataset_graph)
            dataset_graph.remove((BNode(node_id[0]), None, None))
            link_resource(dataset_graph, catalog_purl, DCAT.Dataset)
            upload_resource(dataset_graph, catalog_purl, resource_type=DCAT.Dataset, resource_name="Dataset")