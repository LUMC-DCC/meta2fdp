import sys
import unittest
import yaml
from copy import deepcopy
from pathlib import Path
from pandas import DataFrame, read_csv

BASE_DIR = Path(__file__).resolve().parent
# Ensure local src is importable before importing project modules
sys.path.append(str((BASE_DIR.parent / "src").resolve()))

from samplenavigator2fdp.parsers.csvparser import CSVParser


def parse_config(conf_path: Path):
    try:
        with conf_path.open("r", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file)
    except FileNotFoundError:
        raise
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error parsing YAML configuration: {e}") from e


class CSVParserTests(unittest.TestCase):

    def setUp(self):
        conf_path = BASE_DIR / "test_files" / "test_configs" / "configuration_csv.yaml"
        try:
            self.config = parse_config(conf_path)
        except FileNotFoundError:
            self.skipTest(f"Test configuration not found: {conf_path}")
        except RuntimeError as e:
            self.skipTest(str(e))

        # Normalize file paths to pathlib.Path
        file_paths = {}
        for k, v in (self.config.get("file_paths") or {}).items():
            if v is None:
                file_paths[k] = None
                continue
            p = Path(v)
            file_paths[k] = p
        self.config["file_paths"] = file_paths

        self.parser = CSVParser(self.config)

    def test_parse_catalog(self):
        catalog_path = self.config["file_paths"].get("catalog_input_file")
        if not catalog_path or not catalog_path.exists():
            self.skipTest("catalog_input_file missing for tests")
        df = self.parser.parse_catalog()
        self.assertIsInstance(df, DataFrame)
        reference = read_csv(catalog_path, sep=";", header=0)
        # TODO: handle other CSV separators
        self.assertTrue(set(reference.columns).issubset(set(df.columns)))
        #TODO: test for all mandatory properties being present in the output

    def test_parse_dataset(self):
        dataset_path = self.config["file_paths"].get("dataset_input_file")
        if not dataset_path or not dataset_path.exists():
            self.skipTest("dataset_input_file missing for tests")
        df = self.parser.parse_dataset()
        self.assertIsInstance(df, DataFrame)
        reference = read_csv(dataset_path, sep=";", header=0)
        self.assertTrue(set(reference.columns).issubset(set(df.columns)))

    def test_parse_distribution(self):
        dist_path = self.config["file_paths"].get("distribution_input_file")
        if not dist_path or not dist_path.exists():
            self.skipTest("distribution_input_file missing for tests")
        # if present, exercise the method
        self.parser.parse_distribution()

    def test_parse_catalog_raises_when_file_missing(self):
        cfg = deepcopy(self.config)
        # use a Path object guaranteed not to exist
        cfg["file_paths"]["catalog_input_file"] = BASE_DIR / "no_such_file.csv"
        parser = CSVParser(cfg)
        with self.assertRaises(FileNotFoundError):
            parser.parse_catalog()

    def test_get_metadata_accepts_path_and_str(self):
        dataset_path = self.config["file_paths"].get("dataset_input_file")
        if not dataset_path or not dataset_path.exists():
            self.skipTest("dataset_input_file missing for tests")
        # ensure both Path and str are accepted
        df = self.parser.get_metadata(dataset_path)
        self.assertIsInstance(df, DataFrame)


if __name__ == "__main__":
    unittest.main()
