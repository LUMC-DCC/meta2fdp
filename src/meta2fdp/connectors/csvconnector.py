"""Connector for reading metadata from CSV files."""

import logging
from os import PathLike
from pathlib import Path
from typing import Union
from meta2fdp.config.connector.csvconnector import CSVConnectorConfig
import pandas as pd

from meta2fdp.connectors.base import BaseConnector


class CSVConnector(BaseConnector):
    """Connector for reading metadata from CSV files. This connector is designed to read metadata from CSV files and convert it into a format that can be used by the rest of the meta2fdp pipeline. The connector uses the configuration parameters specified in the CSVConnectorConfig class to determine the file paths for the catalog and dataset metadata, and it implements methods to read these files and return the metadata as pandas DataFrames. The connector also includes error handling to ensure that the specified file paths exist and that the required parameters are provided in the configuration."""

    def __init__(self, config: CSVConnectorConfig):
        self.config = config

    def _resolve_path(self, p: Union[str, PathLike, Path]) -> Path:
        """
        Resolve and validate a filesystem path.

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

    def get_catalog(self) -> pd.DataFrame:
        """Read the catalog metadata from the specified CSV file and return it as a pandas DataFrame."""
        catalog_path = self.config.catalog_input_file
        resolved_path = self._resolve_path(catalog_path)
        return pd.read_csv(
            resolved_path, sep=self.config.separator, header=self.config.header
        )

    def get_dataset(self) -> pd.DataFrame:
        """Read the dataset metadata from the specified CSV file and return it as a pandas DataFrame."""
        dataset_path = self.config.dataset_input_file
        resolved_path = self._resolve_path(dataset_path)
        return pd.read_csv(
            resolved_path, sep=self.config.separator, header=self.config.header
        )
