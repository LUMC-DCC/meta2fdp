"""base class for extractor configuration objects in meta2fdp."""

from typing import Any, Dict
from meta2fdp.config.base import BaseConfig


class Parser(BaseConfig):
    """
    Configuration class for metadata parsers in meta2fdp. This class defines the parameters required to configure a metadata parser, including the parser name and any additional parameters needed for the specific parser implementation. The validate_config method can be used to ensure that the provided configuration parameters are valid for the specified parser, while the public_dict method can be used to return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages). The parse_yaml method can be overridden by subclasses if they require custom parsing logic for their configuration parameters.
    """

    name: str
    type: str = "parser"
    parser_name: str

    def validate_config(self) -> bool:
        """Validate the configuration parameters. Must be implemented by subclasses."""
        pass

    def public_dict(self) -> Dict[str, Any]:
        """Return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages). Must be implemented by subclasses."""
        pass

    def parse_yaml(self, yaml_data: Dict[str, Any]):
        """Parse the configuration parameters from a YAML dictionary. This method can be overridden by subclasses if they require custom parsing logic."""
        for key, value in yaml_data.items():
            setattr(self, key, value)
