"""Integration test of the CSV version of a pipeline made with the package
TODO: this tests a pipeline that is not yet fully implemented, so it should be adapted as the pipeline is developed. The idea is to have a test that shows the minimum script for uploading content from a csv source, and then adapt it as the pipeline is developed / implemented as part of the package. The test should be adapted to the actual implementation of the pipeline, and should not be a copy of the pipeline script itself. The test should be a simplified version of the pipeline script, that shows the minimum steps for uploading content from a csv source. The test should be adapted to the actual implementation of the pipeline, and should not be a copy of the pipeline script itself. The test should be a simplified version of the pipeline script, that shows the minimum steps for uploading content from a csv source.
"""

import sys
import os
import unittest
import subprocess
import yaml
from pathlib import Path
from rdflib import URIRef
from meta2fdp.parsers.csvparser import CSVParser as Parser
from meta2fdp.schemas.hriv2schema import Hriv2Schema as Schema
from meta2fdp.fdp.FDPClient import FDPClient as Client


BASE_DIR = Path(__file__).resolve().parent

# facilitate running tests from command line using `python -m unittest`
sys.path.append(str(BASE_DIR.parent))
from tests.fixtures import build_fdp


class CSVPipelinetests(unittest.TestCase):
    def __init__(
        self,
        methodName: str = "runTest",
    ) -> None:
        self.config = self.parse_yaml(Path("tests/data/config/configuration_csv.yaml"))
        self.default_values = self.parse_yaml(
            Path("tests/data/config/model_config_test.yaml")
        )
        super().__init__(methodName)
        self.client = None

    def setUp(self):
        build_fdp.setup()
        # create client after environment and keyring have been prepared
        self.client = Client(self.config)

    def tearDown(self):
        subprocess.run(
            ["docker", "compose", "down"],
            cwd=Path("tests/test_integration/compose/fdp/ephemeral/v1"),
        )
        # cleanup env var set by build_fdp.setup() to avoid cross-test pollution
        try:
            env_key = self.config["FDP"]["URL"]
            if env_key in os.environ:
                del os.environ[env_key]
        except Exception:
            pass

    def parse_yaml(self, conf_path):
        try:
            with open(conf_path, "r") as config_file:
                config = yaml.safe_load(
                    config_file
                )  # used to obtain right value types from the yaml like booleans
                return config
        except FileNotFoundError:
            print(f"YAML file not found: {conf_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML file: {e}")
            sys.exit(1)

    def test_pipeline(self):
        """An abstract example pipeline that shows the minimum script for uploading content from a csv source"""

        parser = Parser(config=self.config)  # abstract parser
        converter = Schema(self.default_values)  # abstract converter

        self.client.get_api_token()
        if self.client.connection_status() == 200:
            pass
        else:
            raise ConnectionError

        catalogs_df = parser.get_metadata(
            Path(self.config["file_paths"]["catalog_input_file"])
        )
        datasets_df = parser.get_metadata(
            Path(self.config["file_paths"]["dataset_input_file"])
        ).set_index("title_en")

        ####################### upload catalogs #######################
        for index, catalog_metadata in catalogs_df.iterrows():
            # creators = []
            # for i in range(0,10): # imagine you have 10 creators (this is not the same as attributions of the resource)
            #     creators.append(converter.instantiate_agent(catalog_metadata, "creator" + str(i)))
            contact_point = converter.instantiate_HRIVcard(
                catalog_metadata, "contactPoint"
            )
            publisher = converter.instantiate_agent(catalog_metadata, "publisher")
            sempyro_catalog = converter.instantiate_HRICatalog(
                metadata=catalog_metadata,
                contact_point=contact_point,
                publisher=publisher,
            )
            rdf_graph = converter.convert_class_to_rdf(
                sempyro_catalog, URIRef(self.client.URL + "/new")
            )
            rdf_graph.add(
                (
                    URIRef(self.client.URL + "/new"),
                    URIRef("http://purl.org/dc/terms/isPartOf"),
                    URIRef(self.client.URL),
                )
            )
            post_catalog = rdf_graph.serialize()
            catalog_fdp_location = self.client.post_resource(
                post_catalog, resource_type="catalog"
            )
            if self.config["mode"]["publish"]:
                self.client.publish_resource(catalog_fdp_location)

            ####################### upload datasets of catalog #######################
            for dataset_index in catalog_metadata.loc["datasets"].split(","):
                if dataset_index in datasets_df.keys():
                    dataset_metadata = datasets_df.loc[dataset_index, :]
                    # an agnostic way to get all creators
                    creators = [
                        converter.instantiate_agent(dataset_metadata, "creator")
                    ]
                    contact_point = converter.instantiate_HRIVcard(
                        dataset_metadata, "contactPoint"
                    )
                    publisher = converter.instantiate_agent(
                        dataset_metadata, "publisher"
                    )
                    sempyro_dataset = converter.instantiate_HRIDataset(
                        dataset_metadata,
                        creators=creators,
                        contact_point=contact_point,
                        publisher=publisher,
                    )

                    dataset_post_graph = converter.convert_class_to_rdf(
                        sempyro_dataset, URIRef(self.client.URL + "/new")
                    )
                    dataset_post_graph.add(
                        (
                            URIRef(self.client.URL + "/new"),
                            URIRef("http://purl.org/dc/terms/isPartOf"),
                            URIRef(catalog_fdp_location),
                        )
                    )
                    post_dataset = dataset_post_graph.serialize()
                    dataset_fdp_location = self.client.post_resource(
                        post_dataset, resource_type="dataset"
                    )
                    if self.config["mode"]["publish"]:
                        self.client.publish_resource(dataset_fdp_location)


if __name__ == "__main__":
    unittest.main()
