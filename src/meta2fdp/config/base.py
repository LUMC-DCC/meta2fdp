"""Abstract base class for configuration objects in meta2fdp."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from pydantic import BaseModel


class BaseConfig(BaseModel, ABC):
    """Abstract base class for configuration objects in meta2fdp.
    All configuration classes must define:
    - name: a string identifier for the configuration
    - type: a string indicating the type of configuration (e.g., "parser", "converter", "client")
    - validate_config: a method to validate the configuration parameters
    """

    name: str
    type: str

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the configuration parameters. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def public_dict(self) -> Dict[str, Any]:
        """Return a dictionary of the configuration parameters that are safe to expose publicly (e.g., for logging or error messages). Must be implemented by subclasses."""
        pass

    class Config:
        frozen = True  # Make the configuration objects immutable to prevent accidental changes after creation
