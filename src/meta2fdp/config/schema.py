"""Schema configuration class for meta2fdp."""

from meta2fdp.config.base import BaseConfig


class SchemaConfig(BaseConfig):
    """Configuration class for schema-related settings in meta2fdp."""

    name: str
    type: str = "schema"
    schema_name: str
    schema_version: str

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
            "type": self.type,
            "schema": self.schema_name,
            "version": self.schema_version,
        }
