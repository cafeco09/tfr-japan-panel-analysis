"""Aggregate external food imports: national regressions, ML and scenarios.

python scripts/_15_external_food_analysis.py
The World partner total is one national series, with no organic/country interaction.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import brentq
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.base import clone

from _13_ml_sensitivity_projections import grids,select,temporal_comparison,table,power,parameter_text

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"output"/"external_food_imports"
FEATURES=["log_external_food","trend"]


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    imports=pd.read_csv(ROOT/"data"/"external_food_imports_world_2016_2025.csv")
    tfr=pd.read_csv(ROOT/"data"/"national_tfr_2016_2025.csv")
    source=tfr.merge(imports,on="year",validate="one_to_one",suffixes=("_tfr","_imports")).sort_values("year").reset_index(drop=True)
    assert len(source)==10 and source.year.is_unique and source.partner_code.eq(0).all()
    source["log_external_food"]=np.log(source.external_food_import_value_current_usd)
    source["log_component_sum"]=np.log(source.category_sum_current_usd)
    source["trend"]=source.year-2016
    source["d_tfr"]=source.national_tfr.diff();source["d_log_food"]=source.log_external_food.diff()
    source["lag_log_food"]=source.log_external_food.shift()
    source.to_csv(DEST/"analysis_data.csv",index=False)
    final=source[source.year.le(2024)].reset_index(drop=True)
    formulas={"no_time_trend":"national_tfr ~ log_external_food",
              "linear_time_trend":"national_tfr ~ log_external_food + trend",
              "quadratic_time_trend":"national_tfr ~ log_external_food + trend + I(trend**2)",
              "first_differences":"d_tfr ~ d_log_food",
              "one_year_lag_linear_trend":"national_tfr ~ lag_log_food + trend",
              "component_sum_linear_trend":"national_tfr ~ log_component_sum + trend"}
    estimates=[]
    for vintage,data in [("through_2024_final",final),("through_2025_provisional_rate",source)]:
        for name,formula in formulas.items():
            variable=("d_log_food" if name=="first_differences" else "lag_log_food" if name.startswith("one_year")
                      else "log_component_sum" if name.startswith("component_sum") else "log_external_food")
            sample=data.dropna(subset=[variable,"d_tfr"] if name=="first_differences" else [variable]).copy()
            base=smf.ols(formula,sample,missing="raise").fit()
            assert np.linalg.matrix_rank(base.model.exog)==base.model.exog.shape[1]
            for covariance in ["HC3","HAC_lag1"]:
                fitted=(smf.ols(formula,sample,missing="raise").fit(cov_type="HC3",use_t=True) if covariance=="HC3"
                        else smf.ols(formula,sample,missing="raise").fit(cov_type="HAC",cov_kwds={"maxlags":1,"use_correction":True},use_t=True))
                ci=fitted.conf_int().loc[variable]
                estimates.append(dict(training_vintage=vintage,spec=name,covariance=covariance,
                                       coefficient=fitted.params[variable],se=fitted.bse[variable],p_two_sided=fitted.pvalues[variable],
                                       ci_low=ci.iloc[0],ci_high=ci.iloc[1],n=int(fitted.nobs),residual_df=int(fitted.df_resid),
                                       predicted_tfr_change_per_10pct_value=fitted.params[variable]*np.log1p(.1)))
    regressions=pd.DataFrame(estimates);regressions.to_csv(DEST/"national_regression_sensitivity.csv",index=False)
    pred,metrics,tuning=temporal_comparison(final,"OBSERVED_WORLD_FOOD",5,grids(),features=FEATURES)
    pred.to_csv(DEST/"chronological_predictions.csv",index=False)
    metrics.to_csv(DEST/"ML_model_comparison.csv",index=False)
    tuning.to_csv(DEST/"nested_tuning.csv",index=False)
    full={};parameters=[];detail=[];stability=[]
    for name,options in grids().items():
        selected,score=select(options,final[FEATURES],final.national_tfr)
        selected.fit(final[FEATURES],final.national_tfr);full[name]=selected
        parameters.append(dict(training_vintage="through_2024_final",model=name,parameters=parameter_text(selected),inner_MSE=score))
        for fraction in [-.1,-.05,-.01,.01,.05,.1]:
            changed=final[FEATURES].copy();changed.log_external_food+=np.log1p(fraction)
            supported=((changed>=final[FEATURES].min()) & (changed<=final[FEATURES].max())).all(axis=1)
            delta=selected.predict(changed)-selected.predict(final[FEATURES])
            for i in range(len(final)):
                detail.append(dict(model=name,year=int(final.year.iloc[i]),value_change_fraction=fraction,
                                   predicted_tfr_change=delta[i],within_marginal_training_ranges=bool(supported.iloc[i])))
        for omitted in range(len(final)):
            keep=np.arange(len(final))!=omitted;training=final.loc[keep]
            fitted=clone(selected).fit(training[FEATURES],training.national_tfr)
            changed=final[FEATURES].copy();changed.log_external_food+=np.log1p(.01)
            supported=((changed>=training[FEATURES].min()) & (changed<=training[FEATURES].max()) &
                       (final[FEATURES]>=training[FEATURES].min()) & (final[FEATURES]<=training[FEATURES].max())).all(axis=1)
            delta=fitted.predict(changed)-fitted.predict(final[FEATURES])
            stability.append(dict(model=name,omitted_year=int(final.year.iloc[omitted]),
                                  mean_tfr_change_per_1pct=delta[supported].mean() if supported.any() else np.nan,
                                  supported_points=int(supported.sum())))
    detail=pd.DataFrame(detail);detail.to_csv(DEST/"predictive_sensitivity_detail.csv",index=False)
    stability=pd.DataFrame(stability);stability.to_csv(DEST/"leave_year_out_sensitivity.csv",index=False)
    summaries=[]
    for (name,fraction),g in detail.groupby(["model","value_change_fraction"],sort=False):
        supported=g[g.within_marginal_training_ranges];loo=stability[stability.model.eq(name)].mean_tfr_change_per_1pct
        summaries.append(dict(model=name,value_change_fraction=fraction,mean_predicted_tfr_change=supported.predicted_tfr_change.mean(),
                              supported_points=len(supported),loo_1pct_min=loo.min(),loo_1pct_max=loo.max()))
    sensitivity=pd.DataFrame(summaries);sensitivity.to_csv(DEST/"predictive_sensitivity_summary.csv",index=False)
    fit=sm.OLS(final.national_tfr,sm.add_constant(final[FEATURES])).fit();df=int(fit.df_resid)
    critical=stats.t.ppf(.975,df);noncentrality=brentq(lambda nc:power(nc,df,critical)-.8,0,8)
    mde=pd.DataFrame([dict(noise_sd_multiplier=factor,n=len(final),residual_df=df,power=.8,alpha=.05,
                          coefficient_MDE=noncentrality*fit.bse.log_external_food*factor,
                          tfr_change_MDE_for_10pct_value=noncentrality*fit.bse.log_external_food*factor*np.log1p(.1))
                      for factor in [.5,1.,2.]])
    mde.to_csv(DEST/"conditional_detection_threshold.csv",index=False)
    anchor=source.iloc[-1];initial=source.iloc[0]
    cagr=(anchor.external_food_import_value_current_usd/initial.external_food_import_value_current_usd)**(1/9)-1
    growth={"flat_2025_nominal_value":0.,"plus_5pct_per_year":.05,"minus_5pct_per_year":-.05,"historical_2016_2025_CAGR":cagr}
    forecasts=[]
    for vintage,training in [("through_2024_final",final),("through_2025_provisional_rate",source)]:
        selected={}
        for name,options in grids().items():
            chosen,score=select(options,training[FEATURES],training.national_tfr)
            selected[name]=chosen.fit(training[FEATURES],training.national_tfr)
            if vintage!="through_2024_final":
                parameters.append(dict(training_vintage=vintage,model=name,parameters=parameter_text(chosen),inner_MSE=score))
        trend=sm.OLS(training.national_tfr,sm.add_constant(training[["trend"]])).fit()
        for scenario,annual_growth in growth.items():
            for year in range(2026,2031):
                value=anchor.external_food_import_value_current_usd*(1+annual_growth)**(year-2025)
                point=pd.DataFrame({"log_external_food":[np.log(value)],"trend":[year-2016]})
                predictions={name:float(model.predict(point)[0]) for name,model in selected.items()}
                predictions["Linear_trend_only"]=float(trend.predict(sm.add_constant(point[["trend"]],has_constant="add")).iloc[0])
                predictions["Persistence"]=float(training.national_tfr.iloc[-1])
                for name,prediction in predictions.items():
                    forecasts.append(dict(training_vintage=vintage,scenario=scenario,year=year,model=name,projected_tfr=prediction,
                                          assumed_external_food_value_current_usd=value,assumed_growth=annual_growth,
                                          imports_outside_training_range=bool(point.log_external_food.iloc[0]<training.log_external_food.min() or point.log_external_food.iloc[0]>training.log_external_food.max()),
                                          time_outside_training_range=True,interpretation="Conditional scenario, not causal or a calibrated forecast"))
    forecasts=pd.DataFrame(forecasts);forecasts.to_csv(DEST/"projections_2026_2030.csv",index=False)
    pd.DataFrame(parameters).to_csv(DEST/"final_model_parameters.csv",index=False)
    # Direct absorption check: national import values contain no within-year prefectural variation.
    year_dummies=pd.get_dummies(source.year,dtype=float).to_numpy()
    remainder=source.log_external_food.to_numpy()-year_dummies@np.linalg.lstsq(year_dummies,source.log_external_food,rcond=None)[0]
    assert np.linalg.norm(remainder)<1e-10
    metadata=dict(scope="Japan imports from World: all partner origins; food and beverages in primary and processed forms",
                  product="BEC Rev.4 category 1 = 11 + 12",reporter=392,partner=0,flow="M",
                  unit="Current USD, not food volume, price-adjusted exposure, or local consumption",
                  hypothesis="Higher total external food imports are associated with lower fertility; signs remain unconstrained",
                  origin_split=False,organic_interaction=False,primary_n=9,primary_years="2016–2024",
                  provisional_rate_sensitivity_years="2016–2025",chronological_validation_years=[2021,2022,2023,2024],
                  future_years=list(range(2026,2031)),future_value_scenarios=growth,
                  synthetic_data="Existing two-origin simulations are historical method tests; none are pooled or relabelled as observed World totals",
                  unresolved="National common shocks, endogeneity, nominal price/currency effects, nine observations, model/scenario uncertainty")
    metadata["source_aggregation_discrepancies"]=imports.loc[~imports.components_reconcile,["year","aggregation_gap_usd","aggregation_gap_fraction"]].to_dict("records")
    (DEST/"scope_and_methods.json").write_text(json.dumps(metadata,indent=2)+"\n")
    primary=regressions[(regressions.training_vintage=="through_2024_final")&regressions.covariance.eq("HC3")]
    provisional=regressions[(regressions.training_vintage=="through_2025_provisional_rate")&regressions.covariance.eq("HC3")]
    flat=forecasts[(forecasts.training_vintage=="through_2025_provisional_rate")&forecasts.scenario.eq("flat_2025_nominal_value")]
    report=["# Total external food imports: updated analysis", "",
            "Current question: Japan's total food imports from all origins as one external-import variable. No country split or organic interaction is included.",
            "", "## Data definition", "",
            "Use Japan-reported imports with World partner code 0, BEC Rev.4 category 1 (food and beverages), including primary and processed categories. This source aggregate covers all partners directly. It is not China + USA, and individual country totals are not added on top of the World total. Standard reported imports are used; this is not a separately constructed net-import or domestic-food-consumption measure.",
            "", "Values are current USD, not physical volumes. Aggregate weights are unavailable and are not read as zero. The primary outcome sample uses official national TFR for 2016–2024 (nine observations); the provisional 2025 rate is a separate sensitivity. The broader origin scope does not add independent annual observations. Existing two-origin synthetic panels are not relabelled as World data.",
            "", "Source quality: some published category-1 totals do not exactly equal categories 11 + 12. Gaps and reconciliation flags are retained in the data, and a component-sum linear-trend sensitivity is included below. The published World category-1 total remains the main measure; values are not silently altered to force additivity. See scope_and_methods.json for affected years and amounts.",
            "", "## National regression results", "",
            "Hypothesis: a negative association. Coefficients are unconstrained. The primary results use HC3 SE with a t reference distribution; HAC lag-one sensitivity is exported. Neither covariance method solves confounding or provides exact inference in this small sample. Positive or non-significant coefficients cannot be reported as support for the negative hypothesis.", "",
            table(primary,["spec","coefficient","se","p_two_sided","ci_low","ci_high","n"]),
            "", "Inference-method sensitivity: the no-trend negative association has lag-one HAC p = 0.017 versus HC3 p = 0.127. Its direction changes after adding the linear trend (HC3 p = 0.275; HAC p = 0.113). The quadratic-trend HAC result is positive with p = 0.044. These small-sample, model-dependent significance differences are not consistent evidence for a negative causal effect. All covariance variants are retained in the CSV rather than selecting a preferred p-value.",
            "", "Including provisional 2025:", "",table(provisional,["spec","coefficient","p_two_sided","n"]),
            "", "A log-level coefficient gives TFR units per log-point higher nominal import value. The first-difference model relates annual changes; the lag model changes the timing. These are associations under different time-pattern restrictions, not interchangeable causal estimates. Annual fixed effects absorb the national main effect entirely.",
            "", "## ML comparison", "",
            "Four chronological outcomes (2021–2024), initially trained on five past years. Hyperparameter tuning and scaling use only training data. Contemporary import values are supplied for held-out years, so the evaluation is conditional hindcasting rather than advance prediction of unknown imports. All candidates are shown; four errors cannot establish a reliable winner.", "",
            table(metrics.sort_values("MAE"),["model","validation_n","MAE","RMSE"]),
            "", "## Predictive sensitivity", "",
            "A +1% nominal import-value perturbation, holding time fixed, is recomputed for every in-range point. The means below are responses of fitted models, not causal derivatives or significance tests. Leave-year-out ranges use fixed selected parameters and varying supported points; they are not confidence intervals. All ±1%, ±5%, ±10% perturbations and support flags are exported.", "",
            table(sensitivity[np.isclose(sensitivity.value_change_fraction,.01)],["model","mean_predicted_tfr_change","supported_points","loo_1pct_min","loo_1pct_max"]),
            "", "## 2026–2030 projections", "",
            "Future import values are explicit scenarios: flat 2025 values, ±5% annually, or historical 2016–2025 nominal-value CAGR. Separate fits exclude/include provisional 2025 TFR. These are conditional extrapolations, not official forecasts or confidence intervals. Model spread does not quantify all uncertainty; trees and RBF SVR are particularly limited when extrapolating time.",
            "", "Flat 2025 import values, provisional 2025 rate included:", "",
            table(flat.pivot(index="year",columns="model",values="projected_tfr").reset_index(),["year","OLS_imports_and_trend","Ridge","ElasticNet","Linear_trend_only","SVR_RBF","RandomForest_shallow"]),
            "", "## Detection limit", "",
            "Conditional iid Gaussian linear-model calculation: 80% power at two-sided alpha 0.05. Noise is estimated from this small sample and varied from half to twice that estimate. These are assumed-design thresholds, not empirical power guarantees or a remedy for endogeneity.", "",
            table(mde,["noise_sd_multiplier","coefficient_MDE","tfr_change_MDE_for_10pct_value"]),
            "", "## Interpretation limits", "",
            "The scope now matches all-origin external food imports. This does not remove national demand shocks, reverse causality, food-price movements, exchange-rate changes or common fertility trends. More source countries do not create more annual treatment shocks after aggregation. Previous country coefficients and projections are superseded for this aggregate question; historical outputs are retained for traceability. No synthetic records are used to increase empirical n.",
            "", "## Reproduce", "", "```bash", "python scripts/_14_external_food_imports.py", "python scripts/_15_external_food_analysis.py", "```", "",
            "## Sources", "", "- World import selection: https://uncomtrade.org/docs/how-to-retrieve-data-for-world-exports-to-a-country-in-un-comtrade/",
            "- Raw Comtrade URLs and retrieval dates: data/external_food_sources/.",
            "- National TFR provenance: data/national_tfr_2016_2025.csv and its archived MHLW workbook.", ""]
    (DEST/"EXTERNAL_FOOD_IMPORT_RESULTS.md").write_text("\n".join(report))
    print(primary[["spec","coefficient","p_two_sided","n"]].to_string(index=False))
    print(metrics.sort_values("MAE").to_string(index=False))
    print(flat[flat.model.isin(["OLS_imports_and_trend","Ridge","ElasticNet","Linear_trend_only"])].pivot(index="year",columns="model",values="projected_tfr").to_string())


if __name__=="__main__":
    main()
