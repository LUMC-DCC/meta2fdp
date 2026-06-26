"""Unit tests for the configuration classes in meta2fdp."""

import pytest

from meta2fdp.bootstrap import register_models
from meta2fdp.config.connector.csvconnector import CSVConnectorConfig
from meta2fdp.config.extractor.extractor import ExtractorConfig
from meta2fdp.config.fdp.fdpconfig import FDPConfig
from meta2fdp.config.transformer.transformer import TransformerConfig


@pytest.fixture
def registry():
    return register_models()


def test_transformer_config_validates_and_exposes_public_fields(registry):
    config = TransformerConfig(
        name="HRIcore_v2",
        config_type="transformer",
        schema_name="HRIcore",
        schema_version="v2",
    )

    assert config.validate_config(registry) is True

    public_dict = config.public_dict()
    assert public_dict == {
        "name": "HRIcore_v2",
        "config_type": "transformer",
        "schema": "HRIcore",
        "version": "v2",
    }


def test_transformer_config_rejects_unknown_schemas(registry):
    config = TransformerConfig(
        name="unknown_schema",
        config_type="transformer",
        schema_name="UnknownSchema",
        schema_version="v9",
    )

    with pytest.raises(ValueError, match="Schema with name 'UnknownSchema'"):
        config.validate_config(registry)


def test_csv_connector_config_validates_existing_files(test_dir):
    data_dir = test_dir / "data" / "csv_connector_test"
    config = CSVConnectorConfig(
        name="test_connector",
        connector_name="CSVConnector",
        catalog_input_file=data_dir / "catalog_semicolon.csv",
        dataset_input_file=data_dir / "dataset_semicolon.csv",
    )

    assert config.validate_config() is True
    assert config.public_dict()["connector_type"] == "csv"


def test_csv_connector_config_raises_when_files_are_missing(tmp_path):
    catalog_input_file = tmp_path / "catalog.csv"
    dataset_input_file = tmp_path / "dataset.csv"
    catalog_input_file.write_text("id;name\n1;catalog\n", encoding="utf-8")

    config = CSVConnectorConfig(
        name="broken_connector",
        connector_name="CSVConnector",
        catalog_input_file=catalog_input_file,
        dataset_input_file=dataset_input_file,
    )

    with pytest.raises(FileNotFoundError, match="Dataset input file not found"):
        config.validate_config()


def test_extractor_config_loads_mappings_from_file(tmp_path):
    mapping_file = tmp_path / "mappings.yaml"
    mapping_file.write_text(
        "mappings:\n  catalog:\n    title: name\n",
        encoding="utf-8",
    )

    config = ExtractorConfig(name="test_extractor", mapping_file=mapping_file)

    assert config.get_mappings() == {"catalog": {"title": "name"}}
    assert config.mappings == {"catalog": {"title": "name"}}


def test_fdp_config_public_dict_contains_expected_fields():
    config = FDPConfig(
        name="fdp_client",
        fdp_version="1.0",
        URL="https://fdp.example.org",
        target_catalog_url="https://fdp.example.org/catalog/1",
    )

    assert config.public_dict() == {
        "name": "fdp_client",
        "config_type": "fdp",
        "fdp_url": "https://fdp.example.org",
        "fdp_version": "1.0",
        "target_catalog_url": "https://fdp.example.org/catalog/1",
    }
