"""Abstract base class for configuration objects in meta2fdp."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel
import yaml


class BaseConfig(BaseModel, ABC):
    """Abstract base class for configuration objects in meta2fdp.
    All configuration classes must define:
    - name: a string identifier for the configuration
    - type: a string indicating the type of configuration (e.g., "parser", "converter", "client")
    - validate_config: a method to validate the configuration parameters
    - public_dict: a method to return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages)
    """

    name: str
    config_type: str

    @abstractmethod
    def validate_config(self) -> bool:
        try:
            if self.model_validate() is BaseModel:
                return True  # pydantic model validation to ensure all fields are valid according to their types and constraints
        except Exception as e:
            raise ValueError(
                f"Invalid configuration parameters for connector '{self.name}': {str(e)}"
            )

    @abstractmethod
    def public_dict(self) -> Dict[str, Any]:
        """Return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages). Must be implemented by subclasses."""
        pass

    def parse_yaml(self, path: Path) -> None:
        """Parse the configuration parameters from a YAML dictionary. This method can be overridden by subclasses if they require custom parsing logic."""
        with open(path, "r") as f:
            yaml_data = yaml.safe_load(f)
            for key, value in yaml_data.items():
                setattr(self, key, value)

    class Config:
        frozen = True  # Make the configuration objects immutable to prevent accidental changes after creation
