from meta2fdp.config.connector.csvconnector import CSVConnectorConfig
from meta2fdp.config.extractor.extractor import ExtractorConfig
from meta2fdp.connectors.csvconnector import CSVConnector
from meta2fdp.extractors.dfextractor import DFExtractor
import pytest


@pytest.fixture
def extractor_config():
    config = ExtractorConfig(
        name="test_extractor",
        extractor_name="DFExtractor",
        mapping_file="tests/config/mappings.yaml",
    )
    return config


@pytest.fixture
def connector_config():
    config = CSVConnectorConfig(
        name="test_connector",
        connector_name="CSVConnector",
        separator=";",
        header=0,
        catalog_input_file="tests/data/csv_connmap_test/catalog.csv",
        dataset_input_file="tests/data/csv_connmap_test/dataset.csv",
    )
    return config


def test_connmap(connector_config, extractor_config):
    connector = CSVConnector(config=connector_config)
    extractor = DFExtractor(config=extractor_config)

    catalog_df = connector.read_catalog()
    mapped_catalog_df = extractor.parse_catalog(catalog_df)
    assert set(mapped_catalog_df.columns) == set(
        extractor_config.mappings["catalog"].keys()
    ).union(extractor_config.mappings["publisher"].keys()).union(
        extractor_config.mappings["contact_point"].keys()
    ).union(extractor_config.mappings["creator"].keys())
