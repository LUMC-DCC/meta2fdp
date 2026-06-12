"""Base class for connector configurations."""

from typing import Dict, Any
from pathlib import Path
from pydantic import Field
from meta2fdp.config.connector.base import ConnectorConfig


class CSVConnectorConfig(ConnectorConfig):
    """Configuration class for csv connectors in meta2fdp. This class defines the parameters required to configure a connector, including the connector name and any additional parameters needed for the specific connector implementation. The validate_config method can be used to ensure that the provided configuration parameters are valid for the specified connector, while the public_dict method can be used to return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages)."""

    name: str
    config_type: str = "connector"
    connector_name: str = "CSVConnector"
    connector_type: str = "csv"
    separator: str = Field(
        ";", description="The separator used in the CSV files. Default is ';'."
    )
    header: int = Field(
        0,
        description="The row number to use as the column names. Default is 0 (the first row).",
    )
    catalog_input_file: Path = Field(
        ..., description="Path to the CSV file containing catalog metadata."
    )
    dataset_input_file: Path = Field(
        ..., description="Path to the CSV file containing dataset metadata."
    )
    # TODO make the file paths optional and parse from yaml if not provided, to allow for more flexible configuration

    def validate_config(self) -> bool:
        """Validate the configuration parameters for the CSV connector. This method checks that the required parameters are present and that the specified file paths exist. If any validation checks fail, an appropriate exception is raised with a descriptive error message.

        :returns: True if the configuration is valid, otherwise raises an exception.
        :rtype: bool
        :raises ValueError: If any required parameter is missing or if any file path does not exist.
        """
        if not self.catalog_input_file:
            raise ValueError("Catalog input file path is required for CSV connector.")
        if not self.dataset_input_file:
            raise ValueError("Dataset input file path is required for CSV connector.")
        if not self.catalog_input_file.exists():
            raise FileNotFoundError(
                f"Catalog input file not found at path: {self.catalog_input_file}"
            )
        if not self.dataset_input_file.exists():
            raise FileNotFoundError(
                f"Dataset input file not found at path: {self.dataset_input_file}"
            )
        return True

    def public_dict(self) -> Dict[str, Any]:
        """Return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages). Must be implemented by subclasses."""
        return {
            "name": self.name,
            "config_type": self.config_type,
            "connector_name": self.connector_name,
            "connector_type": self.connector_type,
        }
