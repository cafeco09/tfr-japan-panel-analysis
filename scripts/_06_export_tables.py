"""Build Table 1, Table 2, robustness table; export CSV/LaTeX/Word."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _00_load import load_2016_2023, load_period_panel, OUT

TAB = os.path.join(OUT, "tables")

def cluster(m, d): return m.fit(cov_type="cluster", cov_kwds={"groups": d["region_code"]})

def coef_table(models, variables, labels, base):
    rows = []
    for v, lab in zip(variables, labels):
        row = {"Variable": lab}
        for n, m in models.items():
            if v in m.params.index:
                b, se, p = m.params[v], m.bse[v], m.pvalues[v]
                star = "***" if p<0.01 else "**" if p<0.05 else "*" if p<0.1 else ""
                row[n] = f"{b:.3f}{star} ({se:.3f})"
            else:
                row[n] = "—"
        rows.append(row)
    rows.append({"Variable":"N", **{n:int(m.nobs) for n,m in models.items()}})
    rows.append({"Variable":"R²", **{n:f"{m.rsquared:.3f}" for n,m in models.items()}})
    tab = pd.DataFrame(rows)

    tab.to_csv(os.path.join(TAB, f"{base}.csv"), index=False)
    with open(os.path.join(TAB, f"{base}.tex"),"w") as f:
        f.write(tab.to_latex(index=False, escape=True,
                caption="TFR regressions (cluster-robust SE by prefecture; "
                        "*** p<0.01, ** p<0.05, * p<0.1)",
                label=f"tab:{base}"))
    try:
        from docx import Document
        doc = Document(); doc.add_heading("TFR Regressions", level=1)
        t = doc.add_table(rows=1, cols=len(tab.columns)); t.style="Light Grid Accent 1"
        for j,c in enumerate(tab.columns): t.rows[0].cells[j].text=str(c)
        for _,r in tab.iterrows():
            cells = t.add_row().cells
            for j,c in enumerate(tab.columns): cells[j].text=str(r[c])
        doc.add_paragraph("Notes: cluster-robust SE by prefecture; *** p<0.01, ** p<0.05, * p<0.1.")
        doc.save(os.path.join(TAB, f"{base}.docx"))
    except ImportError:
        pass
    print(f"wrote {base}.csv/.tex/.docx")

def run():
    # ---- Table 1: core ----
    df = load_2016_2023(); d1 = df[df["income_obs"] & df["income"].notna()].copy()
    core = {
        "(1) OLS+yrFE": cluster(smf.ols("tfr ~ log_income + log_eating_out + C(year)", data=d1), d1),
        "(2) PrefFE":   cluster(smf.ols("tfr ~ log_income + log_eating_out + C(region_code)", data=d1), d1),
        "(3) 2wayFE":   cluster(smf.ols("tfr ~ log_income + log_eating_out + C(region_code)+C(year)", data=d1), d1),
    }
    coef_table(core, ["log_income","log_eating_out"],
               ["log(income)","log(eating out)"], "table1_core")

    # ---- Table 2: imports x organic ----
    dp = load_period_panel(); dp_obs = dp[dp["eligible_observed_income_regression"]==True].copy()
    pi = {
     "i1_base":       cluster(smf.ols("tfr ~ log_income + log_eating_out + organic_farming_context_z + female_gardening_context_z + C(period_code)+C(region_code)", data=dp_obs), dp_obs),
     "i2_cn_main":    cluster(smf.ols("tfr ~ log_income + log_eating_out + cn_import + organic_farming_context_z + female_gardening_context_z + C(period_code)+C(region_code)", data=dp_obs), dp_obs),
     "i3_cn_x_org":   cluster(smf.ols("tfr ~ log_income + log_eating_out + cn_import*organic_farming_context_z + female_gardening_context_z + C(period_code)+C(region_code)", data=dp_obs), dp_obs),
     "i4_us_x_org":   cluster(smf.ols("tfr ~ log_income + log_eating_out + us_import*organic_farming_context_z + female_gardening_context_z + C(period_code)+C(region_code)", data=dp_obs), dp_obs),
     "i5_both_x_org": cluster(smf.ols("tfr ~ log_income + log_eating_out + cn_import*organic_farming_context_z + us_import*organic_farming_context_z + female_gardening_context_z + C(period_code)+C(region_code)", data=dp_obs), dp_obs),
     "i6_cn_x_fgard": cluster(smf.ols("tfr ~ log_income + log_eating_out + cn_import*female_gardening_context_z + organic_farming_context_z + C(period_code)+C(region_code)", data=dp_obs), dp_obs),
    }
    coef_table(pi,
        ["log_income","log_eating_out","cn_import","us_import",
         "organic_farming_context_z","female_gardening_context_z",
         "cn_import:organic_farming_context_z","us_import:organic_farming_context_z",
         "cn_import:female_gardening_context_z"],
        ["log(income)","log(eating out)","China import","USA import",
         "Organic z","Female gardening z","China×Organic","USA×Organic","China×FemaleGard"],
        "table2_imports_interactions")

    # ---- robustness table ----
    syn = pd.read_csv(os.path.join(os.path.dirname(__file__), "..","data","synthetic_income_sensitivity_only.csv"))
    keys = set(zip(syn["region_code"], syn["year"]))
    d1s = d1[~d1.apply(lambda r:(r["region_code"],r["year"]) in keys, axis=1)].copy()

    def ext(m, v):
        return (m.params[v], m.bse[v], m.pvalues[v]) if v in m.params.index else (np.nan,)*3

    specs = {
      "(1) OLS+yrFE":  cluster(smf.ols("tfr ~ log_income + log_eating_out + C(year)", data=d1), d1),
      "(2) PrefFE":    cluster(smf.ols("tfr ~ log_income + log_eating_out + C(region_code)", data=d1), d1),
      "(3) 2wayFE":    cluster(smf.ols("tfr ~ log_income + log_eating_out + C(region_code)+C(year)", data=d1), d1),
      "(5) DropSynth": cluster(smf.ols("tfr ~ log_income + log_eating_out + C(year)", data=d1s), d1s),
    }
    rows = []
    for n, m in specs.items():
        bi, sei, pi_ = ext(m, "log_income")
        be, see, pe = ext(m, "log_eating_out")
        rows.append({"Spec": n,
                     "Income": f"{bi:.3f} ({sei:.3f})", "Income p": f"{pi_:.3f}",
                     "EatOut": f"{be:.3f} ({see:.3f})", "EatOut p": f"{pe:.3f}",
                     "N": int(m.nobs), "R2": f"{m.rsquared:.3f}"})
    rob = pd.DataFrame(rows)
    rob.to_csv(os.path.join(TAB, "robustness_table.csv"), index=False)
    print("wrote robustness_table.csv")

if __name__ == "__main__":
    run()
