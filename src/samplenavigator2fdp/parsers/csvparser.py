"""
Adapter class from csv to FDP
"""
from samplenavigator2fdp.parsers.abstractparser import Parser
from typing import override
import pandas as pd

class CSVParser(Parser):

    def __init__(self, config: dict):
        self.config = config

    @override
    def get_metadata(self, path: str) -> pd.DataFrame:
        return pd.read_csv(path, sep=";",header=0)

    @override
    def parse_catalog(self) -> pd.DataFrame:
        catalog_path = self.config["file_paths"]["catalog_input_file"]
        if catalog_path == "catalog_input_file":
            raise FileNotFoundError("catalog file path has not been set in config!")
        return self.get_metadata(catalog_path)
    
    @override
    def parse_dataset(self) -> pd.DataFrame:
        dataset_path = self.config["file_paths"]["dataset_input_file"]
        return self.get_metadata(dataset_path)


    @override
    def parse_distribution(self) -> pd.DataFrame:
        distribution_path = self.config["file_paths"]["distribution_input_file"]
        return self.get_metadata(distribution_path)

