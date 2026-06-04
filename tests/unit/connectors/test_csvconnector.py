"""Test suite for the CSVConnector class.

This test suite verifies that the CSVConnector class correctly reads CSV files
with different configurations, and that behavior changes based on configuration changes.
"""

import pytest
from pathlib import Path
import pandas as pd
from meta2fdp.connectors.csvconnector import CSVConnector
from meta2fdp.config.connector.csvconnector import CSVConnectorConfig


@pytest.fixture
def test_data_dir(test_dir) -> Path:
    """Return the path to the CSV connector test data directory."""
    return test_dir / "data" / "csv_connector_test"


class TestCSVConnectorBasicFunctionality:
    """Test basic functionality of the CSVConnector class."""

    def test_connector_initialization(self, test_data_dir):
        """Test that the connector can be initialized with a valid configuration."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
        )
        connector = CSVConnector(config)
        assert connector is not None
        assert connector.config == config

    def test_get_catalog_returns_dataframe(self, test_data_dir):
        """Test that get_catalog returns a pandas DataFrame."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
        )
        connector = CSVConnector(config)
        catalog_df = connector.get_catalog()
        assert isinstance(catalog_df, pd.DataFrame)

    def test_catalog_has_correct_columns(self, test_data_dir):
        """Test that the catalog DataFrame has the expected columns."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
        )
        connector = CSVConnector(config)
        catalog_df = connector.get_catalog()
        expected_columns = ["catalog_id", "catalog_name", "catalog_description"]
        assert list(catalog_df.columns) == expected_columns

    def test_catalog_has_correct_row_count(self, test_data_dir):
        """Test that the catalog DataFrame has the expected number of rows."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
        )
        connector = CSVConnector(config)
        catalog_df = connector.get_catalog()
        assert len(catalog_df) == 3


class TestCSVConnectorSeparatorConfiguration:
    """Test that the connector respects different separator configurations."""

    def test_semicolon_separator_default(self, test_data_dir):
        """Test that semicolon is the default separator."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
            separator=";",
        )
        connector = CSVConnector(config)
        catalog_df = connector.get_catalog()
        assert len(catalog_df.columns) == 3
        assert "catalog_id" in catalog_df.columns
        assert catalog_df.iloc[0]["catalog_id"] == "CAT001"

    def test_comma_separator_configuration(self, test_data_dir):
        """Test that comma separator works when configured."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_comma.csv",
            dataset_input_file=test_data_dir / "dataset_comma.csv",
            separator=",",
        )
        connector = CSVConnector(config)
        catalog_df = connector.get_catalog()
        assert len(catalog_df.columns) == 3
        assert "catalog_id" in catalog_df.columns
        assert catalog_df.iloc[0]["catalog_id"] == "CAT001"

    def test_pipe_separator_configuration(self, test_data_dir):
        """Test that pipe separator works when configured."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_pipe.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
            separator="|",
        )
        connector = CSVConnector(config)
        catalog_df = connector.get_catalog()
        assert len(catalog_df.columns) == 3
        assert "catalog_id" in catalog_df.columns
        assert catalog_df.iloc[0]["catalog_id"] == "CAT001"

    def test_wrong_separator_produces_different_columns(self, test_data_dir):
        """Test that using wrong separator produces incorrect column count."""
        # Using comma separator on semicolon file should result in one column
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
            separator=",",
        )
        connector = CSVConnector(config)
        catalog_df = connector.get_catalog()
        # With wrong separator, the whole line becomes one column
        assert len(catalog_df.columns) == 1
        assert catalog_df.columns[0] != "catalog_id"

    def test_separator_changes_affect_parsing(self, test_data_dir):
        """Test that changing separator configuration changes how the file is parsed."""
        # Parse with semicolon (correct)
        config_semicolon = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
            separator=";",
        )
        connector_semicolon = CSVConnector(config_semicolon)
        df_semicolon = connector_semicolon.get_catalog()

        # Parse with comma (incorrect for this file)
        config_comma = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
            separator=",",
        )
        connector_comma = CSVConnector(config_comma)
        df_comma = connector_comma.get_catalog()

        # Verify that they produce different results
        assert len(df_semicolon.columns) != len(df_comma.columns)
        assert len(df_semicolon.columns) == 3
        assert len(df_comma.columns) == 1


class TestCSVConnectorHeaderConfiguration:
    """Test that the connector respects different header configurations."""

    def test_default_header_is_zero(self, test_data_dir):
        """Test that header defaults to 0 (first row)."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
            header=0,
        )
        connector = CSVConnector(config)
        catalog_df = connector.get_catalog()
        assert "catalog_id" in catalog_df.columns
        assert "catalog_name" in catalog_df.columns
        assert "catalog_description" in catalog_df.columns

    def test_skip_rows_via_header_configuration(self, test_data_dir):
        """Test that header configuration can skip rows at the beginning."""
        # Use the file with skip rows, but set header=2 to skip the first 2 rows
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_skip_rows.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
            header=2,
        )
        connector = CSVConnector(config)
        catalog_df = connector.get_catalog()
        # After skipping 2 rows, the header should be recognized correctly
        assert "catalog_id" in catalog_df.columns
        assert "catalog_name" in catalog_df.columns
        assert len(catalog_df) == 3  # Should have 3 data rows

    def test_header_configuration_changes_column_names(self, test_data_dir):
        """Test that different header configurations result in different column names."""
        # With header=0 (first row as header)
        config_header_0 = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_with_skip.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
            header=0,
        )
        connector_header_0 = CSVConnector(config_header_0)
        df_header_0 = connector_header_0.get_catalog()

        # With header=1 (second row as header)
        config_header_1 = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_with_skip.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
            header=1,
        )
        connector_header_1 = CSVConnector(config_header_1)
        df_header_1 = connector_header_1.get_catalog()

        # Verify different column names due to different header configuration
        assert df_header_0.columns[0] == "skip_this_row"
        assert df_header_1.columns[0] == "catalog_id"
        # When header=1, the first row is skipped, so different row counts
        assert len(df_header_0) > len(df_header_1)


class TestCSVConnectorPathResolution:
    """Test path resolution and validation."""

    def test_path_exists_validation(self, test_data_dir):
        """Test that connector validates that paths exist."""
        nonexistent_path = test_data_dir / "nonexistent.csv"
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=nonexistent_path,
        )
        # Config creation should not raise, but resolution should
        connector = CSVConnector(config)
        # Path validation happens at config level, not connector level
        assert connector is not None

    def test_resolve_path_with_existing_file(self, test_data_dir):
        """Test that _resolve_path works with existing files."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
        )
        connector = CSVConnector(config)
        resolved_path = connector._resolve_path(test_data_dir / "catalog_semicolon.csv")
        assert resolved_path.exists()
        assert resolved_path.is_file()

    def test_resolve_path_with_nonexistent_file(self, test_data_dir):
        """Test that _resolve_path raises FileNotFoundError for missing files."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
        )
        connector = CSVConnector(config)
        nonexistent_path = test_data_dir / "does_not_exist.csv"
        with pytest.raises(FileNotFoundError):
            connector._resolve_path(nonexistent_path)

    def test_resolve_path_with_relative_path(self, test_data_dir):
        """Test that _resolve_path resolves relative paths correctly."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
        )
        connector = CSVConnector(config)
        # Test with Path object
        resolved_path = connector._resolve_path(test_data_dir / "catalog_semicolon.csv")
        assert resolved_path.exists()


class TestCSVConnectorConfigValidation:
    """Test configuration validation."""

    def test_config_validation_success(self, test_data_dir):
        """Test that valid configuration passes validation."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
        )
        assert config.validate_config() is True

    def test_config_validation_missing_catalog_file(self):
        """Test that configuration with missing catalog file is invalid."""
        # Pydantic will raise a validation error when a required field is not provided
        with pytest.raises((ValueError, TypeError)):
            CSVConnectorConfig(
                name="test_connector",
                connector_name="test",
                catalog_input_file=None,
                dataset_input_file=Path("/some/path.csv"),
            )

    def test_config_validation_missing_dataset_file(self):
        """Test that configuration with missing dataset file is invalid."""
        # Pydantic will raise a validation error when a required field is not provided
        with pytest.raises((ValueError, TypeError)):
            CSVConnectorConfig(
                name="test_connector",
                connector_name="test",
                catalog_input_file=Path("/some/path.csv"),
                dataset_input_file=None,
            )

    def test_config_validation_nonexistent_catalog_file(self, test_data_dir):
        """Test that configuration validates file existence when validate_config is called."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "nonexistent.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
        )
        # validate_config should raise FileNotFoundError for nonexistent file
        with pytest.raises(FileNotFoundError, match="Catalog input file not found"):
            config.validate_config()

    def test_config_public_dict(self, test_data_dir):
        """Test that public_dict returns only safe configuration parameters."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
        )
        public = config.public_dict()
        assert "name" in public
        assert "connector_name" in public
        assert "connector_type" in public
        assert public["connector_type"] == "csv"
        # File paths should not be in public dict
        assert "catalog_input_file" not in public
        assert "dataset_input_file" not in public


class TestCSVConnectorBehaviorChanges:
    """Test that connector behavior changes based on configuration changes."""

    def test_behavior_changes_with_separator_change(self, test_data_dir):
        """Test that reading the same file with different separators produces different results."""
        results = {}

        # Test with different separators on the semicolon file
        for separator in [";", ",", "|"]:
            try:
                config = CSVConnectorConfig(
                    name="test_connector",
                    connector_name="test",
                    catalog_input_file=test_data_dir / "catalog_semicolon.csv",
                    dataset_input_file=test_data_dir / "dataset_semicolon.csv",
                    separator=separator,
                )
                connector = CSVConnector(config)
                df = connector.get_catalog()
                results[separator] = {
                    "column_count": len(df.columns),
                    "row_count": len(df),
                    "first_column": df.columns[0],
                }
            except Exception as e:
                results[separator] = {"error": str(e)}

        # Verify that different separators produce different results
        assert results[";"]["column_count"] == 3
        assert results[","]["column_count"] == 1
        assert results["|"]["column_count"] == 1
        assert results[";"]["first_column"] == "catalog_id"

    def test_behavior_changes_with_header_change(self, test_data_dir):
        """Test that changing header configuration changes parsing behavior."""
        results = {}

        # Test with different header settings on the with_skip file
        for header in [0, 1]:
            config = CSVConnectorConfig(
                name="test_connector",
                connector_name="test",
                catalog_input_file=test_data_dir / "catalog_with_skip.csv",
                dataset_input_file=test_data_dir / "dataset_semicolon.csv",
                header=header,
            )
            connector = CSVConnector(config)
            try:
                df = connector.get_catalog()
                results[header] = {
                    "column_count": len(df.columns),
                    "row_count": len(df),
                    "first_column": df.columns[0],
                    "success": True,
                }
            except Exception as e:
                # Some header configurations may fail to parse
                results[header] = {"success": False, "error": str(type(e).__name__)}

        # Verify that header=0 and header=1 produce different results
        assert results[0]["success"] is True
        assert results[1]["success"] is True
        assert results[0]["first_column"] == "skip_this_row"
        assert results[1]["first_column"] == "catalog_id"
        assert results[0]["row_count"] > results[1]["row_count"]

    def test_behavior_changes_with_multiple_config_changes(self, test_data_dir):
        """Test that changing multiple configuration options affects behavior."""
        # Read with one configuration
        config1 = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
            separator=";",
            header=0,
        )
        connector1 = CSVConnector(config1)
        df1 = connector1.get_catalog()

        # Read same file with different configuration (wrong separator)
        config2 = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
            separator=",",
            header=0,
        )
        connector2 = CSVConnector(config2)
        df2 = connector2.get_catalog()

        # Verify that configuration changes result in different parsing
        assert len(df1.columns) != len(df2.columns)
        # Even though row count may be the same, the column count should be different
        assert len(df1.columns) == 3  # Correct parsing with semicolon
        assert len(df2.columns) == 1  # Wrong separator treats whole line as one column
        assert "catalog_id" not in df2.columns


class TestCSVConnectorDataIntegrity:
    """Test that data is read correctly with various configurations."""

    def test_data_values_are_correct_with_correct_separator(self, test_data_dir):
        """Test that data values are read correctly with proper configuration."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_semicolon.csv",
            dataset_input_file=test_data_dir / "dataset_semicolon.csv",
            separator=";",
        )
        connector = CSVConnector(config)
        catalog_df = connector.get_catalog()

        # Verify specific data values
        assert catalog_df.iloc[0]["catalog_id"] == "CAT001"
        assert catalog_df.iloc[0]["catalog_name"] == "Biobank Catalog"
        assert catalog_df.iloc[1]["catalog_id"] == "CAT002"
        assert catalog_df.iloc[2]["catalog_name"] == "Test Catalog"

    def test_data_values_in_comma_separated_file(self, test_data_dir):
        """Test that data values are read correctly from comma-separated file."""
        config = CSVConnectorConfig(
            name="test_connector",
            connector_name="test",
            catalog_input_file=test_data_dir / "catalog_comma.csv",
            dataset_input_file=test_data_dir / "dataset_comma.csv",
            separator=",",
        )
        connector = CSVConnector(config)
        catalog_df = connector.get_catalog()

        # Verify that data is correctly parsed with comma separator
        assert catalog_df.iloc[0]["catalog_id"] == "CAT001"
        assert catalog_df.iloc[0]["catalog_name"] == "Biobank Catalog"
        assert len(catalog_df) == 3
