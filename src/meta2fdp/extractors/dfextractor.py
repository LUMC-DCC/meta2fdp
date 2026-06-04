"""DFextractor: uses mappings to extract resource matadata from CSV files and return pandas.DataFrame objects."""

import logging

import pandas as pd
from meta2fdp.extractors.base import AbstractExtractor
from meta2fdp.config.extractor.extractor import ExtractorConfig


class DFExtractor(AbstractExtractor):
    """
    Adapter that reads reads or transforms dataframes to use column headers accepted by the transformer modules.

    :param config: Configuration dictionary. Expected to contain a "file_paths"
                   mapping with keys such as "catalog_input_file",
                   "dataset_input_file" and "distribution_input_file".
    :type config: dict
    """

    def __init__(self, config: ExtractorConfig):
        self.config = config
        self.config.get_mappings()

    def map_metadata(self, df: pd.DataFrame, properties: dict) -> pd.DataFrame:
        """
        Get metadata from the dataframe using the provided properties mapping. Keys in the properties mapping represent the expected output column names, while values represent the corresponding input column names in the dataframe. The function checks that all expected input column names are present in the dataframe and raises a KeyError if any are missing. If all expected columns are present, it returns a new DataFrame with columns renamed according to the properties mapping.

        :param df: The input dataframe to extract metadata from.
        :type df: pandas.DataFrame
        :param properties: A dictionary mapping the expected output column names to the corresponding input column names in the dataframe.
        :type properties: dict
        :returns: A DataFrame containing the extracted metadata with columns renamed according to the properties mapping.
        :rtype: pandas.DataFrame
        :raises KeyError: If any of the expected input column names specified in the properties mapping are not found in the dataframe.
        """
        missing_columns = [col for col in properties.values() if col not in df.columns]
        if missing_columns:
            raise KeyError(f"Missing expected columns in dataframe: {missing_columns}")

        return df.rename(columns={value: key for key, value in properties.items()})

    def parse_catalog(self, catalog_df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse the catalog dataframe

        :returns: DataFrame for the catalog.
        :rtype: pandas.DataFrame
        :raises FileNotFoundError: If the config value is missing or file not found.
        """
        logging.info("Parsing catalog dataframe using DFExtractor...")
        catalog_properties = self.config.mappings.get("catalog", False)
        if not catalog_properties:
            logging.error("Catalog properties have not been set in config!")
            logging.debug(f"Current config mappings: {self.config.mappings}")
            raise FileNotFoundError("Catalog properties have not been set in config!")
        publisher_properties = self.config.mappings.get("publisher", False)
        if not publisher_properties:
            logging.error("Publisher properties have not been set in config!")
            logging.debug(f"Current config mappings: {self.config.mappings}")
            raise FileNotFoundError("Publisher properties have not been set in config!")
        contact_point_properties = self.config.mappings.get("contact_point", False)
        if not contact_point_properties:
            logging.error("Contact point properties have not been set in config!")
            logging.debug(f"Current config mappings: {self.config.mappings}")
            raise FileNotFoundError(
                "Contact point properties have not been set in config!"
            )
        creator_properties = self.config.mappings.get("creator", False)
        if not creator_properties:
            logging.error("Creator properties have not been set in config!")
            logging.debug(f"Current config mappings: {self.config.mappings}")
            raise FileNotFoundError("Creator properties have not been set in config!")
        catalog_df = self.map_metadata(catalog_df, catalog_properties)
        catalog_df = self.map_metadata(catalog_df, publisher_properties)
        catalog_df = self.map_metadata(catalog_df, contact_point_properties)
        catalog_df = self.map_metadata(catalog_df, creator_properties)
        return catalog_df

    def parse_dataset(self, dataset_df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse the dataset dataframe

        Expects config["file_paths"]["dataset_input_file"] to be set.

        :returns: DataFrame for the dataset.
        :rtype: pandas.DataFrame
        :raises FileNotFoundError: If the config value is missing or file not found.
        """
        dataset_path = self.config.get("file_paths", {}).get("dataset_input_file")
        if not dataset_path:
            raise FileNotFoundError("Dataset file path has not been set in config!")
        return self.get_metadata(dataset_path)

    def parse_distribution(self, distribution_df: pd.DataFrame) -> pd.DataFrame:
        """
        Parse the distribution dataframe

        Expects config["file_paths"]["distribution_input_file"] to be set.

        :returns: DataFrame for the distribution.
        :rtype: pandas.DataFrame
        :raises FileNotFoundError: If the config value is missing or file not found.
        """
        distribution_path = self.config.get("file_paths", {}).get(
            "distribution_input_file"
        )
        if not distribution_path:
            raise FileNotFoundError(
                "Distribution file path has not been set in config!"
            )
        return self.get_metadata(distribution_path)
