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
    config_type: str = "parser"
    parser_name: str

    def __init__(
        self, name: str, bases: tuple[type, ...], dict: Dict[str, Any], /, **kwds: Any
    ) -> None:
        self.mapping_file: Path = Field(
            ...,
            description="Path to the mapping file used by the parser.",
            default=Path("config/extractor/mappings_default.yaml"),
        )
        self.mappings: Dict[str, str | Dict[str, Any]] = Field(
            ...,
            description="Dictionary of mappings used by the extractor.",
            default_factory=lambda: self.get_mappings(self.mapping_file),
        )
        super().__init__(name, bases, dict, **kwds)

    def validate_config(self) -> bool:
        """Validate the configuration parameters. Must be implemented by subclasses."""
        pass

    def public_dict(self) -> Dict[str, Any]:
        """Return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages). Must be implemented by subclasses."""
        pass

    def parse_yaml(self, path: Path):
        self.parse_yaml(path)

    def get_mappings(self, path: Path) -> Dict[str, str | Dict[str, Any]]:
        """Return a dictionary of mappings from the parser configuration. Must be implemented by subclasses."""
        yaml_data = yaml.safe_load(path.read_text())
        return yaml_data.get("mappings", {})
