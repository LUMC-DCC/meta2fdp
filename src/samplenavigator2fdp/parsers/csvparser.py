"""
CSV parser adapter for FDP.

This module implements :class:`CSVParser`, an adapter that reads CSV files
and returns :class:`pandas.DataFrame` objects for downstream processing.
"""
from samplenavigator2fdp.parsers.abstractparser import AbstractParser
import pandas as pd
from pathlib import Path

class CSVParser(AbstractParser):
    """
    Adapter that reads CSV files and returns pandas.DataFrame objects.

    :param config: Configuration dictionary. Expected to contain a "file_paths"
                   mapping with keys such as "catalog_input_file",
                   "dataset_input_file" and "distribution_input_file".
    :type config: dict
    """

    def __init__(self, config: dict):
        self.config = config


    def get_metadata(self, path: Path) -> pd.DataFrame:
        """
        Read a CSV file and return its contents as a pandas DataFrame.

        The CSV is read using ';' as separator and the first row as header.

        :param path: Path to the CSV file (Path or string).
        :type path: pathlib.Path or str
        :returns: DataFrame containing the CSV data.
        :rtype: pandas.DataFrame
        :raises FileNotFoundError: If the file does not exist.
        """
        p = self._resolve_path(path)
        return pd.DataFrame(pd.read_csv(str(p), sep=";", header=0))


    def parse_catalog(self) -> pd.DataFrame:
        """
        Parse the catalog CSV specified in the config.

        Expects config["file_paths"]["catalog_input_file"] to be set.

        :returns: DataFrame for the catalog.
        :rtype: pandas.DataFrame
        :raises FileNotFoundError: If the config value is missing or file not found.
        """
        catalog_path = self.config.get("file_paths", {}).get("catalog_input_file")
        if not catalog_path:
            raise FileNotFoundError("Catalog file path has not been set in config!")
        return self.get_metadata(catalog_path)


    def parse_dataset(self) -> pd.DataFrame:
        """
        Parse the dataset CSV specified in the config.

        Expects config["file_paths"]["dataset_input_file"] to be set.

        :returns: DataFrame for the dataset.
        :rtype: pandas.DataFrame
        :raises FileNotFoundError: If the config value is missing or file not found.
        """
        dataset_path = self.config.get("file_paths", {}).get("dataset_input_file")
        if not dataset_path:
            raise FileNotFoundError("Dataset file path has not been set in config!")
        return self.get_metadata(dataset_path)


    def parse_distribution(self) -> pd.DataFrame:
        """
        Parse the distribution CSV specified in the config.

        Expects config["file_paths"]["distribution_input_file"] to be set.

        :returns: DataFrame for the distribution.
        :rtype: pandas.DataFrame
        :raises FileNotFoundError: If the config value is missing or file not found.
        """
        distribution_path = self.config.get("file_paths", {}).get("distribution_input_file")
        if not distribution_path:
            raise FileNotFoundError("Distribution file path has not been set in config!")
        return self.get_metadata(distribution_path)

