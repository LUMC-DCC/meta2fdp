import unittest
import yaml
import pathlib
import sys


BASE_DIR = pathlib.Path(__file__).resolve().parent

# facilitate running tests from command line using `python -m unittest`
sys.path.append(str(BASE_DIR.parent / 'src'))
from samplenavigator2fdp.parsers.csvparser import CSVParser
import sys
import pathlib
from pandas import DataFrame, read_csv

config_path = pathlib.Path("tests/test_files/test_configs/configuration_csv.yaml")

def parse_config(conf_path):
        try:
            with open(conf_path, "r") as config_file:
                config = yaml.safe_load(config_file)  # used to obtain right value types from the yaml like booleans
                return config
        except FileNotFoundError:
            print(f"Configuration file not found: {conf_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML configuration file: {e}")
            sys.exit(1) 

config = parse_config(config_path)

class CSVParserTests(unittest.TestCase):

    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.config = config
        self.parser = CSVParser(self.config)


    def testparse_catalog(self):
        catalog = self.parser.parse_catalog()
        self.assertEqual(type(catalog), DataFrame, "Catalog is not a DataFrame")
        test_read = read_csv(self.config["file_paths"]["catalog_input_file"], sep=";",header=0)
        #TODO might need to become a check if all mandatory property headers are there
        self.assertTrue(
            len(set(test_read.columns.to_list())-set(catalog.columns.to_list())) == 0,
            "Not all reference properties in parsed catalog dataframe colnames!"
        )

    def testparse_dataset(self):
        dataset = self.parser.parse_dataset()
        self.assertEqual(type(dataset), DataFrame, "dataset is not a DataFrame")
        test_read = read_csv(self.config["file_paths"]["dataset_input_file"], sep=";",header=0)
        #TODO might need to become a check if all mandatory property headers are there
        self.assertTrue(
            len(set(test_read.columns.to_list())-set(dataset.columns.to_list())) == 0,
            "Not all reference properties in parsed dataset dataframe colnames!"
        )

    @unittest.skipIf(config["file_paths"]["distribution_input_file"] == "distribution_input_file", "no distribution file in test config yet, skipping distribution parsing test.")
    def testparse_distribution(self):
        self.parser.parse_distribution()

    @unittest.skipIf(config["file_paths"]["dataservice_input_file"] == "dataservice_input_file", "no datasetseries file in test config yet, skipping datasetseries parsing test.")
    def testparse_dataservice(self):
        self.parser.parse_dataservice()
    
    @unittest.skipIf(config["file_paths"]["datasetseries_input_file"] == "datasetseries_input_file", "no datasetseries file in test config yet, skipping datasetseries parsing test.")
    def testparse_datasetseries(self):
        self.parser.parse_distribution()
