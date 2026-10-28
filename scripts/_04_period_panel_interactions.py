"""Period-panel organic/gardening/import-interaction specs -> Table 2."""
import numpy as np, statsmodels.formula.api as smf, os, sys
from scipy.stats import norm
sys.path.insert(0, os.path.dirname(__file__))
from _00_load import load_period_panel

def cluster(m, data):
    return m.fit(cov_type="cluster", cov_kwds={"groups": data["region_code"]})

def run():
    dp = load_period_panel()
    dp_obs = dp[dp["eligible_observed_income_regression"] == True].copy()

    specs = {
     "i1_base":       "tfr ~ log_income + log_eating_out + organic_farming_context_z + female_gardening_context_z + C(period_code)+C(region_code)",
     "i2_cn_main":    "tfr ~ log_income + log_eating_out + cn_import + organic_farming_context_z + female_gardening_context_z + C(period_code)+C(region_code)",
     "i3_cn_x_org":   "tfr ~ log_income + log_eating_out + cn_import*organic_farming_context_z + female_gardening_context_z + C(period_code)+C(region_code)",
     "i4_us_x_org":   "tfr ~ log_income + log_eating_out + us_import*organic_farming_context_z + female_gardening_context_z + C(period_code)+C(region_code)",
     "i5_both_x_org": "tfr ~ log_income + log_eating_out + cn_import*organic_farming_context_z + us_import*organic_farming_context_z + female_gardening_context_z + C(period_code)+C(region_code)",
     "i6_cn_x_fgard": "tfr ~ log_income + log_eating_out + cn_import*female_gardening_context_z + organic_farming_context_z + C(period_code)+C(region_code)",
    }
    res = {}
    for n, f in specs.items():
        m = cluster(smf.ols(f, data=dp_obs), dp_obs); res[n] = m
        print(f"\n--- {n} ---"); print(m.summary().tables[1])
        print(f"N={int(m.nobs)}, R2={m.rsquared:.3f}")

    # marginal effect of China imports at organic z = -1, 0, +1 (spec i3)
    m3 = res["i3_cn_x_org"]
    b  = m3.params.get("cn_import", np.nan)
    bI = m3.params.get("cn_import:organic_farming_context_z", np.nan)
    V  = m3.cov_params()
    print("\nMarginal effect of China import on TFR at organic z:")
    for z in [-1, 0, 1]:
        est = b + bI*z
        var = (V.loc["cn_import","cn_import"]
               + z**2*V.loc["cn_import:organic_farming_context_z","cn_import:organic_farming_context_z"]
               + 2*z*V.loc["cn_import","cn_import:organic_farming_context_z"])
        se  = np.sqrt(var); p = 2*(1-norm.cdf(abs(est/se)))
        print(f"  z={z:+.0f}: {est:+.4f} (SE {se:.4f}, p={p:.3f})")
    return res

if __name__ == "__main__":
    run()
