"""Integration test of the CSV version of a pipeline made with the package"""
import pathlib
import sys


BASE_DIR = pathlib.Path(__file__).resolve().parent

# facilitate running tests from command line using `python -m unittest`
sys.path.append(str(BASE_DIR.parent))

import unittest

import subprocess
from samplenavigator2fdp.parsers.csvparser import CSVParser as Parser
from samplenavigator2fdp.converters.hriv2model import Hriv2Model as Model
from samplenavigator2fdp.graphutils.graphutils import graphutils
from samplenavigator2fdp.fdp.FDPClient import FDPClient as Client
from tests import build_fdp

from rdflib import URIRef
import yaml
import pathlib
import sys

class CSVPipelinetests(unittest.TestCase):

    def __init__(self, methodName: str = "runTest", ) -> None:
        self.config = self.parse_yaml(pathlib.Path("tests/test_files/test_configs/configuration_csv.yaml"))
        self.default_values = self.parse_yaml(pathlib.Path("config/model_config.yaml"))
        super().__init__(methodName)
        self.client = Client(self.config)


    def setUp(self):
        build_fdp.setup()


    def tearDown(self):
        subprocess.run(["docker", "compose", "down"], cwd=pathlib.Path("tests/test_integration/compose/fdp/ephemeral/v1"))


    def parse_yaml(self, conf_path):
        try:
            with open(conf_path, "r") as config_file:
                config = yaml.safe_load(config_file)  # used to obtain right value types from the yaml like booleans
                return config
        except FileNotFoundError:
            print(f"YAML file not found: {conf_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            sys.exit(1) 


    def test_pipeline(self):
        """An abstract example pipeline that shows the minimum script for uploading content from a csv source
"""     
        
        parser = Parser(config=self.config) #abstract parser
        converter = Model(self.default_values) #abstract converter

        self.client.get_api_token()
        if self.client.connection_status() == 200:
            pass
        else:
            raise ConnectionError
        

        catalogs_df = parser.get_metadata(self.config["file_paths"]["catalog_input_file"])
        datasets_df = parser.get_metadata(self.config["file_paths"]["dataset_input_file"]).set_index("title_en")

        ####################### upload catalogs #######################
        for index, catalog_metadata in catalogs_df.iterrows():
            # creators = []
            # for i in range(0,10): # imagine you have 10 creators (this is not the same as attributions of the resource)
            #     creators.append(converter.instantiate_agent(catalog_metadata, "creator" + str(i)))
            contact_point = converter.instantiate_HRIVcard(catalog_metadata, "contactPoint")
            publisher = converter.instantiate_agent(catalog_metadata, "publisher")
            sempyro_catalog = converter.instantiate_HRICatalog(metadata=catalog_metadata, contact_point=contact_point, publisher=publisher)
            rdf_graph = converter.convert_class_to_rdf(sempyro_catalog, URIRef(self.client.URL + "/new"))
            rdf_graph.add((URIRef(self.client.URL + "/new"), URIRef("http://purl.org/dc/terms/isPartOf"), URIRef(self.client.URL)))
            post_catalog = rdf_graph.serialize()
            catalog_fdp_location = self.client.post_resource(post_catalog, resource_type="catalog")
            if self.config["mode"]["publish"]:
                self.client.publish_resource(catalog_fdp_location)

        ####################### upload datasets of catalog #######################
            for dataset_index in catalog_metadata.loc["datasets"].split(","):
                if dataset_index in datasets_df.keys():
                    dataset_metadata = datasets_df.loc[dataset_index,:]
                    # an agnostic way to get all creators
                    creators = [converter.instantiate_agent(dataset_metadata, "creator")] 
                    contact_point = converter.instantiate_HRIVcard(dataset_metadata, "contactPoint")
                    publisher = converter.instantiate_agent(dataset_metadata, "publisher")
                    sempyro_dataset = converter.instantiate_HRIDataset(dataset_metadata, creators=creators, contact_point=contact_point, publisher=publisher)

                    dataset_post_graph = converter.convert_class_to_rdf(sempyro_dataset, URIRef(self.client.URL + "/new"))
                    dataset_post_graph.add((URIRef(self.client.URL + "/new"), URIRef("http://purl.org/dc/terms/isPartOf"), URIRef(catalog_fdp_location)))
                    post_dataset = dataset_post_graph.serialize()
                    dataset_fdp_location = self.client.post_resource(post_dataset, resource_type="dataset")
                    if self.config["mode"]["publish"]:
                        self.client.publish_resource(dataset_fdp_location)

if __name__ == '__main__':
    unittest.main()

