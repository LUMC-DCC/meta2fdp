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
