from pathlib import Path
import pytest
# import sys


# BASE_DIR = Path(__file__).resolve().parent

# facilitate running tests from command line using `python -m unittest`
# sys.path.append(str(BASE_DIR.parent / 'src'))


@pytest.fixture(scope="session")
def data_dir(request) -> Path:
    tests_root = Path(request.config.rootpath) / "tests"
    return tests_root / "data"


@pytest.fixture(scope="session")
def config(data_dir):
    import yaml

    with open(data_dir / "config" / "configuration_csv.yaml", "r") as fh:
        return yaml.safe_load(fh)


@pytest.fixture(scope="session")
def model_config(data_dir):
    import yaml

    with open(data_dir / "config" / "model_config_test.yaml", "r") as fh:
        return yaml.safe_load(fh)
