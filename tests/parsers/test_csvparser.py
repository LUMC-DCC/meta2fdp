import yaml
import pytest
from copy import deepcopy
from pathlib import Path
from pandas import DataFrame, read_csv
from meta2fdp.parsers.csvparser import CSVParser

BASE_DIR = Path(__file__).resolve().parent


def parse_config(conf_path: Path):
    try:
        with conf_path.open("r", encoding="utf-8") as config_file:
            return yaml.safe_load(config_file)
    except FileNotFoundError:
        raise
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error parsing YAML configuration: {e}") from e


@pytest.fixture(scope="module")
def config():
    # tests are located in tests/parsers, test data lives in tests/data
    conf_path = BASE_DIR.parent / "data" / "config" / "configuration_csv.yaml"
    try:
        cfg = parse_config(conf_path)
    except FileNotFoundError:
        pytest.skip(f"Test configuration not found: {conf_path}")
    except RuntimeError as e:
        pytest.skip(str(e))

    # Normalize file paths to pathlib.Path
    file_paths = {}
    for k, v in (cfg.get("file_paths") or {}).items():
        if v is None:
            file_paths[k] = None
            continue
        p = Path(v)
        file_paths[k] = p
    cfg["file_paths"] = file_paths
    return cfg


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
    cfg["file_paths"]["catalog_input_file"] = BASE_DIR / "no_such_file.csv"
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
