"""Pytest fixtures for testing the meta2fdp package."""

import pytest
from dotenv import load_dotenv
from pathlib import Path


def pytest_configure():
    """Load environment variables from the .env.test file before any tests are run."""
    load_dotenv(dotenv_path=Path(__file__).parent / ".env.test")


@pytest.fixture(scope="session")
def test_dir(request) -> Path:
    """Return the path to the tests directory."""
    tests_root = Path(request.config.rootpath) / "tests"
    return tests_root


@pytest.fixture(scope="session")
def data_dir(test_dir) -> Path:
    """Return the path to the tests/data directory."""
    return test_dir / "data"


@pytest.fixture(scope="session")
def config_path(test_dir) -> Path:
    """Return the path to the configuration YAML file for the CSV parser tests."""
    return test_dir / "config" / "configuration_csv.yaml"


@pytest.fixture(scope="session")
def config(config_path):
    """Load the configuration from the YAML file and return it as a dictionary."""
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
    """Load the model/schema configuration from the YAML file and return it as a dictionary."""
    import yaml

    with open(test_dir / "config" / "model_config_test.yaml", "r") as fh:
        return yaml.safe_load(fh)
