import pathlib
import sys

BASE_DIR = pathlib.Path(__file__).resolve().parent

# facilitate running tests from command line using `python -m unittest`
sys.path.append(str(BASE_DIR.parent / 'samplenavigator2fdp'))