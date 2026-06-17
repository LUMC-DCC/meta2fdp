"""DFextractor: uses mappings to extract resource matadata from CSV files and return pandas.DataFrame objects."""

import logging

import pandas as pd
import numpy as np
from meta2fdp.extractors.base import BaseExtractor
from meta2fdp.config.extractor.extractor import ExtractorConfig


class DFExtractor(BaseExtractor):
    """
    Adapter that reads reads or transforms dataframes to use column headers accepted by the transformer modules.

    :param config: Configuration dictionary. Expected to contain a "file_paths"
                   mapping with keys such as "catalog_input_file",
                   "dataset_input_file" and "distribution_input_file".
    :type config: dict
    """

    def __init__(self, config: ExtractorConfig):
        self.config = config

    def map_metadata(self, df: pd.DataFrame, properties: dict) -> pd.DataFrame:
        """
        Get metadata from the dataframe using the provided properties mapping. Keys in the properties mapping represent the expected output column names, while values represent the corresponding input column names in the dataframe. If a value is `None`, the key is treated as an optional property and a column with that name will be added to the result (filled with `pd.NA`) if it does not exist. The function checks that all required input column names are present in the dataframe and raises a KeyError if any are missing. If all required columns are present, it returns a new DataFrame with columns renamed according to the properties mapping.

        :param df: The input dataframe to extract metadata from.
        :type df: pandas.DataFrame
        :param properties: A dictionary mapping the expected output column names to the corresponding input column names in the dataframe. Keys with `None` values are treated as optional properties.
        :type properties: dict
        :returns: A DataFrame containing the extracted metadata with columns renamed according to the properties mapping.
        :rtype: pandas.DataFrame
        :raises KeyError: If any of the expected input column names specified in the properties mapping are not found in the dataframe.
        """
        optional_properties = {
            key for key, value in properties.items() if value is pd.NA or value is None
        }
        required_properties = {
            key: value
            for key, value in properties.items()
            if value is not None and value is not pd.NA
        }

        raw_lang_tags = []
        if hasattr(self.config, "mappings") and isinstance(self.config.mappings, dict):
            raw_lang_tags = self.config.mappings.get("lang_tags", [])

        if isinstance(raw_lang_tags, str):
            lang_tags = [tag.strip() for tag in raw_lang_tags.split(",") if tag.strip()]
        elif isinstance(raw_lang_tags, (list, tuple, set)):
            lang_tags = [str(tag).strip() for tag in raw_lang_tags if str(tag).strip()]
        else:
            lang_tags = []

        selected_columns = []
        rename_columns = {}
        missing_columns = []

        for output_name, input_name in required_properties.items():
            logging.debug(f"{output_name} output_name")
            logging.debug(f"{input_name} input_name")
            if input_name is dict:
                continue

            if input_name in df.columns:
                selected_columns.append(input_name)
                if output_name != input_name:
                    rename_columns[input_name] = output_name
                continue

            fallback_columns = []
            for langtag in lang_tags:
                candidate = f"{input_name}_{langtag}"
                if candidate in df.columns:
                    fallback_columns.append(candidate)
                    logging.info(
                        f"Column '{input_name}' is missing, but found '{candidate}' in the dataframe."
                        f" This column will be used as a fallback for '{input_name}'."
                    )

            if not fallback_columns and lang_tags:
                fallback_columns = [
                    column
                    for column in df.columns
                    if column.startswith(f"{input_name}_")
                    and column.split("_", 1)[1] in lang_tags
                ]

            if fallback_columns:
                selected_columns.extend(fallback_columns)
            else:
                missing_columns.append(input_name)

        if missing_columns:
            raise KeyError(
                f"Missing expected columns in dataframe: {missing_columns}. "
                f"Properties mapping: {properties}. "
                f"DataFrame columns: {list(df.columns)}"
            )

        result_df = df.loc[:, selected_columns].copy()

        if rename_columns:
            result_df = result_df.rename(columns=rename_columns)

        if optional_properties:
            result_df = result_df.reindex(
                columns=list(result_df.columns)
                + [col for col in optional_properties if col not in result_df.columns],
                fill_value=pd.NA,
            )

        return result_df

    def get_properties_with_prefix(self, mappings: dict, rdf_class: str) -> dict:
        properties = mappings.get(
            rdf_class, False
        )  # FIXME output is not prefixed correctly?
        properties = (
            {f"{rdf_class}_" + key: value for key, value in properties.items()}
            if properties
            else False
        )
        if not properties:
            logging.error(f"{rdf_class} properties have not been set in config!")
            logging.debug(f"Current config mappings: {mappings}")
            raise FileNotFoundError(
                f"{rdf_class} properties have not been set in config!"
            )
        return properties

    def map_resource(self, dataframe: pd.DataFrame, mappings: dict):
        """Potential replacement of map_metadata"""
        flattened_mappings = pd.json_normalize(mappings, sep="_").to_dict(
            orient="records"
        )[0]
        mapped_resource = self.map_metadata(dataframe, flattened_mappings)
        return mapped_resource.replace({np.nan: None}).to_dict("records")

    def parse_catalog(self, catalog_df: pd.DataFrame) -> list[dict]:
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
        # get properties for related classes as well, since these are needed to parse the catalog dataframe as well, and they are often nested in the catalog dataframe, so we need to flatten them out and include them in the catalog dataframe before we can map the catalog dataframe using the catalog properties mapping:
        publisher_properties = self.get_properties_with_prefix(
            catalog_properties, "publisher"
        )
        contact_point_properties = self.get_properties_with_prefix(
            catalog_properties, "contactPoint"
        )
        creator_properties = self.get_properties_with_prefix(
            catalog_properties, "creator"
        )
        catalog_properties = {
            key: value
            for key, value in catalog_properties.items()
            if type(value) is not dict
        }

        # merge properties needed for catalog:
        # TODO: remove unprefixed properties from the catalog_properties because this causes "duplicate" column headers.
        catalog_properties = {
            **catalog_properties,
            **publisher_properties,
            **contact_point_properties,
            **creator_properties,
        }
        logging.debug(catalog_properties)
        catalog_mapped = self.map_metadata(catalog_df, catalog_properties)
        return catalog_mapped.replace({np.nan: None}).to_dict("records")

    def parse_dataset(self, dataset_df: pd.DataFrame) -> list[dict]:
        """
        Parse the dataset dataframe.

        If a dataset mapping is configured, use it to rename dataset columns.
        Otherwise, return the dataset dataframe unchanged.

        :param dataset_df: The dataset dataframe returned by the connector.
        :returns: Parsed dataset DataFrame.
        :rtype: pandas.DataFrame
        """
        if dataset_df is None:
            raise ValueError("Dataset dataframe must be provided to parse_dataset.")
        dataset_properties = self.config.mappings.get("dataset", False)
        if not dataset_properties:
            logging.error("Dataset properties have not been set in config!")
            logging.debug(f"Current config mappings: {self.config.mappings}")
            raise FileNotFoundError("Dataset properties have not been set in config!")
        # get properties for related classes as well, since these are needed to parse the dataset dataframe as well, and they are often nested in the dataset dataframe, so we need to flatten them out and include them in the dataset dataframe before we can map the dataset dataframe using the dataset properties mapping:
        publisher_properties = self.get_properties_with_prefix(
            dataset_properties, "publisher"
        )
        contact_point_properties = self.get_properties_with_prefix(
            dataset_properties, "contactPoint"
        )
        creator_properties = self.get_properties_with_prefix(
            dataset_properties, "creator"
        )
        dataset_properties = {
            key: value
            for key, value in dataset_properties.items()
            if type(value) is not dict
        }

        dataset_properties = {
            **dataset_properties,
            **publisher_properties,
            **contact_point_properties,
            **creator_properties,
        }
        dataset_mapped = self.map_metadata(dataset_df, dataset_properties)
        return dataset_mapped.replace({np.nan: None}).to_dict("records")

    def parse_distribution(self, distribution_df: pd.DataFrame) -> list[dict]:
        """
        Parse the distribution dataframe.

        If a distribution mapping is configured, use it to rename distribution columns.
        Otherwise, return the distribution dataframe unchanged.

        :param distribution_df: The distribution dataframe returned by the connector.
        :returns: Parsed distribution DataFrame.
        :rtype: pandas.DataFrame
        """
        raise NotImplementedError(
            "Distribution parsing is not implemented yet in DFExtractor."
        )
