"""Integration test of the CSV version of a pipeline made with the package
TODO: this tests a pipeline that is not yet fully implemented, so it should be adapted as the pipeline is developed. The idea is to have a test that shows the minimum script for uploading content from a csv source, and then adapt it as the pipeline is developed / implemented as part of the package. The test should be adapted to the actual implementation of the pipeline, and should not be a copy of the pipeline script itself. The test should be a simplified version of the pipeline script, that shows the minimum steps for uploading content from a csv source. The test should be adapted to the actual implementation of the pipeline, and should not be a copy of the pipeline script itself. The test should be a simplified version of the pipeline script, that shows the minimum steps for uploading content from a csv source.
"""

import logging
import pytest
from pathlib import Path
from rdflib import URIRef

from meta2fdp.config.connector.csvconnector import CSVConnectorConfig
from meta2fdp.config.extractor.extractor import ExtractorConfig
from meta2fdp.config.transformer.transformer import TransformerConfig
from meta2fdp.config.fdp.fdpconfig import FDPConfig

# from meta2fdp.config.fdp.fdp import FDPConfig #TODO not yet implemented, but will be needed for the client configuration
from meta2fdp.connectors.csvconnector import CSVConnector
from meta2fdp.extractors.dfextractor import DFExtractor
from meta2fdp.transformers.HRIcore.v2.hriv2schema import Hriv2Schema as Schema
from meta2fdp.fdp.fdpclient import FDPClient as Client


from meta2fdp.secrets.environmentprovider import EnvSecretsProvider
from meta2fdp.secrets.keyringprovider import KeyringSecretsProvider


from tests.fixtures.build_fdp import fdp_server


@pytest.fixture
def environment_secrets_provider():
    provider = EnvSecretsProvider(env_path=Path("tests\.env.test"))
    return provider


@pytest.fixture
def keyring_secrets_provider():
    provider = KeyringSecretsProvider()
    return provider


@pytest.fixture
def connector_config():
    return CSVConnectorConfig(
        name="test_connector",
        catalog_input_file="tests/data/input/Health-RI_LUMC_catalogue.csv",
        dataset_input_file="tests/data/input/Health-RI_LUMC_datasets.csv",
    )


@pytest.fixture
def extractor_config():
    x_config = ExtractorConfig(
        name="test_extractor",
        extractor_type="df",
        mapping_file=Path("tests/config/mappings_test.yaml"),
        language_tags=["en", "nl"],
    )
    x_config.get_mappings()  # TODO the extractor config should handle the get_mappings step internally when the config is initialized, so that the user doesn't have to worry about this extra step and doesn't forget to do it, which could lead to errors later on in the pipeline when the mappings are needed but not set in the config. So ideally, the ExtractorConfig class should have a method that is called when the config is initialized that automatically calls get_mappings and sets the mappings attribute of the config, so that the user doesn't have to worry about this extra step and doesn't forget to do it, which could lead to errors later on in the pipeline when the mappings are needed but not set in the config. #TODO the function also now returns the mappings, but this is not really needed, since the mappings are now set as an attribute of the config, so the function could just return None
    return x_config


@pytest.fixture
def transformer_config():
    transformer_config = TransformerConfig(
        name="test_transformer",
        schema_name="HRIcore",
        schema_version="v2",
    )
    transformer_config.get_default_values(
        Path("tests/config/default_values_tests.yaml")
    )  ##TODO the transformer config shouldn't need to call get_default_values, as this is an extra step that is not needed for the transformer configuration itself, but is an a step that is easily forgotten by users of the package, so it would be better if the transformer config itself would handle this step internally when the config is initialized, so that the user doesn't have to worry about this extra step and doesn't forget to do it, which could lead to errors later on in the pipeline when the default values are needed but not set in the config. So ideally, the TransformerConfig class should hav
    return transformer_config


@pytest.fixture(scope="session")
def config():
    # used in build_fdp fixture to set env vars for the client configuration, and potentially in the future to set other configuration values for the test
    return {
        "FDP": {
            "URL": "FDP_URL",
            "username": "FDP_USERNAME",
        },
        "mode": {"publish": True},
        "stayalive": True,
    }


# set up a local FDP server before the client to allow for different version and URL settings
fdp_server


@pytest.fixture
def client(fdp_server, environment_secrets_provider, keyring_secrets_provider):
    # create client after fdp_server fixture has started the server
    logging.debug(
        f"test FDP URL from environment secrets provider: {environment_secrets_provider}"
    )
    logging.debug(
        f"test FDP URL from keyring secrets provider: {keyring_secrets_provider}"
    )
    logging.debug(f"fdp_url: {environment_secrets_provider.get_info('FDP_BASE_URL')}")
    fdp_config = FDPConfig(
        name="test_fdp_client",
        fdp_version=environment_secrets_provider.get_info("FDP_BASE_VERSION"),
        URL=environment_secrets_provider.get_info("FDP_BASE_URL"),
        environmentprovider=environment_secrets_provider,
        keyringprovider=keyring_secrets_provider,
    )
    return Client(fdp_config)


def test_pipeline(
    config, connector_config, extractor_config, transformer_config, client
):
    connector = CSVConnector(connector_config)
    # get data from files:
    catalog_df = connector.get_catalog()
    dataset_df = connector.get_dataset()

    parser = DFExtractor(extractor_config)
    converter = Schema(transformer_config)
    logging.debug(f"client class config: {client.config}")
    logging.debug(
        f"client has following secretsproviders:\n {client.environmentprovider} \n {client.keyringprovider}"
    )

    if client.connection_status() != 200:
        raise ConnectionError("Unable to connect to FDP")

    catalogs_list = parser.parse_catalog(catalog_df)
    datasets_list = parser.parse_dataset(dataset_df)

    for catalog_metadata in catalogs_list:
        logging.debug(f"Catalog metadata:\n {catalog_metadata}\n")
        publisher = converter.instantiate_agent(catalog_metadata, "publisher_")
        logging.debug(
            publisher.to_graph(URIRef("https://example.org/publisher")).serialize()
        )
        creator = converter.instantiate_agent(catalog_metadata, "creator_")
        logging.debug(
            creator.to_graph(URIRef("https://example.org/creator")).serialize()
        )
        contact_point = converter.instantiate_vcard(catalog_metadata, "contactPoint_")
        logging.debug(
            contact_point.to_graph(URIRef("https://example.org/contact_point"))
        )
        logging.debug(type(publisher))
        sempyro_catalog = converter.instantiate_catalog(
            catalog_metadata,
            creators=[creator],
            publisher=publisher,
            contact_point=contact_point,
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
        logging.debug(f"Serialized catalog RDF graph: \n{post_catalog}")
        catalog_fdp_location = client.post_resource(
            post_catalog, resource_type="catalog"
        )
        if config["mode"]["publish"]:
            client.publish_resource(catalog_fdp_location)
        # HACK this uses the datasets column to identifiy which datasets are in the catalog
        # it's bad form as the "dataset" property is used within the schema to actually do that
        # but that one needs a URL that does not exist yet, as the dataset is not published on the FDP yet.
        # So we map the ID's that link the two csv files with each other to the arbritrary "datasets" column
        # in the extractor module (called parser in this iteration of integration test).
        linked_datasets = catalog_metadata["datasets"].split(",")
        logging.debug(f"linked_datasets: {linked_datasets}")
        for dataset_metadata in datasets_list:
            logging.debug(f"dataset_metadata: {dataset_metadata}")
            logging.debug(
                f"dataset in linked_datasets: {dataset_metadata['identifier']}"
            )
            if str(dataset_metadata["identifier"]) in linked_datasets:
                creators = converter.instantiate_agent(dataset_metadata, "creator_")
                contact_point = converter.instantiate_vcard(
                    dataset_metadata, "contactPoint_"
                )
                publisher = converter.instantiate_agent(dataset_metadata, "publisher_")
                sempyro_dataset = converter.instantiate_dataset(
                    dataset_metadata,
                    creators=[creators],
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
                logging.debug(f"Serialized dataset RDF graph: \n{post_dataset}")
                dataset_fdp_location = client.post_resource(
                    post_dataset, resource_type="dataset"
                )
                if config["mode"]["publish"]:
                    client.publish_resource(dataset_fdp_location)
