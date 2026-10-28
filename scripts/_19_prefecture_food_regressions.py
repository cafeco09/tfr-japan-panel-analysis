"""Prefectural TFR and shared national food imports: regression audit.

Balanced panels; year-cluster inference is accompanied by annual-mean HC3/HAC.
National import terms cannot be identified alongside unrestricted year effects.
"""
import json
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

from _13_ml_sensitivity_projections import table

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "output/prefecture_food_regressions"


def estimate(panel, annual, spec, terms, vintage):
    rhs = " + ".join(terms)
    formula = "tfr_children_per_woman ~ " + rhs
    panel_fit = smf.ols(formula + " + C(region_code)", panel, missing="raise").fit(
        cov_type="cluster", cov_kwds={"groups":panel.year, "use_correction":True, "df_correction":True}, use_t=True)
    assert np.linalg.matrix_rank(panel_fit.model.exog) == panel_fit.model.exog.shape[1]
    annual_fits = {
        "annual_mean_HC3": smf.ols(formula, annual, missing="raise").fit(cov_type="HC3", use_t=True),
        "annual_mean_HAC_lag1": smf.ols(formula, annual, missing="raise").fit(
            cov_type="HAC", cov_kwds={"maxlags":1, "use_correction":True}, use_t=True),
    }
    fits = {"prefecture_FE_year_cluster":panel_fit, **annual_fits}
    results = []
    for covariance, fit in fits.items():
        for variable in [t for t in terms if t.startswith("log_")]:
            assert np.isclose(panel_fit.params[variable], annual_fits["annual_mean_HC3"].params[variable], atol=1e-9)
            interval = fit.conf_int().loc[variable]
            results.append(dict(training_vintage=vintage, spec=spec, inference=covariance, term=variable,
                                coefficient=fit.params[variable], se=fit.bse[variable], p_two_sided=fit.pvalues[variable],
                                ci_low=interval.iloc[0], ci_high=interval.iloc[1],
                                tfr_change_for_10pct=fit.params[variable]*np.log1p(.1),
                                panel_rows=len(panel), prefectures=panel.region_code.nunique(), annual_years=len(annual),
                                regression_n=int(fit.nobs), model_residual_df=float(fit.df_resid),
                                inference_t_df=float(getattr(fit,"df_resid_inference",fit.df_resid))))
    return results


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    source = pd.read_csv(ROOT/"output/tfr_merged/prefecture_food_imports_and_tfr_2016_2025.csv")
    assert not source.duplicated(["region_code","year"]).any()
    assert source.groupby("year").region_code.nunique().eq(47).all()
    for name, col in [("total_food","published_food_usd"), ("soyabeans","whole_soyabeans_usd"),
                      ("other_food","other_mapped_food_usd")]:
        assert source[col].gt(0).all() and source.groupby("year")[col].nunique().eq(1).all()
        source["log_"+name] = np.log(source[col])
    source["trend"] = source.year - 2016
    all_results, annual_rows, stability, absorption = [], [], [], []
    specifications = {
        "total_no_time_trend":["log_total_food"],
        "total_linear_time_trend":["log_total_food","trend"],
        "total_quadratic_time_trend":["log_total_food","trend","I(trend**2)"],
        "soyabeans_and_other_linear_trend":["log_soyabeans","log_other_food","trend"],
    }
    for vintage, panel in [("through_2024_final", source[source.year.le(2024)].copy()),
                            ("through_2025_provisional", source.copy())]:
        annual = panel.groupby("year",as_index=False).agg(
            tfr_children_per_woman=("tfr_children_per_woman","mean"),
            log_total_food=("log_total_food","first"),log_soyabeans=("log_soyabeans","first"),
            log_other_food=("log_other_food","first"),trend=("trend","first"))
        annual_rows.append(annual.assign(training_vintage=vintage))
        for spec, terms in specifications.items():
            all_results.extend(estimate(panel,annual,spec,terms,vintage))
        # Do not print pseudoinverse coefficients for a rank-deficient year-FE model.
        dummies = pd.get_dummies(panel.year,dtype=float).to_numpy()
        for term in ["log_total_food","log_soyabeans","log_other_food"]:
            x = panel[term].to_numpy()
            remainder = x-dummies@np.linalg.lstsq(dummies,x,rcond=None)[0]
            max_abs = float(np.max(np.abs(remainder)))
            assert max_abs < 1e-10
            absorption.append(dict(training_vintage=vintage,term=term,
                                   max_abs_residual_after_year_effects=max_abs,identified_with_year_FE=False))
        if vintage == "through_2024_final":
            for spec in ["total_linear_time_trend","soyabeans_and_other_linear_trend"]:
                terms=specifications[spec]
                for omitted in annual.year:
                    subset=annual[annual.year.ne(omitted)]
                    fit=smf.ols("tfr_children_per_woman ~ "+" + ".join(terms),subset).fit()
                    for term in [t for t in terms if t.startswith("log_")]:
                        stability.append(dict(spec=spec,term=term,omitted_year=int(omitted),
                                              coefficient=fit.params[term],tfr_change_for_10pct=fit.params[term]*np.log1p(.1)))
    results=pd.DataFrame(all_results)
    results.to_csv(DEST/"regression_results.csv",index=False)
    pd.concat(annual_rows).to_csv(DEST/"annual_unweighted_prefecture_means.csv",index=False)
    pd.DataFrame(absorption).to_csv(DEST/"year_fixed_effect_absorption.csv",index=False)
    stability=pd.DataFrame(stability);stability.to_csv(DEST/"leave_year_out_stability.csv",index=False)

    # Transparent one-at-a-time screening; do not put 20 groups into nine years.
    final=source[source.year.le(2024)]
    target=final.groupby("year").tfr_children_per_woman.mean()
    screening,excluded=[],[]
    columns=[c for c in source if c.startswith("group_hs") or c.startswith("soy_hs")]
    for col in columns:
        series=final.groupby("year")[col].first()
        assert final.groupby("year")[col].nunique(dropna=False).eq(1).all()
        if not series.notna().all() or not series.gt(0).all():
            excluded.append(dict(feature=col,reason="Incomplete or nonpositive primary annual data; no zero imputation"))
            continue
        frame=pd.DataFrame({"tfr":target,"log_value":np.log(series)})
        frame["trend"]=frame.index-2016
        fit=smf.ols("tfr ~ log_value + trend",frame).fit(cov_type="HC3",use_t=True)
        ci=fit.conf_int().loc["log_value"]
        screening.append(dict(feature=col,n_years=len(frame),coefficient=fit.params.log_value,
                              se_HC3=fit.bse.log_value,p_HC3=fit.pvalues.log_value,ci_low=ci.iloc[0],ci_high=ci.iloc[1],
                              tfr_change_for_10pct=fit.params.log_value*np.log1p(.1),
                              food_scope="Supplementary oilcake; excluded from food total" if col=="soy_hs230400_usd" else "Broad BEC food classification"))
    screening=pd.DataFrame(screening)
    screening["BH_q_value"]=multipletests(screening.p_HC3,method="fdr_bh")[1]
    screening.to_csv(DEST/"exploratory_product_group_screening.csv",index=False)
    pd.DataFrame(excluded).to_csv(DEST/"excluded_screening_features.csv",index=False)
    metadata=dict(run_utc=datetime.now(timezone.utc).isoformat(),primary_panel_rows=423,
                  primary_prefectures=47,primary_annual_years=9,provisional_2025_sensitivity_rows=470,
                  outcome="Prefectural period TFR; annual comparison is the unweighted mean across 47 prefectures, not the official national TFR",
                  controls="Prefecture fixed effects; no trend, common linear trend, common quadratic trend; joint whole-soyabean/other-food model",
                  inference="Panel OLS with year clusters and finite-sample correction, t reference with 8 primary cluster degrees of freedom. Annual mean regressions HC3 and lag-one HAC with residual-df t references.",
                  limits="Nine clusters are few; neither clustered, HC3 nor HAC inference is exact. Common shocks, serial dependence, nominal prices and endogeneity remain. No causal effect is identified.",
                  absorption="All three import terms are absorbed by unrestricted year fixed effects; no such coefficients estimated",
                  screening=f"One-at-a-time annual-mean models with trend; {len(screening)} tests, BH FDR across all of them. Dependent, overlapping nominal import series; exploratory only.",
                  software={p:version(p) for p in ["numpy","pandas","scipy","statsmodels"]})
    (DEST/"methods.json").write_text(json.dumps(metadata,indent=2)+"\n")
    primary=results[results.training_vintage.eq("through_2024_final")]
    stable=stability.groupby(["spec","term"]).coefficient.agg(["min","max"]).reset_index()
    report=["# Prefectural TFR and national food imports: regressions", "",
        "The negative hypothesis is not supported consistently. The total-import coefficient is negative without a time trend but positive with linear or quadratic trends. The quadratic specification is positive and significant under the reported HC3 inference. The joint soyabean coefficient is not significant and changes sign under year omission. None of the 27 exploratory product/group tests passes BH q < 0.05.", "",
        "Primary sample: 47 prefectures × 2016–2024 = 423 records, but only nine annual import observations. The 470-row sensitivity adds provisional 2025 TFR. Import values are national, nominal current USD, and identical across prefectures within year.", "",
        "The outcome is prefectural TFR. Annual checks use its unweighted mean across the 47 prefectures, which differs from Japan's official national TFR. No population weighting, consumption allocation or synthetic observations are introduced.", "",
        "## Prefecture fixed effects, year-clustered inference", "",
        table(primary[primary.inference.eq("prefecture_FE_year_cluster")],["spec","term","coefficient","se","p_two_sided","ci_low","ci_high","tfr_change_for_10pct"]), "",
        "The primary reference uses eight cluster degrees of freedom, not 423 independent import observations. Nine year clusters are few, and clustering by year does not handle arbitrary serial correlation across years. Time trends restrict common changes; they do not remove all confounding.", "",
        "## Annual-mean inference sensitivity", "",
        table(primary[primary.inference.ne("prefecture_FE_year_cluster")],["spec","inference","term","coefficient","p_two_sided","ci_low","ci_high"]), "",
        "Because the panel is balanced and regressors vary only by year, the import coefficients equal those from annual unweighted prefecture-mean regressions. This equality is checked numerically. HC3 and lag-one HAC provide different assumptions, not additional observations or exact small-sample inference. All variants are reported.", "",
        "In particular, the no-trend negative coefficient has year-cluster p = 0.0195 but annual HC3 p = 0.1448. The positive other-food coefficient in the joint model has year-cluster p = 0.0066 but annual HC3 p = 0.2619. The positive quadratic-trend total-import coefficient has annual HC3 p = 0.0151. These differences must remain visible; selecting one covariance method or trend specification to obtain significance would misrepresent the uncertainty.", "",
        "## Leave-one-year-out stability", "",table(stable,["spec","term","min","max"]), "",
        "These ranges omit each year in turn. They are coefficient stability diagnostics, not confidence intervals.", "",
        "## Provisional 2025 sensitivity", "",
        table(results[results.training_vintage.eq("through_2025_provisional") & results.inference.eq("annual_mean_HC3")],["spec","term","coefficient","p_two_sided","ci_low","ci_high"]), "",
        "## Food-group and soy-product screening", "",
        f"{len(screening)} separate log-import-plus-linear-trend regressions, each with nine annual outcomes. All results are exported, with Benjamini–Hochberg adjustment across the full family. Incomplete series are excluded, not imputed as zero. A significant screen is exploratory and does not identify a causal or regional food effect.", "",
        table(screening.sort_values("p_HC3"),["feature","coefficient","p_HC3","BH_q_value"]), "",
        "Whole soyabeans include sowing seed. Soyabean oilcake is a supplementary non-food series and is not added to food totals. Soyabeans, derivatives and food groups overlap; screening coefficients describe separate specifications, not a decomposition of a total effect.", "",
        "## Unrestricted year effects", "",
        "All import regressors have zero residual variation after year indicators (verified to tolerance 1e-10). Thus a prefecture-and-year fixed-effects model cannot estimate their main effects. Pseudoinverse output from that rank-deficient design is not reported as an identified result.", "",
        "## Reproduce", "", "```bash", "python scripts/_19_prefecture_food_regressions.py", "```", "",
        "Detailed coefficients, intervals, inference degrees of freedom, screening exclusions and source merge documentation are retained with the CSV exports and methods.json.", ""]
    (DEST/"REGRESSION_RESULTS.md").write_text("\n".join(report))
    print(primary[primary.inference.eq("annual_mean_HC3")][["spec","term","coefficient","p_two_sided","ci_low","ci_high"]].to_string(index=False))
    print(stable.to_string(index=False))
    print(screening.sort_values("p_HC3")[["feature","coefficient","p_HC3","BH_q_value"]].to_string(index=False))


if __name__=="__main__":
    main()
