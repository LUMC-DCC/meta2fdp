from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent

# facilitate running tests from command line using `python -m unittest`
sys.path.append(str(BASE_DIR.parent / 'src'))