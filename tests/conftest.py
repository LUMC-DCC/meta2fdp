from pathlib import Path
import pytest
# import sys


# BASE_DIR = Path(__file__).resolve().parent

# facilitate running tests from command line using `python -m unittest`
# sys.path.append(str(BASE_DIR.parent / 'src'))


@pytest.fixture(scope="session")
def test_dir(request) -> Path:
    tests_root = Path(request.config.rootpath) / "tests"
    return tests_root


@pytest.fixture(scope="session")
def data_dir(test_dir) -> Path:
    return test_dir / "data"


@pytest.fixture(scope="session")
def config_path(test_dir) -> Path:
    return test_dir / "config" / "configuration_csv.yaml"


@pytest.fixture(scope="session")
def config(config_path):
    import yaml

    with open(config_path, "r") as fh:
        # TODO: this should be part of src utils, and handle all config files, not just the one for csvparser tests
        cfg = yaml.safe_load(fh)
        file_paths = {}
        for k, v in (cfg.get("file_paths") or {}).items():
            if v is None:
                file_paths[k] = None
                continue
            p = Path(v)
            file_paths[k] = p
        cfg["file_paths"] = file_paths
        return cfg


@pytest.fixture(scope="session")
def model_config(test_dir):
    import yaml

    with open(test_dir / "config" / "model_config_test.yaml", "r") as fh:
        return yaml.safe_load(fh)
