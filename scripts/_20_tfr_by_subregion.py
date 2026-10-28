"""TFR as outcome; prefectures as categorical independent variables."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

from _13_ml_sensitivity_projections import table

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"output/tfr_by_subregion"


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    source=pd.read_csv(ROOT/"output/tfr_merged/prefecture_food_imports_and_tfr_2016_2025.csv")
    final=source[source.year.le(2024)].copy()
    assert len(final)==423 and not final.duplicated(["region_code","year"]).any()
    names=source[["region_code","prefecture"]].drop_duplicates().set_index("region_code").prefecture.to_dict()
    region='C(region_code, Treatment(reference="JP-01"))'
    specifications={"prefectures_only":region,"years_only":"C(year)","prefectures_and_years":region+" + C(year)"}
    comparisons=[];coefficients=[];contrasts=[];summary=[]
    for vintage,data in [("through_2024_final",final),("through_2025_provisional",source)]:
        assert data.groupby("year").region_code.nunique().eq(47).all()
        fits={}
        for name,rhs in specifications.items():
            fit=smf.ols("tfr_children_per_woman ~ "+rhs,data,missing="raise").fit(
                cov_type="cluster",cov_kwds={"groups":data.year,"use_correction":True,"df_correction":True},use_t=True)
            assert np.linalg.matrix_rank(fit.model.exog)==fit.model.exog.shape[1]
            fits[name]=fit
            comparisons.append(dict(training_vintage=vintage,spec=name,outcome="tfr_children_per_woman",formula=fit.model.formula,
                                    panel_rows=len(data),prefectures=47,annual_years=data.year.nunique(),
                                    r_squared=fit.rsquared,adjusted_r_squared=fit.rsquared_adj,
                                    in_sample_RMSE=float(np.sqrt(np.mean(fit.resid**2))),
                                    interpretation="In-sample descriptive fit; not out-of-sample performance or causal explanation"))
            ci=fit.conf_int()
            for term in fit.params.index:
                coefficients.append(dict(training_vintage=vintage,spec=name,term=term,
                                          coefficient=fit.params[term],year_cluster_se=fit.bse[term],
                                          year_cluster_p=fit.pvalues[term],ci_low=ci.loc[term,0],ci_high=ci.loc[term,1],
                                          inference_t_df=float(fit.df_resid_inference)))
        pivot=data.pivot(index="year",columns="region_code",values="tfr_children_per_woman")
        for code in sorted(names):
            values=pivot[code];diff=values-pivot["JP-01"]
            row=dict(training_vintage=vintage,region_code=code,prefecture=names[code],years=len(values),
                     mean_tfr=values.mean(),min_tfr=values.min(),max_tfr=values.max(),
                     difference_from_Hokkaido=diff.mean())
            if code!="JP-01":
                term=region+"[T."+code+"]"
                assert np.isclose(fits["prefectures_only"].params[term],diff.mean(),atol=1e-10)
                assert np.isclose(fits["prefectures_and_years"].params[term],diff.mean(),atol=1e-10)
                # Each year's paired regional contrast is one observation, not 47.
                frame=pd.DataFrame({"difference":diff.to_numpy()})
                for method,kwargs in [("HC3",{}),("HAC_lag1",{"maxlags":1,"use_correction":True})]:
                    fit=smf.ols("difference ~ 1",frame).fit(cov_type="HC3" if method=="HC3" else "HAC",cov_kwds=kwargs,use_t=True)
                    ci=fit.conf_int().loc["Intercept"]
                    contrasts.append(dict(training_vintage=vintage,region_code=code,prefecture=names[code],reference="Hokkaido",
                                          method=method,annual_observations=len(frame),coefficient=fit.params.Intercept,
                                          se=fit.bse.Intercept,p_two_sided=fit.pvalues.Intercept,
                                          ci_low=ci.iloc[0],ci_high=ci.iloc[1],
                                          inference_t_df=float(fit.df_resid)))
                omitted=[diff.drop(year).mean() for year in diff.index]
                row.update(leave_year_out_difference_min=min(omitted),leave_year_out_difference_max=max(omitted))
            summary.append(row)
    comparisons=pd.DataFrame(comparisons);coefficients=pd.DataFrame(coefficients)
    contrasts=pd.DataFrame(contrasts);summary=pd.DataFrame(summary)
    for _,indexes in contrasts.groupby(["training_vintage","method"]).groups.items():
        contrasts.loc[indexes,"BH_q_value"]=multipletests(contrasts.loc[indexes,"p_two_sided"],method="fdr_bh")[1]
    comparisons.to_csv(DEST/"model_comparison.csv",index=False)
    coefficients.to_csv(DEST/"all_model_coefficients.csv",index=False)
    contrasts.to_csv(DEST/"prefecture_contrasts_vs_Hokkaido.csv",index=False)
    summary.to_csv(DEST/"prefecture_summary.csv",index=False)
    methods=dict(dependent_variable="tfr_children_per_woman",independent_variables="Prefecture indicators; year indicators in adjusted specification",
                 prefectures_are_categorical=True,reference_prefecture="JP-01 Hokkaido",reference_year=2016,
                 primary_years="2016–2024",primary_rows=423,provisional_sensitivity="2016–2025, 470 rows",
                 inference="OLS with year-clustered SE and finite-sample corrections; additionally annual paired regional contrasts with HC3 and lag-one HAC, t references; 46 comparisons BH-adjusted separately within vintage and method",
                 limitations="Few years; temporal dependence and differential regional trends remain. Region labels measure descriptive differences, not manipulable causal effects. No omnibus cluster Wald test for 46 region coefficients is interpreted with only nine year clusters.",
                 import_variables="Not included in these region-predictor models. Existing import regressions also used TFR as outcome and prefecture indicators as covariates; unrestricted year effects absorb national import main effects.")
    (DEST/"methods.json").write_text(json.dumps(methods,indent=2)+"\n")
    primary=comparisons[comparisons.training_vintage.eq("through_2024_final")]
    s=summary[summary.training_vintage.eq("through_2024_final")].sort_values("mean_tfr")
    examples=pd.concat([s.head(3),s.tail(3)])
    report=["# TFR explained by subregional indicators", "",
        "Dependent variable: prefectural TFR, in children per woman. Independent variables: prefecture categories, entered as 46 indicators plus an intercept. Region codes are labels, not a numerical scale. Hokkaido is the reference category.", "",
        "Primary sample: 47 prefectures, 2016–2024, 423 records. A separate sensitivity adds provisional 2025. Each prefecture has an observed rate in each year; no TFR is imputed.", "",
        "## Models", "", "```text", "TFR = intercept + prefecture indicators + error", "TFR = intercept + prefecture indicators + year indicators + error", "```", "",
        "A years-only model is also exported as a descriptive benchmark. These regressions do not include food imports. The earlier import regressions already had TFR on the left-hand side and prefecture fixed effects on the right-hand side; this run isolates the regional predictors explicitly.", "",
        table(primary,["spec","panel_rows","r_squared","adjusted_r_squared","in_sample_RMSE"]), "",
        "R-squared is descriptive in-sample fit; it is not a causal contribution or held-out predictive accuracy. With a balanced panel, adding common year effects leaves the prefecture differences unchanged, while accounting for the common annual TFR pattern.", "",
        "## Lowest and highest average TFR", "",table(examples,["prefecture","mean_tfr","difference_from_Hokkaido"]), "",
        "The region-only intercept is Hokkaido's average TFR. Each region coefficient is that prefecture's average difference from Hokkaido. In the region-plus-year model, the intercept is the fitted Hokkaido value at the reference year 2016; year coefficients are common changes relative to 2016. No rank ordering of numerical region codes is used.", "",
        "## Inference and exports", "",
        "all_model_coefficients.csv includes the region and year coefficients with year-clustered standard errors. Nine primary year clusters are few. No joint cluster Wald test over all 46 regional indicators is interpreted because the covariance has insufficient rank for that test.", "",
        "prefecture_contrasts_vs_Hokkaido.csv treats each year's paired TFR difference as one annual observation and reports HC3 and lag-one HAC sensitivity, with BH adjustment across the 46 contrasts within each method and sample vintage. Both inference methods have assumptions that nine years cannot validate. These comparisons describe persistent differences; they do not establish causal effects of living in a prefecture.", "",
        "prefecture_summary.csv includes all 47 regions, mean/minimum/maximum TFR, and leave-year-out contrast ranges. A range is a stability diagnostic, not a confidence interval.", "",
        "## Reproduce", "", "```bash", "python scripts/_20_tfr_by_subregion.py", "```", ""]
    (DEST/"TFR_SUBREGION_RESULTS.md").write_text("\n".join(report))
    print(primary.to_string(index=False));print(examples[["prefecture","mean_tfr","difference_from_Hokkaido"]].to_string(index=False))


if __name__=="__main__":
    main()
