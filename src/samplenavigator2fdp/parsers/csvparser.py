"""
Adapter class from csv to FDP
"""
from samplenavigator2fdp.parsers.abstractparser import AbstractParser
import pandas as pd

class CSVParser(AbstractParser):

    def __init__(self, config: dict):
        self.config = config


    def get_metadata(self, path: str) -> pd.DataFrame:
        return pd.DataFrame(pd.read_csv(path, sep=";",header=0))

    
    def parse_catalog(self) -> pd.DataFrame:
        catalog_path = self.config["file_paths"]["catalog_input_file"]
        if catalog_path == "catalog_input_file":
            raise FileNotFoundError("catalog file path has not been set in config!")
        return self.get_metadata(catalog_path)
    

    def parse_dataset(self) -> pd.DataFrame:
        dataset_path = self.config["file_paths"]["dataset_input_file"]
        return self.get_metadata(dataset_path)


    def parse_distribution(self) -> pd.DataFrame:
        distribution_path = self.config["file_paths"]["distribution_input_file"]
        return self.get_metadata(distribution_path)

