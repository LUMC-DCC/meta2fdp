"""base class for extractor configuration objects in meta2fdp."""

from typing import Any, Dict
from pathlib import Path
from pydantic import Field
from meta2fdp.config.base import BaseConfig
import yaml


class ExtractorConfig(BaseConfig):
    """
    Configuration class for metadata extractors in meta2fdp. This class defines the parameters required to configure a metadata extractor, including the extractor name and any additional parameters needed for the specific extractor implementation. The validate_config method can be used to ensure that the provided configuration parameters are valid for the specified extractor, while the public_dict method can be used to return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages). The parse_yaml method can be overridden by subclasses if they require custom parsing logic for their configuration parameters.
    """

    name: str
    config_type: str = "extractor"
    extractor_name: str
    mapping_file: Path | None = Field(
        description="Path to the mapping file used by the parser.",
        default=Path("config/extractor/mappings_default.yaml"),
    )

    mappings: Dict[str, str | Dict[str, Any]] | None = Field(
        description="Dictionary of mappings used by the extractor.", default=None
    )

    def validate_config(self) -> bool:
        """Validate the configuration parameters. Must be implemented by subclasses."""
        pass

    def public_dict(self) -> Dict[str, Any]:
        """Return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages). Must be implemented by subclasses."""
        pass

    def parse_yaml(self, path: Path):
        self.parse_yaml(path)

    def get_mappings(self) -> Dict[str, str | Dict[str, Any]]:
        """Set mappings based on mapping_file attribute. Return a dictionary of mappings from the configuration."""
        if (
            not self.mappings
        ):  # Only load the mappings from the file if they have not already been loaded
            raise FileNotFoundError(
                "Mapping file path is not set in the configuration."
            )
        with open(self.mapping_file, "r") as file:
            yaml_data = yaml.safe_load(file)
        setattr(self, "mappings", yaml_data.get("mappings", {}))
        return self.mappings
