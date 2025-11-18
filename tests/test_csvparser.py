import sys
import pathlib
from unittest import TestCase
import yaml
from samplenavigator2fdp.parsers import csvparser
from samplenavigator2fdp.fdp import FDPClient
from tests import build_fdp
import subprocess



DATA_DIR = pathlib.Path(__file__)
RESOURCES_PASS_DIR = DATA_DIR.joinpath("test_pass")

class CSVParserTests(TestCase):

    def setUp(self):
        conf_path = "tests/test_files/test_configs/configuration_csv.yaml"
        try:
            with open(conf_path, "r") as config_file:
                self.config = yaml.safe_load(config_file)  # used to obtain right value types from the yaml like booleans
        except FileNotFoundError:
            print(f"Configuration file not found: {conf_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"Error parsing YAML configuration file: {e}")
            sys.exit(1) 
        self.client = FDPClient.FDPClient(fdp_url=self.config["FDP"]["URL"], username=self.config["FDP"]["username"],password=self.config["FDP"]["password"], persistent_url=self.config["FDP"]["catalog_purl"],verbose=True)
        build_fdp.setup()


    def tearDown(self):
        subprocess.run(["docker", "compose", "down"], cwd=pathlib.Path("tests\\test_integration\\compose\\fdp\\ephemeral\\v1"))
        pass


    def test_parse_cat_dat_pass(self):
        parser = csvparser.CSVParser(config=self.config, client=self.client)
        try:
            parser.parse_cat_dat(self.config["file_paths"]["catalog_input_file"], self.config["file_paths"]["datasets_input_file"], publish=True)
        except Exception:
            self.fail("")
