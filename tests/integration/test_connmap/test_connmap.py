from meta2fdp.config.connector.csvconnector import CSVConnectorConfig
from meta2fdp.config.extractor.extractor import ExtractorConfig
from meta2fdp.connectors.csvconnector import CSVConnector
from meta2fdp.extractors.dfextractor import DFExtractor
import pytest
import pandas as pd
import yaml


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


@pytest.fixture
def extractor_config():
    config = ExtractorConfig(
        name="test_extractor",
        extractor_name="DFExtractor",
        mapping_file="tests/config/mappings_connmap_test.yaml",
    )
    config.get_mappings()
    return config


def test_connmap(connector_config, extractor_config):
    """Check if column headers are mapped correctly"""
    connector = CSVConnector(config=connector_config)
    extractor = DFExtractor(config=extractor_config)

    catalog_df = connector.get_catalog()
    mapped_catalog_df = extractor.parse_catalog(catalog_df)
    print(mapped_catalog_df)

    with open("tests/config/mappings_connmap_test.yaml") as file:
        catalog = yaml.safe_load(file)
        expected_column_headers = pd.json_normalize(
            catalog["mappings"]["catalog"], sep="_"
        ).to_dict(orient="records")
        print(expected_column_headers)
    assert set(mapped_catalog_df[0].keys()) == set(expected_column_headers[0].keys())
