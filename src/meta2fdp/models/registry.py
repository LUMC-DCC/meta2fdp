"""Module for managing the registry of metadata schema modules.
This module defines the ModelRegistry class, which allows for registering and retrieving metadata schema modules by name and version.
The registry is used to keep track of the available metadata schemas, and to allow for easy retrieval of these schemas.
The ModelRegistry class provides methods for registering a new metadata schema, checking if a schema exists, and retrieving a registered schema by name and version.
The registry is implemented as a dictionary, where the keys are the schema names and the values are dictionaries that map schema versions to the corresponding metadata schema modules.
"""

from types import ModuleType
from typing import Dict, Type

from pydantic import BaseModel


class ModelRegistry:
    """Registry for metadata schema modules.
    This class allows for registering and retrieving metadata schema modules by name and version.
    """

    def __init__(self):
        self._model_registry: Dict[str, Dict[str, ModuleType]] = {}

    def register(
        self, schema_name: str, schema_version: str, module: Type[BaseModel]
    ) -> None:
        """Register a metadata schema with a unique name and version."""
        self._model_registry.setdefault(schema_name, {})
        if schema_version in self._model_registry[schema_name]:
            raise ValueError(
                f"Schema with name '{schema_name}' and version '{schema_version}' is already registered."
            )
        self._model_registry[schema_name][schema_version] = module

    def exists(self, schema_name: str, schema_version: str = None) -> bool:
        """Check if a metadata schema with the given name and optionally version exists in the registry."""
        return schema_name in self._model_registry and (
            schema_version is None
            or schema_version in self._model_registry[schema_name]
        )

    def get(self, schema_name: str, schema_version: str) -> ModuleType:
        """Retrieve a registered metadata schema module by name and optionally by version."""
        if schema_name not in self._model_registry:
            raise KeyError(f"Schema with name '{schema_name}' is not registered.")
        if schema_version is not None:
            if (
                hasattr(self._model_registry[schema_name], "version")
                and self._model_registry[schema_name].version != schema_version
            ):
                raise KeyError(
                    f"Schema with name '{schema_name}' and version '{schema_version}' is not registered."
                )
        return self._model_registry[schema_name][schema_version]

    def list_schemas(self):
        return list(self._model_registry.keys())

    def list_versions(self, schema_name: str):
        if schema_name not in self._model_registry:
            raise KeyError(f"Schema with name '{schema_name}' is not registered.")
        return list(self._model_registry[schema_name].keys())
