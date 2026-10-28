"""TFR outcome, food-import predictors, prefecture/time/socioeconomic controls."""
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from _13_ml_sensitivity_projections import table

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"output/controlled_food_regressions"


def wild_cluster_p(fit, years, term):
    """Enumerated restricted Rademacher bootstrap, studentised with CR1 SEs.

    This is a small-cluster diagnostic, not an exact randomisation test.
    """
    X=fit.model.exog;y=fit.model.endog;idx=fit.model.exog_names.index(term)
    restricted=np.delete(X,idx,axis=1)
    fitted=restricted@np.linalg.lstsq(restricted,y,rcond=None)[0]
    errors=y-fitted
    pinv=np.linalg.pinv(X);weights=pinv[idx]
    unique,inverse=np.unique(years,return_inverse=True);g=len(unique);n,k=X.shape
    correction=g/(g-1)*(n-1)/(n-k)
    signs=np.array(list(itertools.product([-1.,1.],repeat=g)))
    outcomes=fitted[:,None]+errors[:,None]*signs[:,inverse].T
    betas=pinv@outcomes;residual=outcomes-X@betas
    scores=np.stack([(weights[inverse==j,None]*residual[inverse==j]).sum(axis=0) for j in range(g)])
    ses=np.sqrt(correction*(scores**2).sum(axis=0))
    observed=float(fit.params[term]/fit.bse[term])
    stats=betas[idx]/ses
    assert np.isfinite(stats).all()
    # Check the same score calculation on the observed fit before using it.
    observed_scores=np.array([np.dot(weights[inverse==j],fit.resid[inverse==j]) for j in range(g)])
    assert np.isclose(np.sqrt(correction*np.sum(observed_scores**2)),fit.bse[term],rtol=1e-7)
    return float(np.mean(np.abs(stats)>=abs(observed)-1e-9)),len(signs)


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    panel=pd.read_csv(ROOT/"output/tfr_merged/prefecture_food_imports_and_tfr_2016_2025.csv")
    history=pd.read_csv(ROOT/"data/dated_source_panel_2016_2025.csv")
    controls=["observed_income_jpy_per_resident","income_fiscal_year","income_release_vintage","income_source","income_source_cell","income_measure_note",
              "eating_out_jpy_per_household","eating_out_source","eating_out_source_cell","eating_out_source_city","eating_out_release_status"]
    assert not history.duplicated(["region_code","year"]).any()
    panel=panel.merge(history[["region_code","year"]+controls],on=["region_code","year"],how="left",validate="one_to_one",indicator=True)
    assert panel._merge.eq("both").all()
    panel=panel.drop(columns="_merge")
    for name,col in [("log_food","published_food_usd"),("log_soyabeans","whole_soyabeans_usd"),
                     ("log_other_food","other_mapped_food_usd"),("log_income","observed_income_jpy_per_resident"),
                     ("log_eating_out","eating_out_jpy_per_household")]:
        panel[name]=np.log(panel[col].where(panel[col].gt(0)))
    panel["trend"]=panel.year-2016
    panel["trend_squared"]=panel.trend**2
    panel["complete_controls"]=panel[["log_income","log_eating_out"]].notna().all(axis=1)
    coverage=panel.groupby("year").agg(prefectures=("region_code","size"),observed_income=("log_income","count"),
                                       observed_eating_out=("log_eating_out","count"),complete_rows=("complete_controls","sum")).reset_index()
    coverage.to_csv(DEST/"control_coverage.csv",index=False)
    complete_years=coverage.loc[coverage.complete_rows.eq(47)&coverage.year.le(2024),"year"]
    primary=panel[panel.year.isin(complete_years)].copy()
    extended=panel[panel.complete_controls&panel.year.le(2024)].copy()
    assert set(primary.year)==set(range(2016,2023)) and len(primary)==329 and len(extended)==371
    primary.to_csv(DEST/"balanced_analysis_data.csv",index=False)
    extended.to_csv(DEST/"extended_complete_case_data.csv",index=False)
    specifications={
        "total_prefecture_trend":["log_food","trend"],
        "total_plus_income":["log_food","trend","log_income"],
        "total_full_controls":["log_food","trend","log_income","log_eating_out"],
        "total_full_controls_quadratic":["log_food","trend","trend_squared","log_income","log_eating_out"],
        "soy_other_prefecture_trend":["log_soyabeans","log_other_food","trend"],
        "soy_other_full_controls":["log_soyabeans","log_other_food","trend","log_income","log_eating_out"],
    }
    results=[];diagnostics=[];stability=[]
    for sample,data in [("balanced_2016_2022",primary),("unbalanced_complete_2016_2023",extended)]:
        for spec,terms in specifications.items():
            if sample.startswith("unbalanced") and spec not in ["total_full_controls","soy_other_full_controls"]:
                continue
            formula="tfr_children_per_woman ~ "+" + ".join(terms)+" + C(region_code)"
            fit=smf.ols(formula,data,missing="raise").fit(cov_type="cluster",cov_kwds={"groups":data.year,"use_correction":True,"df_correction":True},use_t=True)
            assert np.linalg.matrix_rank(fit.model.exog)==fit.model.exog.shape[1]
            diagnostics.append(dict(sample=sample,spec=spec,formula=formula,rows=len(data),prefectures=data.region_code.nunique(),
                                    annual_clusters=data.year.nunique(),cluster_t_df=fit.df_resid_inference,
                                    in_sample_R2=fit.rsquared,design_condition_number=fit.condition_number))
            for term in terms:
                ci=fit.conf_int().loc[term]
                is_import=term in ["log_food","log_soyabeans","log_other_food"]
                boot,reps=wild_cluster_p(fit,data.year.to_numpy(),term) if is_import else (np.nan,0)
                results.append(dict(sample=sample,spec=spec,term=term,role="import predictor" if is_import else "control",
                                    coefficient=fit.params[term],year_cluster_se=fit.bse[term],year_cluster_p=fit.pvalues[term],
                                    ci_low=ci.iloc[0],ci_high=ci.iloc[1],wild_cluster_p=boot,wild_sign_patterns=reps,
                                    tfr_change_for_10pct=fit.params[term]*np.log1p(.1) if term.startswith("log_") else np.nan,
                                    panel_rows=len(data),annual_clusters=data.year.nunique(),inference_t_df=fit.df_resid_inference))
            if sample.startswith("balanced") and spec in ["total_full_controls","soy_other_full_controls"]:
                for year in sorted(data.year.unique()):
                    subset=data[data.year.ne(year)]
                    loo=smf.ols(formula,subset).fit()
                    for term in [t for t in terms if t in ["log_food","log_soyabeans","log_other_food"]]:
                        stability.append(dict(spec=spec,term=term,omitted_year=year,coefficient=loo.params[term]))
    results=pd.DataFrame(results);diagnostics=pd.DataFrame(diagnostics);stability=pd.DataFrame(stability)
    results.to_csv(DEST/"regression_coefficients.csv",index=False)
    diagnostics.to_csv(DEST/"model_diagnostics.csv",index=False)
    stability.to_csv(DEST/"leave_year_out_import_coefficients.csv",index=False)
    methods=dict(dependent_variable="Prefectural TFR",main_predictors="log total all-origin food imports; alternative joint log whole soyabeans and log other mapped food",
                 controls="Prefecture indicators, common time trend, log prefectural income per resident, log capital-city eating-out expenditure; quadratic trend sensitivity",
                 primary_sample="47 prefectures × 2016–2022 = 329; matched sample for all control comparisons",
                 extended_sample="371 complete cases, 2016–2023; five prefectures missing income in 2023; no imputation",
                 income_definition="Observed nominal prefectural income per resident, not household disposable income; fiscal year matched to calendar-year label; source vintage retained",
                 eating_out_definition="Capital-city household survey expenditure proxy, nominal JPY; not a prefecture-wide food quantity or import exposure measure",
                 inference="Year clusters: seven primary clusters, t df 6; extended eight clusters, t df 7. Restricted Rademacher wild cluster bootstrap enumerates all 128/256 sign patterns with CR1 studentisation.",
                 bootstrap_limit="Approximate residual-bootstrap diagnostic using fitted null nuisance parameters; not an exact randomisation test. Assumes independent year clusters and appropriate error symmetry; temporal dependence remains unresolved.",
                 causal_limit="Income and eating-out are not assumed exogenous; eating-out may be a mediator or collider. Controls do not identify a causal effect. Imports are national current USD, not local exposure. Unrestricted year indicators absorb their main effects.",
                 excluded="Provisional 2025 and 2024 lack observed income; organic/gardening measures are single-year snapshots and are not filled across years. National population is not a local population control.")
    (DEST/"methods.json").write_text(json.dumps(methods,indent=2)+"\n")
    imports=results[results.role.eq("import predictor")]
    stable=stability.groupby(["spec","term"]).coefficient.agg(["min","max"]).reset_index()
    report=["# Food imports as predictors of prefectural TFR, with controls", "",
        "The balanced fully controlled model estimates a total-food coefficient of −0.0503 (year-cluster p = 0.6647; restricted wild-cluster p = 0.7344). In the joint model, soyabeans are negative (−0.0872): conventional year-cluster p = 0.0146, but wild-cluster p = 0.1875. The extended incomplete 2023 panel gives a stronger soyabean result (−0.0960; wild p = 0.0234), while the total-food coefficient changes sign. The negative soyabean association is sensitive to sample and inference; it is not a demonstrated causal effect.", "",
        "Dependent variable: prefectural TFR. Main independent variable: log national food imports from all origins. Prefecture indicators are categorical control variables. Controls also include a common time trend, log observed prefectural income per resident and log capital-city eating-out expenditure. A separate specification splits whole soyabeans and other mapped food without double counting.", "",
        "```text", "TFR_it = prefecture intercept_i + beta log(food imports_t)", "         + gamma log(income_it) + delta log(eating-out proxy_it)", "         + common time trend_t + error_it", "```", "",
        "## Matched balanced sample", "",
        "All controlled comparisons use the same 329 observations: 47 prefectures × 2016–2022. Income is complete through 2022; 2023 has only 42 observed prefectural incomes, and 2024–2025 have none. Missing income is not imputed. Using a shared sample separates the effect of adding controls from changing the sample years.", "",
        table(imports[imports['sample'].eq("balanced_2016_2022")],["spec","term","coefficient","year_cluster_p","wild_cluster_p","ci_low","ci_high","tfr_change_for_10pct"]), "",
        "Year-cluster inference uses six t degrees of freedom, not 329 independent import observations. Restricted wild cluster bootstrap p-values enumerate all 128 year-sign patterns; they are approximate diagnostics under independent cluster and error-symmetry assumptions, not exact significance guarantees. Neither approach handles arbitrary dependence across years.", "",
        "## Control coefficients", "",
        table(results[results['sample'].eq("balanced_2016_2022")&results.spec.isin(["total_full_controls","soy_other_full_controls"])&results.role.eq("control")],["spec","term","coefficient","year_cluster_p","ci_low","ci_high"]), "",
        "Income is a broad nominal prefectural income measure per resident, not disposable household income. Its fiscal year is matched to the calendar-year label. Eating-out spending is measured in the prefectural capital's household survey and is used as a proxy; it is not measured prefecture-wide consumption. Both may be endogenous; including them is an association sensitivity, not automatic causal adjustment.", "",
        "## Extended complete-case sensitivity", "",
        "The unbalanced 2016–2023 sensitivity includes 371 records and eight year clusters. It adds 42 prefectures in 2023; the five missing incomes remain excluded. All 256 bootstrap sign patterns are evaluated.", "",
        table(imports[imports['sample'].eq("unbalanced_complete_2016_2023")],["spec","term","coefficient","year_cluster_p","wild_cluster_p","ci_low","ci_high"]), "",
        "## Leave-one-year-out stability", "",table(stable,["spec","term","min","max"]), "",
        "These ranges are diagnostics, not confidence intervals. Import values are identical across prefectures within each year. Unrestricted year fixed effects would absorb all import main effects, even with these additional controls. A time trend imposes a common path rather than removing all shared national shocks.", "",
        "Organic-farming and gardening snapshots are not copied across years as controls. No synthetic observations, arbitrary allocation of national imports, or numerical encoding of prefecture labels is used.", "",
        "## Reproduce", "", "```bash", "python scripts/_21_controlled_food_regressions.py", "```", "",
        "Analysis CSVs retain control source URLs, source cells, release vintage and capital-city names. Food and TFR provenance remain in the merged source data.", ""]
    (DEST/"CONTROLLED_REGRESSION_RESULTS.md").write_text("\n".join(report))
    print(imports[["sample","spec","term","coefficient","year_cluster_p","wild_cluster_p"]].to_string(index=False))
    print(stable.to_string(index=False))


if __name__=="__main__":
    main()
