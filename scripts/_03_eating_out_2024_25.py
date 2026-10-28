"""2024-2025 eating-out-only + full 2016-2025 EO panel."""
import numpy as np, statsmodels.formula.api as smf, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _00_load import load_full_panel

def cluster(m, data):
    return m.fit(cov_type="cluster", cov_kwds={"groups": data["region_code"]})

def run():
    df = load_full_panel()
    d24 = df[df["year"].isin([2024, 2025])].copy()
    d_all = df[df["tfr"].notna() & df["eating_out"].notna()].copy()

    res = {}
    res["b1_pooled_EO"]     = cluster(smf.ols("tfr ~ log_eating_out + C(year)", data=d24), d24)
    res["b2_prefFE_EO"]     = cluster(smf.ols("tfr ~ log_eating_out + C(year)+C(region_code)", data=d24), d24)
    res["b3_pooled_EO_cap"] = cluster(smf.ols("tfr ~ log_cap_meals + C(year)", data=d24), d24)
    res["b4_prefFE_EO_cap"] = cluster(smf.ols("tfr ~ log_cap_meals + C(year)+C(region_code)", data=d24), d24)
    res["b6_full_2016_25"]  = cluster(smf.ols("tfr ~ log_eating_out + C(year)+C(region_code)", data=d_all), d_all)

    for n, m in res.items():
        print(f"\n--- {n} ---")
        print(m.summary().tables[1])
        print(f"N={int(m.nobs)}, R2={m.rsquared:.3f}")
    return res

if __name__ == "__main__":
    run()
