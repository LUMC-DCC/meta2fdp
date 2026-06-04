"""Base connector class for meta2fdp."""

from abc import ABC, abstractmethod
from pathlib import Path
from os import PathLike
from typing import Union
import logging


class BaseConnector(ABC):
    """Abstract base class for connectors that read metadata from various sources.

    This class defines the interface that all connector implementations must follow,
    including methods for reading catalog and dataset metadata.
    """

    @abstractmethod
    def read_catalog(self):
        """Read the catalog metadata from the specified source.

        :return: Catalog metadata in connector-specific format
        """
        pass

    @abstractmethod
    def read_dataset(self):
        """Read the dataset metadata from the specified source.

        :return: Dataset metadata in connector-specific format
        """
        pass

    def _resolve_path(self, p: Union[str, PathLike, Path]) -> Path:
        """Resolve and validate a filesystem path.

        :param p: Path-like object or string to resolve.
        :type p: str or os.PathLike or pathlib.Path
        :returns: Resolved pathlib.Path
        :rtype: pathlib.Path
        :raises FileNotFoundError: If the resolved path does not exist.
        """
        p = Path(p)
        logging.debug(f"Resolving path: {p}")
        p = p.expanduser().resolve(strict=False)
        logging.debug(f"Resolved path: {p}")
        if not p.exists():
            raise FileNotFoundError(f"File not found: {p}")
        return p
