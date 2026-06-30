"""Base class for SQL connector configurations."""

from typing import Dict, Any
from meta2fdp.config.base import BaseConfig
from meta2fdp.secrets.environmentprovider import EnvSecretsProvider
from meta2fdp.secrets.keyringprovider import KeyringSecretsProvider


class SQLConnectorConfig(BaseConfig):
    """Configuration class for SQL connectors in meta2fdp. This class defines the parameters required to configure a SQL connector, including the connector name and any additional parameters needed for the specific connector implementation. The validate_config method can be used to ensure that the provided configuration parameters are valid for the specified connector, while the public_dict method can be used to return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages). The parse_yaml method can be overridden by subclasses if they require custom parsing logic for their configuration parameters."""

    name: str
    config_type: str = "connector"
    connector_name: str
    connector_type: str
    environmentprovider = EnvSecretsProvider  # not public
    keyringprovider = KeyringSecretsProvider  # not public
    tds_version: str = "7.4"  # default tds version for mssql
    catalog_id: str = "catalog"  # default catalog table name
    dataset_id: str = "dataset"  # default dataset table name

    def public_dict(self) -> Dict[str, Any]:
        """Return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages). Must be implemented by subclasses."""
        return {
            "name": self.name,
            "config_type": self.config_type,
            "connector_name": self.connector_name,
            "connector_type": self.connector_type,
        }

    def parse_yaml(self, yaml_data: Dict[str, Any]):
        self.parse_yaml(yaml_data)
