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
    extractor_name: str = "DFExtractor"
    extractor_type: str = "df"
    mapping_file: Path | None = Field(
        description="Path to the mapping file used by the parser.",
        default=None,
    )

    mappings: Dict[str, str | Dict[str, Any]] | None = Field(
        description="Dictionary of mappings used by the extractor.", default=None
    )

    def validate_config(self) -> bool:
        """Validate the configuration parameters. Must be implemented by subclasses."""
        raise NotImplementedError("not implemented yet")

    def public_dict(self) -> Dict[str, Any]:
        """Return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages). Must be implemented by subclasses."""
        raise NotImplementedError("not implemented yet")

    def parse_yaml(self, path: Path):
        self.parse_yaml(path)

    def get_mappings(self) -> Dict[str, str | Dict[str, Any]]:
        # todo allow for path to be passed as an argument, and for the mappings to be set directly in the configuration as well, with the file being used as a fallback if the mappings are not set directly in the configuration
        """Set mappings based on mapping_file attribute. Return a dictionary of mappings from the configuration."""
        if (
            not self.mapping_file or not self.mapping_file.exists()
        ):  # Only load the mappings from the file if they have not already been loaded
            raise FileNotFoundError(
                "Mapping file path is not set or does not exist in the configuration."
            )
        with open(self.mapping_file, "r") as file:
            yaml_data = yaml.safe_load(file)
        setattr(self, "mappings", yaml_data.get("mappings", {}))
        return self.mappings
