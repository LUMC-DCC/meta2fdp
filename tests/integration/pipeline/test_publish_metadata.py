from pathlib import Path

import pytest
from meta2fdp.pipeline.publish_catalogs_datasets_metadata import (
    PublishCatalogsDatasetsMetadataPipeline,
)
from meta2fdp.bootstrap import register_modules, register_transformer_configs
from meta2fdp.config.connector.csvconnector import CSVConnectorConfig
from meta2fdp.config.extractor.extractor import ExtractorConfig
from meta2fdp.config.fdp.fdpconfig import FDPConfig
from meta2fdp.fdp.fdpclient import FDPClient
from tests.fixtures.build_fdp import fdp_server
from rdflib import DCAT, Graph, RDF, URIRef
import logging

logging.basicConfig(level=logging.INFO)


@pytest.fixture
def transformer_configs():
    return register_transformer_configs()


fdp_server


def test_publish_metadata_pipeline(transformer_configs, fdp_server):

    registries = register_modules()
    transformer_configs = register_transformer_configs()

    connector_config = CSVConnectorConfig(
        name="csv_connector",
        connector_name="CSVConnector",
        connector_type="csv",
        separator=";",
        header=0,
        catalog_input_file=Path("tests/data/input/Health-RI_LUMC_catalogue.csv"),
        dataset_input_file=Path("tests/data/input/Health-RI_LUMC_datasets.csv"),
    )

    extractor_config = ExtractorConfig(
        name="df_extractor",
        config_type="extractor",
        extractor_name="DFExtractor",
        extractor_type="df",
        mapping_file=Path("tests/config/mappings_test.yaml"),
    )
    extractor_config.get_mappings()  # Load mappings from the specified mapping file

    schema_config = transformer_configs["HRIcore_v2_LUMC"]

    fdp_config = FDPConfig(
        name="FDPClient",
        fdp_version="v2",
        URL="http://localhost",
        environmentprovider=registries["secrets"]["env"](),
        keyringprovider=registries["secrets"]["keyring"](),
    )

    pipeline = PublishCatalogsDatasetsMetadataPipeline(
        connector_config=connector_config,
        extractor_config=extractor_config,
        schema_config=schema_config,
        FDP_config=fdp_config,
        registries=registries,
    )

    pipeline.run()

    client = FDPClient(fdp_config)
    fdpgraph = Graph().parse(data=client.get_resource("http://localhost"))
    catalog_urls = [URIRef(row[0]) for row in client.get_children(fdpgraph)]

    assert (
        len(catalog_urls) == 1
    )  # FAILS IF there are more than one catalog in the FDP server, which is the case if the FDP server is not restarted between tests. This is why we set stayalive to False in the config fixture, so that the FDP server is restarted between tests.

    catalog_url = catalog_urls[0]
    catalog_graph = Graph().parse(data=client.get_resource(str(catalog_url)))
    assert (catalog_url, RDF.type, DCAT.Catalog) in catalog_graph
    dataset_urls = [URIRef(row[0]) for row in client.get_children(catalog_graph)]
    assert (
        len(dataset_urls) == 3
    )  # FAILS IF there are more than three datasets in the FDP server, which is the case if the FDP server is not restarted between tests. This is why we set stayalive to False in the config fixture, so that the FDP server is restarted between tests.

    for dataset_url in dataset_urls:
        dataset_graph = Graph().parse(data=client.get_resource(str(dataset_url)))
        assert (dataset_url, RDF.type, DCAT.Dataset) in dataset_graph
