"""Integration test of the CSV version of a pipeline made with the package
TODO: this tests a pipeline that is not yet fully implemented, so it should be adapted as the pipeline is developed. The idea is to have a test that shows the minimum script for uploading content from a csv source, and then adapt it as the pipeline is developed / implemented as part of the package. The test should be adapted to the actual implementation of the pipeline, and should not be a copy of the pipeline script itself. The test should be a simplified version of the pipeline script, that shows the minimum steps for uploading content from a csv source. The test should be adapted to the actual implementation of the pipeline, and should not be a copy of the pipeline script itself. The test should be a simplified version of the pipeline script, that shows the minimum steps for uploading content from a csv source.
"""

import pytest
from pathlib import Path
from rdflib import URIRef
from meta2fdp.parsers.csvparser import CSVParser as Parser
from meta2fdp.models.HRIcore.v2.hriv2schema import Hriv2Schema as Schema
from meta2fdp.fdp.FDPClient import FDPClient as Client


from tests.fixtures.build_fdp import fdp_server


@pytest.fixture
def client(config, fdp_server):
    # create client after fdp_server fixture has started the server
    return Client(config)


def test_pipeline(client, config, model_config):
    parser = Parser(config=config)
    converter = Schema(model_config)

    client.get_api_token()
    if client.connection_status() != 200:
        raise ConnectionError("Unable to connect to FDP")

    catalogs_df = parser.get_metadata(Path(config["file_paths"]["catalog_input_file"]))
    datasets_df = (
        parser.get_metadata(Path(config["file_paths"]["dataset_input_file"]))
    ).set_index("title_en")

    for index, catalog_metadata in catalogs_df.iterrows():
        contact_point = converter.instantiate_HRIVcard(catalog_metadata, "contactPoint")
        publisher = converter.instantiate_agent(catalog_metadata, "publisher")
        sempyro_catalog = converter.instantiate_HRICatalog(
            metadata=catalog_metadata, contact_point=contact_point, publisher=publisher
        )
        rdf_graph = converter.convert_class_to_rdf(
            sempyro_catalog, URIRef(client.URL + "/new")
        )
        rdf_graph.add(
            (
                URIRef(client.URL + "/new"),
                URIRef("http://purl.org/dc/terms/isPartOf"),
                URIRef(client.URL),
            )
        )
        post_catalog = rdf_graph.serialize()
        catalog_fdp_location = client.post_resource(
            post_catalog, resource_type="catalog"
        )
        if config["mode"]["publish"]:
            client.publish_resource(catalog_fdp_location)

        for dataset_index in catalog_metadata.loc["datasets"].split(","):
            if dataset_index in datasets_df.keys():
                dataset_metadata = datasets_df.loc[dataset_index, :]
                creators = [converter.instantiate_agent(dataset_metadata, "creator")]
                contact_point = converter.instantiate_HRIVcard(
                    dataset_metadata, "contactPoint"
                )
                publisher = converter.instantiate_agent(dataset_metadata, "publisher")
                sempyro_dataset = converter.instantiate_HRIDataset(
                    dataset_metadata,
                    creators=creators,
                    contact_point=contact_point,
                    publisher=publisher,
                )

                dataset_post_graph = converter.convert_class_to_rdf(
                    sempyro_dataset, URIRef(client.URL + "/new")
                )
                dataset_post_graph.add(
                    (
                        URIRef(client.URL + "/new"),
                        URIRef("http://purl.org/dc/terms/isPartOf"),
                        URIRef(catalog_fdp_location),
                    )
                )
                post_dataset = dataset_post_graph.serialize()
                dataset_fdp_location = client.post_resource(
                    post_dataset, resource_type="dataset"
                )
                if config["mode"]["publish"]:
                    client.publish_resource(dataset_fdp_location)
