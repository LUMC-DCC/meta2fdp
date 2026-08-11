"""Example pipeline that shows how to use the CSV connector, extractor,
transformer, and FDP client in a simple metadata publishing workflow.

This script is intentionally written as a general usage example rather than a
pytest test. It can be adapted to your own CSV files and FDP instance.
"""

import logging
from pathlib import Path
from rdflib import URIRef

from meta2fdp.config.connector.csvconnector import CSVConnectorConfig
from meta2fdp.config.extractor.extractor import ExtractorConfig
from meta2fdp.config.transformer.transformer import TransformerConfig
from meta2fdp.config.fdp.fdpconfig import FDPConfig

from meta2fdp.connectors.csvconnector import CSVConnector
from meta2fdp.extractors.dfextractor import DFExtractor
from meta2fdp.transformers.HRIcore.v2.hriv2schema import Hriv2Schema as Schema
from meta2fdp.fdp.fdpclient import FDPClient
from meta2fdp.secrets.environmentprovider import EnvSecretsProvider
from meta2fdp.secrets.keyringprovider import KeyringSecretsProvider


EXAMPLE_DIR = Path(__file__).resolve().parent


def build_environment_provider() -> EnvSecretsProvider:
    """Load FDP credentials from environment variables or a .env file."""
    return EnvSecretsProvider(env_path=Path("tests/.envtests.test"))


def build_keyring_provider() -> KeyringSecretsProvider:
    """Return a keyring-based secrets provider."""
    return KeyringSecretsProvider()


def build_connector_config() -> CSVConnectorConfig:
    return CSVConnectorConfig(
        name="example_connector",
        connector_name="CSVConnector",
        connector_type="csv",
        separator=";",
        header=0,
        catalog_input_file=EXAMPLE_DIR / "catalog.csv",
        dataset_input_file=EXAMPLE_DIR / "datasets.csv",
    )


def build_extractor_config() -> ExtractorConfig:
    config = ExtractorConfig(
        name="example_extractor",
        extractor_name="DFExtractor",
        extractor_type="df",
        mapping_file=EXAMPLE_DIR / "mappings.yaml",
    )
    config.get_mappings()
    return config


def build_transformer_config() -> TransformerConfig:
    config = TransformerConfig(
        name="example_transformer",
        schema_name="HRIcore",
        schema_version="v2",
    )
    config.get_default_values(EXAMPLE_DIR / "default_values.yaml")
    return config


def build_fdp_config(environment_provider, keyring_provider) -> FDPConfig:
    return FDPConfig(
        name="example_fdp_client",
        fdp_version=environment_provider.get_info("FDP_BASE_VERSION"),
        URL=environment_provider.get_info("FDP_BASE_URL"),
        environmentprovider=environment_provider,
        keyringprovider=keyring_provider,
    )


def run_pipeline() -> None:
    logging.basicConfig(level=logging.INFO)

    environment_provider = build_environment_provider()
    keyring_provider = build_keyring_provider()

    connector_config = build_connector_config()
    extractor_config = build_extractor_config()
    transformer_config = build_transformer_config()
    fdp_config = build_fdp_config(environment_provider, keyring_provider)

    connector = CSVConnector(connector_config)
    extractor = DFExtractor(extractor_config)
    transformer = Schema(transformer_config)
    client = FDPClient(fdp_config)

    if client.connection_status() != 200:
        raise ConnectionError("Unable to connect to the FDP instance.")

    catalog_df = connector.get_catalog()
    dataset_df = connector.get_dataset()

    catalog_records = extractor.parse_catalog(catalog_df)
    dataset_records = extractor.parse_dataset(dataset_df)

    for catalog_record in catalog_records:
        publisher = transformer.instantiate_agent(catalog_record, "publisher_")
        creator = transformer.instantiate_agent(catalog_record, "creator_")
        contact_point = transformer.instantiate_vcard(catalog_record, "contactPoint_")

        catalog_resource = transformer.instantiate_catalog(
            catalog_record,
            creators=[creator],
            publisher=publisher,
            contact_point=contact_point,
        )

        catalog_graph = transformer.convert_class_to_rdf(
            catalog_resource,
            URIRef(f"{client.URL}/new"),
        )
        catalog_graph.add(
            (
                URIRef(f"{client.URL}/new"),
                URIRef("http://purl.org/dc/terms/isPartOf"),
                URIRef(client.URL),
            )
        )

        catalog_location = client.post_resource(
            catalog_graph.serialize(),
            resource_type="catalog",
        )
        logging.info("Posted catalog to %s", catalog_location)

        linked_dataset_ids = [
            item.strip()
            for item in str(catalog_record.get("dataset_ids", "")).split(",")
            if item.strip()
        ]

        for dataset_record in dataset_records:
            if str(dataset_record.get("identifier")) not in linked_dataset_ids:
                continue

            publisher = transformer.instantiate_agent(dataset_record, "publisher_")
            creator = transformer.instantiate_agent(dataset_record, "creator_")
            contact_point = transformer.instantiate_vcard(
                dataset_record,
                "contactPoint_",
            )

            dataset_resource = transformer.instantiate_dataset(
                dataset_record,
                creators=[creator],
                publisher=publisher,
                contact_point=contact_point,
            )

            dataset_graph = transformer.convert_class_to_rdf(
                dataset_resource,
                URIRef(f"{client.URL}/new"),
            )
            dataset_graph.add(
                (
                    URIRef(f"{client.URL}/new"),
                    URIRef("http://purl.org/dc/terms/isPartOf"),
                    URIRef(catalog_location),
                )
            )

            dataset_location = client.post_resource(
                dataset_graph.serialize(),
                resource_type="dataset",
            )
            logging.info("Posted dataset to %s", dataset_location)


if __name__ == "__main__":
    run_pipeline()
