import numpy as np
from pathlib import Path
import os

workdir = os.path.dirname(os.path.realpath(__file__))


LONGITUDES = list(np.arange(-90.0, 90.25, 0.25))
LATITUDES = list(np.arange(-180.0, 180.25, 0.25))

PROJECT_DIR = Path(workdir).parent
DATA_DIR = PROJECT_DIR / "data"

CDSAPIRC_PATH = Path.home() / ".cdsapirc"
