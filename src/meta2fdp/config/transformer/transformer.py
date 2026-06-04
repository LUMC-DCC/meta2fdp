"""Schema configuration class for meta2fdp."""

from meta2fdp.config.base import BaseConfig
from yaml import safe_load


class TransformerConfig(BaseConfig):
    """Configuration class for schema-related settings in meta2fdp."""

    name: str
    config_type: str = "transformer"
    schema_name: str
    schema_version: str
    default_values: dict = {}
    language_tags: list = ["en", "nl"]

    def validate_config(self, model_registry) -> bool:
        """Validate the schema configuration parameters."""
        # For this example, we don't have specific parameters to validate, but this method can be expanded as needed.
        if not model_registry.exists(self.schema_name, self.schema_version):
            raise ValueError(
                f"Schema with name '{self.schema_name}' and version '{self.schema_version}' is not registered in the model registry."
            )
        return True

    def public_dict(self) -> dict:
        """Return a dictionary of the schema configuration parameters that are safe to expose publicly."""
        return {
            "name": self.name,
            "config_type": self.config_type,
            "schema": self.schema_name,
            "version": self.schema_version,
        }

    def get_default_values(self, path):
        with open(path, "r") as f:
            self.default_values = safe_load(f)
