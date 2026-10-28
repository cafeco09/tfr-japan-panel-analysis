"""Optional model audit; preserves the original pipeline and output tables.

Run from any directory: python scripts/_07_diagnostics.py
Sensitivity specifications are reported together, not selected by significance.
"""
from pathlib import Path
import json
import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _00_load import DATA, OUT, load_2016_2023, load_full_panel, load_period_panel

DEST = Path(OUT) / "audit"
DEST.mkdir(parents=True, exist_ok=True)
CORE = "tfr ~ log_income + log_eating_out + C(region_code) + C(year)"
FE = "tfr ~ C(region_code) + C(year)"


def fit(formula, data, require_full_rank=True):
    model = smf.ols(formula, data=data, missing="raise")
    rank = np.linalg.matrix_rank(model.exog)
    if require_full_rank and rank != model.exog.shape[1]:
        raise ValueError(f"Rank deficient: {formula}: {rank}/{model.exog.shape[1]}")
    return model.fit(cov_type="cluster", cov_kwds={"groups": data.region_code}, use_t=True)


def rows(name, result, variables, data, baseline=None):
    answer = []
    for variable in variables:
        ci = result.conf_int().loc[variable]
        answer.append(dict(spec=name, variable=variable, coefficient=result.params[variable],
                           cluster_se=result.bse[variable], p=result.pvalues[variable],
                           ci_low=ci.iloc[0], ci_high=ci.iloc[1], n=int(result.nobs),
                           clusters=data.region_code.nunique(), years=data.year.nunique(),
                           rank=np.linalg.matrix_rank(result.model.exog),
                           columns=result.model.exog.shape[1], r2=result.rsquared,
                           incremental_r2_over_FE=(1-result.ssr/baseline.ssr
                                                   if baseline is not None else np.nan)))
    return answer


def main():
    d = load_2016_2023()
    d = d[d.income_obs & d.income.notna()].copy().sort_values(["region_code", "year"])
    if not np.isfinite(d[["tfr", "log_income", "log_eating_out"]]).all().all():
        raise ValueError("Core sample contains non-finite model inputs")
    all_panel = load_full_panel()
    period = load_period_panel()
    raw = pd.read_csv(Path(DATA) / "dated_source_panel_2016_2025.csv")
    # Recover year using the exact shared outcome/expenditure keys, with no row-order assumption.
    key = ["region_code", "tfr", "eating_out"]
    period = period.merge(all_panel[key + ["year"]], on=key, how="left", validate="one_to_one")
    if period.year.isna().any():
        raise ValueError("Could not uniquely recover year for every period-panel row")
    p = period[period.eligible_observed_income_regression.eq(True)].copy()
    annual = raw.rename(columns={"observed_income_jpy_per_resident":"income",
                                  "china_national_crop_import_kg_per_resident":"cn_import",
                                  "usa_national_crop_import_kg_per_resident":"us_import"})
    aligned = period.merge(annual[["region_code","year","income","cn_import","us_import"]],
                           on=["region_code","year"], validate="one_to_one", suffixes=("","_annual"))
    for column in ["income","cn_import","us_import"]:
        assert np.allclose(aligned[column], aligned[column+"_annual"], equal_nan=True), column
    p["year_c"] = p.year-p.year.min()
    snapshot = p.groupby("region_code")[["organic_farming_context_z", "female_gardening_context_z"]].nunique()
    assert snapshot.eq(1).all().all()
    assert raw.groupby("year")[["china_national_crop_import_kg_per_resident",
                                "usa_national_crop_import_kg_per_resident"]].nunique().eq(1).all().all()
    assert not raw.duplicated(["region_code", "year"]).any()
    checks = dict(core_n=len(d), prefectures=d.region_code.nunique(),
                  years=sorted(map(int,d.year.unique())), period_rows=len(period),
                  eligible_period_rows=len(p),
                  recovered_period_years={str(k): sorted(map(int,v.year.unique()))
                                         for k,v in period.groupby("period_code")},
                  duplicate_prefecture_years=int(raw.duplicated(["region_code","year"]).sum()),
                  tfr_2025_status=sorted(raw.loc[raw.year.eq(2025),"tfr_release_status"].unique().tolist()))
    (DEST / "data_checks.json").write_text(json.dumps(checks, indent=2)+"\n")

    # Same complete-case sample for each pair of nested core/FE-only models.
    balanced_regions = d.groupby("region_code").size().loc[lambda s:s.eq(8)].index
    samples = {
        "annual_two_way_FE": d,
        "balanced_42_prefectures": d[d.region_code.isin(balanced_regions)].copy(),
        "pre_COVID_2016_2019": d[d.year.le(2019)].copy(),
        "exclude_2020_2021": d[~d.year.isin([2020,2021])].copy(),
        "exclude_Tokyo": d[d.region_code.ne("JP-13")].copy(),
        "exclude_Okinawa": d[d.region_code.ne("JP-47")].copy(),
        "exclude_Tokyo_Okinawa": d[~d.region_code.isin(["JP-13","JP-47"])].copy(),
        "annual_2017_2023_period_sample": d[d.year.ge(2017)].copy(),
    }
    core_rows = []
    for name, sample in samples.items():
        core_rows += rows(name, fit(CORE,sample), ["log_income","log_eating_out"],
                          sample, fit(FE,sample))
    trend = d.copy()
    trend["year_c"] = trend.year-trend.year.min()
    # One reference-prefecture trend is omitted: annual FE already span the common trend.
    trend_columns = []
    for region in sorted(trend.region_code.unique())[1:]:
        name = "trend_"+region.replace("-", "_")
        trend[name] = trend.region_code.eq(region).astype(int)*trend.year_c
        trend_columns.append(name)
    trend_terms = " + " + " + ".join(trend_columns)
    trend_fe = FE + trend_terms
    core_rows += rows("prefecture_specific_linear_trends", fit(CORE+trend_terms,trend),
                      ["log_income","log_eating_out"],trend,fit(trend_fe,trend))
    lag = d.copy()
    for col in ["log_income","log_eating_out"]:
        lag["lag_"+col] = lag.groupby("region_code")[col].shift()
    lag = lag[(lag.year-lag.groupby("region_code").year.shift()).eq(1)].copy()
    lag_formula = "tfr ~ lag_log_income + lag_log_eating_out + C(region_code) + C(year)"
    core_rows += rows("one_year_lagged_covariates",fit(lag_formula,lag),
                      ["lag_log_income","lag_log_eating_out"],lag,fit(FE,lag))
    diff = d.copy()
    for col in ["tfr","log_income","log_eating_out"]:
        diff["d_"+col] = diff.groupby("region_code")[col].diff()
    diff = diff[(diff.year-diff.groupby("region_code").year.shift()).eq(1)].copy()
    diff_formula = "d_tfr ~ d_log_income + d_log_eating_out + C(year)"
    core_rows += rows("first_differences_with_year_effects",fit(diff_formula,diff),
                      ["d_log_income","d_log_eating_out"],diff)
    core_table = pd.DataFrame(core_rows)
    core_table.to_csv(DEST/"core_sensitivity.csv",index=False)

    # Leave one prefecture out: 47 predefined fits, all exported.
    leave_rows = []
    for region in sorted(d.region_code.unique()):
        sample=d[d.region_code.ne(region)].copy()
        leave_rows += rows(region,fit(CORE,sample),["log_income","log_eating_out"],sample)
    leave_table=pd.DataFrame(leave_rows)
    leave_table.to_csv(DEST/"leave_one_prefecture_out.csv",index=False)

    # Compare period effects with annual effects on identical rows.
    base="tfr ~ log_income + log_eating_out + C(region_code)"
    org="organic_farming_context_z"
    gard="female_gardening_context_z"
    specs={
        "legacy_base":base+f" + {org} + {gard} + C(period_code)",
        "legacy_China_interaction":base+f" + cn_import*{org} + {gard} + C(period_code)",
        "period_FE_identified_China_interaction":base+f" + cn_import + cn_import:{org} + C(period_code)",
        "annual_FE_base":base+" + C(year)",
        "annual_FE_China_interaction":base+f" + cn_import:{org} + C(year)",
        "annual_FE_USA_interaction":base+f" + us_import:{org} + C(year)",
        "annual_FE_both_interactions":base+f" + cn_import:{org} + us_import:{org} + C(year)",
        "annual_FE_China_gardening_interaction":base+f" + cn_import:{gard} + C(year)",
        "annual_FE_China_interaction_context_trend":base+f" + cn_import:{org} + {org}:year_c + C(year)",
    }
    interaction_rows=[]
    ranks=[]
    for name,formula in specs.items():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result=fit(formula,p,require_full_rank=not name.startswith("legacy"))
        ranks.append(dict(spec=name,n=int(result.nobs),columns=result.model.exog.shape[1],
                          rank=np.linalg.matrix_rank(result.model.exog)))
        variables=[v for v in result.params.index if v in ["log_income","log_eating_out","cn_import"]
                   or v.startswith("cn_import:") or v.startswith("us_import:")]
        interaction_rows+=rows(name,result,variables,p)
    pd.DataFrame(ranks).to_csv(DEST/"model_rank.csv",index=False)
    interactions=pd.DataFrame(interaction_rows)
    interactions.to_csv(DEST/"interaction_sensitivity.csv",index=False)
    leave_year_rows=[]
    for year in sorted(p.year.unique()):
        sample=p[p.year.ne(year)].copy()
        result=fit(specs["annual_FE_China_interaction"],sample)
        leave_year_rows+=rows(str(int(year)),result,[f"cn_import:{org}"],sample)
    leave_year_table=pd.DataFrame(leave_year_rows)
    leave_year_table.to_csv(DEST/"interaction_leave_one_year_out.csv",index=False)

    # Eating-out models explicitly separate final-labelled data from provisional 2025.
    eo_rows=[]
    for name,sample in {
        "EO_2016_2024_final_labelled":all_panel[all_panel.year.le(2024)].copy(),
        "EO_2016_2025_with_provisional":all_panel.copy(),
        "EO_2024_2025_only":all_panel[all_panel.year.ge(2024)].copy(),
    }.items():
        formula="tfr ~ log_eating_out + C(region_code) + C(year)"
        eo_rows+=rows(name,fit(formula,sample),["log_eating_out"],sample,fit(FE,sample))
    pd.DataFrame(eo_rows).to_csv(DEST/"eating_out_sensitivity.csv",index=False)

    def table(frame, columns):
        formatted=frame[columns].copy()
        for c in formatted.select_dtypes(include="number"):
            formatted[c]=formatted[c].map(lambda x:f"{x:.4f}" if pd.notna(x) else "—")
        return "| "+" | ".join(columns)+" |\n|"+"|".join(["---"]*len(columns))+"|\n"+"\n".join(
            "| "+" | ".join(map(str,r))+" |" for r in formatted.itertuples(index=False,name=None))
    summary=["# Model audit", "", "Audit date: 28 October 2026. Source CSVs and original model outputs are unchanged.",
             "", "## Data and identification", "",
             "- The core sample contains 371 observed-income rows across 47 prefectures and eight years.",
             "- The period file is annual data with year labels removed, not period averages. Exact matching recovers years for every row: period 1 = 2017–2019, 2 = 2020–2021, 3 = 2022–2023, 4 = 2024–2025.",
             "- The eligible period sample has 324 rows from 2017–2023; there are no eligible income rows in period 4.",
             "- Both context variables are constant within prefecture. National imports are constant within year.",
             "- Annual fixed effects absorb national import main effects. Prefecture fixed effects absorb context main effects. The full-rank annual interaction models therefore omit those absorbed terms.",
             "- The 2025 TFR entries are explicitly labelled provisional in the supplied data. This audit checks internal structure, not every external source value.",
             "", "## Core sensitivity estimates", "",
             "Cluster standard errors use a t reference distribution with cluster degrees of freedom. The original tables use the normal reference distribution. Sensitivity specifications change the estimand and are not interchangeable estimates of one causal effect.", "",
             table(core_table,["spec","variable","coefficient","cluster_se","p","n","incremental_r2_over_FE"]),
             "", "The incremental R² measures improvement over the matching fixed-effects-only model, not the total R² dominated by prefecture and year effects. It is in-sample, not predictive validation.",
             "", "## Leave-one-prefecture-out", ""]
    for variable,g in leave_table.groupby("variable"):
        low=g.loc[g.coefficient.idxmin()]; high=g.loc[g.coefficient.idxmax()]
        summary.append(f"- {variable}: coefficients range {low.coefficient:.4f} (omit {low.spec}) to {high.coefficient:.4f} (omit {high.spec}); {int(g.p.lt(.05).sum())}/47 fits have p < 0.05. These dependent fits are influence diagnostics, not 47 replications.")
    summary += ["", "## Rank checks", "", table(pd.DataFrame(ranks),["spec","rank","columns","n"]),
                "", "## Interaction sensitivity", "",
                table(interactions[interactions.variable.str.contains(":")],
                      ["spec","variable","coefficient","cluster_se","p","n"]),
                "", "Legacy context main effects are not uniquely identified because they are absorbed by prefecture effects. The import main effect is algebraically estimable under coarse period effects, since imports still vary within periods, but remains exposed to annual national confounding. Removing the absorbed context main effects leaves the legacy China interaction unchanged; the rank warning alone does not invalidate every coefficient.",
                "", "With annual effects, the national import main effect is absorbed and absolute import marginal effects cannot be estimated. The annual-FE interaction describes differential exposure by context, conditional on common year shocks; it is not a national average import effect or proof of a protective organic-farming mechanism.",
                "", "Only seven annual exposure values enter the eligible interaction sample. Prefecture clustering does not establish robustness to residual common national shocks. Few-year inference, multiple exploratory tests and context-specific trends remain unresolved.",
                "", "### China interaction: omit each year", "",
                table(leave_year_table,["spec","coefficient","cluster_se","p","n"]),
                "", "The spec label is the omitted year. These are dependent influence checks, not independent replications. The context-trend specification above tests whether the interaction survives a linear trend proportional to organic context; it does not control all context-specific shocks.",
                "", "## Eating-out sensitivity", "",table(pd.DataFrame(eo_rows),["spec","coefficient","cluster_se","p","n"]),
                "", "## Next improvements", "",
                "1. Replace the legacy exploratory models with full-rank annual-FE interaction models and remove unidentified main effects and absolute marginal-effect claims from exports.",
                "2. Pre-specify the main estimand and sensitivity set; retain sign changes and null results rather than choosing models by p-value.",
                "3. Audit the raw income measure, price basis and source vintages; a national deflator only shifts log covariates by year and is absorbed by annual fixed effects. Prefecture-specific living costs require extra data.",
                "4. Seek repeated demographic controls such as age structure, marriage, migration and urbanisation with a causal rationale. Avoid treating mediators as routine controls.",
                "5. Separate provisional/final data, replace the duplicate synthetic-exclusion check with a real observed-versus-imputed comparison if imputation is scientifically justified, and add source checks and explicit finite-value/sample checks to every model.",
                "6. If prediction is the goal, define a forecast horizon and use forward-in-time evaluation against simple baselines. R² from fixed-effect regressions is insufficient.", ""]
    (DEST/"MODEL_AUDIT.md").write_text("\n".join(summary))
    print(f"Audit written to {DEST}")
    print(core_table[["spec","variable","coefficient","p"]].to_string(index=False))
    print(interactions[interactions.variable.str.contains(":")][["spec","coefficient","p"]].to_string(index=False))


if __name__ == "__main__":
    main()
