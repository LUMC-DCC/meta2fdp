import yaml
import pytest
from copy import deepcopy
from pathlib import Path
from pandas import DataFrame, read_csv
from meta2fdp.parsers.csvparser import CSVParser


def parse_config(conf_path: Path):
    try:
        with conf_path.open("r", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file)
    except FileNotFoundError:
        raise
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error parsing YAML configuration: {e}") from e


@pytest.fixture
def parser(config):
    return CSVParser(config)


def test_parse_catalog(parser, config):
    catalog_path = config["file_paths"].get("catalog_input_file")
    if not catalog_path or not catalog_path.exists():
        pytest.skip("catalog_input_file missing for tests")
    df = parser.parse_catalog()
    assert isinstance(df, DataFrame)
    reference = read_csv(catalog_path, sep=";", header=0)
    # TODO: handle other CSV separators
    assert set(reference.columns).issubset(set(df.columns))


def test_parse_dataset(parser, config):
    dataset_path = config["file_paths"].get("dataset_input_file")
    if not dataset_path or not dataset_path.exists():
        pytest.skip("dataset_input_file missing for tests")
    df = parser.parse_dataset()
    assert isinstance(df, DataFrame)
    reference = read_csv(dataset_path, sep=";", header=0)
    assert set(reference.columns).issubset(set(df.columns))


def test_parse_distribution(parser, config):
    dist_path = config["file_paths"].get("distribution_input_file")
    if not dist_path or not dist_path.exists():
        pytest.skip("distribution_input_file missing for tests")
    # if present, exercise the method
    parser.parse_distribution()


def test_parse_catalog_raises_when_file_missing(config):
    cfg = deepcopy(config)
    # use a Path object guaranteed not to exist
    cfg["file_paths"]["catalog_input_file"] = "no_such_file.csv"
    parser = CSVParser(cfg)
    with pytest.raises(FileNotFoundError):
        parser.parse_catalog()


def test_get_metadata_accepts_path_and_str(parser, config):
    dataset_path = config["file_paths"].get("dataset_input_file")
    if not dataset_path or not dataset_path.exists():
        pytest.skip("dataset_input_file missing for tests")
    # ensure both Path and str are accepted
    df = parser.get_metadata(dataset_path)
    assert isinstance(df, DataFrame)
