"""Import specs without year FE + time trend."""
import numpy as np, statsmodels.formula.api as smf, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _00_load import load_2016_2023

def cluster(m, data):
    return m.fit(cov_type="cluster", cov_kwds={"groups": data["region_code"]})

def run():
    df = load_2016_2023()
    d1 = df[df["income_obs"] & df["income"].notna()].copy()
    d1["log_cn"] = np.log(d1["cn_import"].replace(0, np.nan))
    d1["log_us"] = np.log(d1["us_import"].replace(0, np.nan))

    specs = {
        "a1_trend_only":  "tfr ~ log_income + log_eating_out + year_c",
        "a2_trend_quad":  "tfr ~ log_income + log_eating_out + year_c + year_c2",
        "a3_add_cn":      "tfr ~ log_income + log_eating_out + log_cn + year_c + year_c2",
        "a4_add_us":      "tfr ~ log_income + log_eating_out + log_us + year_c + year_c2",
        "a5_add_both":    "tfr ~ log_income + log_eating_out + log_cn + log_us + year_c + year_c2",
    }
    res = {}
    for n, f in specs.items():
        m = cluster(smf.ols(f, data=d1), d1); res[n] = m
        print(f"\n--- {n} ---")
        print(m.summary().tables[1])
        print(f"N={int(m.nobs)}, R2={m.rsquared:.3f}")
    return res

if __name__ == "__main__":
    run()
