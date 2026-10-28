"""Core income/eating-out regressions (Table 1)."""
import pandas as pd, numpy as np, statsmodels.formula.api as smf, os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from _00_load import load_2016_2023

def run():
    df = load_2016_2023()
    data = df[df["income_obs"] & df["income"].notna()].copy()
    specs = {
        "(1) OLS+yrFE": "tfr ~ log_income + log_eating_out + C(year)",
        "(2) PrefFE": "tfr ~ log_income + log_eating_out + C(region_code)",
        "(3) 2wayFE": "tfr ~ log_income + log_eating_out + C(region_code) + C(year)",
    }
    results = {}
    for name, formula in specs.items():
        model = smf.ols(formula, data=data).fit(
            cov_type="cluster", cov_kwds={"groups": data["region_code"]})
        results[name] = model
        print(f"\n--- {name} ---")
        print(model.summary())
    return results

if __name__ == "__main__":
    run()
