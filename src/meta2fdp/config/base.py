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

    # class Config: This is feature becomes depricated in pydantic v2, so we can remove it for now. It was used to make the configuration objects immutable (frozen) to prevent accidental changes after creation. If we want to keep this behavior, we can implement it using a custom __setattr__ method or by using a different approach to enforce immutability.
    #     frozen = True  # Make the configuration objects immutable to prevent accidental changes after creation
    # Karolis: I have removed the frozen = True for now, as it will become depricated and it interferes with the ability to set the mappings attribute in the ExtractorConfig class after loading the mappings from the YAML file. We can consider implementing immutability in a different way if needed, but for now it is more important to allow the configuration objects to be mutable so that we can set the mappings after loading them from the YAML file. This is necessary because the mappings may not be known at the time of creating the ExtractorConfig object, and they need to be loaded from the YAML file and set as an attribute on the configuration object after it has been created. This is mainly to reduce the complexity of setting a configuration object as just having the mappings as an attribute forces the users of the package to load the mappings from the YAML file and set them on the configuration object before they can use it, which adds an extra step to the process of using the configuration object. By allowing the configuration object to be mutable, we can set the mappings after loading them from the YAML file without needing to create a new configuration object or use a different approach to enforce immutability. This makes it easier for users to work with the configuration objects and reduces the complexity of using them in practice.
