from meta2fdp.config.base import BaseConfig
from typing import Dict, Any, ClassVar, Type
from meta2fdp.secrets.base import SecretsProvider


class FDPConfig(BaseConfig):
    """Abstract base class for configuration a fdp client in meta2fdp.
    All configuration classes must define:
    - name: a string identifier for the configuration
    - type: a string indicating the type of configuration (e.g., "parser", "converter", "client")
    - validate_config: a method to validate the configuration parameters
    - public_dict: a method to return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages)
    """

    name: str
    config_type: str = "fdp"
    fdp_version: str
    fdp_url: str  # Website URL of the FDP instance, e.g., 'https://fdp.example.com', used as base target for API calls.
    target_catalog_url: str | None = (
        None  # Optional URL of the target catalog to which data will be published, e.g., "https://fdp.example.com/catalog/UUID"
    )
    environmentprovider: ClassVar[Type[SecretsProvider]] = SecretsProvider
    keyringprovider: ClassVar[Type[SecretsProvider]] = SecretsProvider

    def validate_config(self):
        """Validate the configuration parameters."""
        pass

    def public_dict(self) -> Dict[str, Any]:
        """Return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages). Must be implemented by subclasses."""
        return {
            "name": self.name,
            "config_type": self.config_type,
            "fdp_url": self.fdp_url,
            "fdp_version": self.fdp_version,
            "target_catalog_url": self.target_catalog_url,
        }
