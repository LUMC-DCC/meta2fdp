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
def config():
    # used in build_fdp fixture to set env vars for the client configuration, and potentially in the future to set other configuration values for the test
    return {
        "FDP": {
            "URL": "FDP_URL",
            "username": "FDP_USERNAME",
        },
        "mode": {"publish": True},
        "stayalive": False,  # set to True to keep the FDP server running after the tests are done, for debugging purposes
    }
