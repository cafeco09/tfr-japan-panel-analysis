"""Core income/eating-out regressions (Table 1)."""
import pandas as pd, numpy as np, statsmodels.formula.api as smf, os
from importlib.util import spec_from_file_location, module_from_spec
import sys
sys.path.insert(0, os.path.dirname(__file__))
from _00_load import load_2016_2023  # rename file to _00_load.py or adjust

# NOTE: save 00_load.py as _00_load.py to import directly, or use exec.
