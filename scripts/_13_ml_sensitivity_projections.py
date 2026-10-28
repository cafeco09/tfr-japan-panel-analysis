"""Chronological ML comparison, predictive sensitivity and scenario projections.

python scripts/_13_ml_sensitivity_projections.py
Observed national data and synthetic benchmarks remain separate. No causal ML claim.
"""
import json
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.integrate import quad
from scipy.optimize import brentq
import statsmodels.api as sm
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import ElasticNet, LinearRegression, Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVR

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"output"/"ml_food_imports"
FEATURES=["log_china_food","log_usa_food","trend"]
SEED=20261028


def grids():
    return {
        "OLS_imports_and_trend":[make_pipeline(StandardScaler(),LinearRegression())],
        "Ridge":[make_pipeline(StandardScaler(),Ridge(alpha=a)) for a in [.01,.1,1.,10.]],
        "ElasticNet":[make_pipeline(StandardScaler(),ElasticNet(alpha=a,l1_ratio=r,max_iter=100000,tol=1e-8))
                      for a in [.0001,.001,.01] for r in [.2,.8]],
        "SVR_RBF":[make_pipeline(StandardScaler(),SVR(C=c,epsilon=e,gamma="scale"))
                   for c in [.03,.1,.3] for e in [.005,.02]],
        "RandomForest_shallow":[RandomForestRegressor(n_estimators=100,max_depth=depth,min_samples_leaf=2,
                                                       random_state=SEED,n_jobs=1) for depth in [1,2]],
    }


def parameter_text(model):
    if hasattr(model,"steps"):
        end=model.steps[-1][1]
    else:
        end=model
    parameters=end.get_params()
    keep=["alpha","l1_ratio","C","epsilon","gamma","max_depth","min_samples_leaf","n_estimators"]
    return json.dumps({k:parameters[k] for k in keep if k in parameters},sort_keys=True)


def select(candidates,x,y):
    if len(candidates)==1:
        return clone(candidates[0]),np.nan
    scores=[]
    # At least three past outcomes before an inner one-step validation observation.
    for candidate in candidates:
        errors=[]
        for j in range(3,len(x)):
            fitted=clone(candidate).fit(x.iloc[:j],y.iloc[:j])
            prediction=float(fitted.predict(x.iloc[[j]])[0])
            errors.append((prediction-float(y.iloc[j]))**2)
        scores.append(float(np.mean(errors)))
    best=int(np.argmin(scores))
    return clone(candidates[best]),scores[best]


def temporal_comparison(frame,label,initial,models,tune=True):
    predictions=[];traces=[]
    x=frame[FEATURES];y=frame.national_tfr
    for j in range(initial,len(frame)):
        train_x=x.iloc[:j];train_y=y.iloc[:j];test_x=x.iloc[[j]]
        assert frame.year.iloc[:j].max()<frame.year.iloc[j]
        trend=LinearRegression().fit(train_x[["trend"]],train_y)
        baseline={"Persistence":float(train_y.iloc[-1]),"Linear_trend_only":float(trend.predict(test_x[["trend"]])[0])}
        for name,prediction in baseline.items():
            predictions.append(dict(dataset=label,year=int(frame.year.iloc[j]),model=name,
                                    actual=float(y.iloc[j]),predicted=prediction,error=prediction-float(y.iloc[j]),
                                    train_start=int(frame.year.iloc[0]),train_end=int(frame.year.iloc[j-1]),train_n=j))
        for name,candidates in models.items():
            chosen,inner=select(candidates,train_x,train_y) if tune else (clone(candidates[0]),np.nan)
            chosen.fit(train_x,train_y)
            prediction=float(chosen.predict(test_x)[0])
            predictions.append(dict(dataset=label,year=int(frame.year.iloc[j]),model=name,
                                    actual=float(y.iloc[j]),predicted=prediction,error=prediction-float(y.iloc[j]),
                                    train_start=int(frame.year.iloc[0]),train_end=int(frame.year.iloc[j-1]),train_n=j))
            traces.append(dict(dataset=label,test_year=int(frame.year.iloc[j]),model=name,
                               inner_validation_mse=inner,parameters=parameter_text(chosen),
                               latest_training_year=int(frame.year.iloc[j-1]),training_n=j))
    pred=pd.DataFrame(predictions)
    metrics=[]
    for name,g in pred.groupby("model",sort=False):
        metrics.append(dict(dataset=label,model=name,validation_n=len(g),MAE=abs(g.error).mean(),
                            RMSE=np.sqrt(np.mean(g.error**2)),max_absolute_error=abs(g.error).max()))
    return pred,pd.DataFrame(metrics),pd.DataFrame(traces)


def sensitivity(model,x):
    base=model.predict(x)
    rows=[]
    for country,col in [("China","log_china_food"),("USA","log_usa_food")]:
        for change in [-.1,-.05,-.01,.01,.05,.1]:
            perturbed=x.copy();perturbed[col]+=np.log1p(change)
            within=((perturbed>=x.min()) & (perturbed<=x.max())).all(axis=1)
            delta=model.predict(perturbed)-base
            for i,(shift,supported) in enumerate(zip(delta,within)):
                rows.append(dict(country=country,import_value_change_fraction=change,observation=i,
                                 predicted_tfr_change=float(shift),within_marginal_training_ranges=bool(supported)))
    return rows


def power(ncp,df,critical):
    left=stats.nct.cdf(-critical,df,ncp)
    right=stats.nct.sf(critical,df,ncp)
    if np.isfinite(left+right):
        return float(left+right)
    # Direct chi-square mixture integration avoids rare extreme-tail nct numerical failures.
    return quad(lambda v:(stats.norm.cdf(ncp-critical*np.sqrt(v/df))+
                           stats.norm.cdf(-ncp-critical*np.sqrt(v/df)))*stats.chi2.pdf(v,df),
                0,np.inf,epsabs=1e-10)[0]


def detection_threshold(data):
    fit=sm.OLS(data.national_tfr,sm.add_constant(data[FEATURES])).fit()
    df=int(fit.df_resid);critical=stats.t.ppf(.975,df)
    delta=brentq(lambda value:power(value,df,critical)-.8,0,8,xtol=1e-12)
    rows=[];powers=[]
    for country,col in [("China","log_china_food"),("USA","log_usa_food")]:
        for multiplier in [.5,1.,2.]:
            threshold=delta*fit.bse[col]*multiplier
            rows.append(dict(country=country,noise_sd_multiplier=multiplier,n=len(data),residual_df=df,
                             target_power=.8,two_sided_alpha=.05,required_noncentrality=delta,
                             coefficient_MDE=threshold,tfr_change_MDE_for_10pct_value_change=threshold*np.log(1.1)))
        for effect in [.005,.01,.02,.05]:
            beta=effect/np.log(1.1)
            powers.append(dict(country=country,assumed_tfr_change_per_10pct_value_change=effect,
                               conditional_power=power(beta/fit.bse[col],df,critical)))
    return pd.DataFrame(rows),pd.DataFrame(powers)


def table(frame,columns):
    f=frame[columns].copy()
    for col in f.select_dtypes(include="number"):
        f[col]=f[col].map(lambda x:f"{x:.5f}" if pd.notna(x) else "—")
    return "| "+" | ".join(columns)+" |\n|"+"|".join(["---"]*len(columns))+"|\n"+"\n".join(
        "| "+" | ".join(map(str,r))+" |" for r in f.itertuples(index=False,name=None))


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    source=pd.read_csv(ROOT/"output"/"food_import_results"/"analysis_data.csv").sort_values("year").reset_index(drop=True)
    data=source[source.year.le(2024)].reset_index(drop=True)
    assert len(data)==9 and data.year.is_unique
    candidates=grids()
    pred,metrics,trace=temporal_comparison(data,"OBSERVED_2016_2024",5,candidates)
    pred.to_csv(DEST/"observed_chronological_predictions.csv",index=False)
    metrics.to_csv(DEST/"observed_model_comparison.csv",index=False)
    trace.to_csv(DEST/"observed_nested_tuning.csv",index=False)
    x=data[FEATURES];y=data.national_tfr
    fitted={};full_parameters=[]
    sensitivities=[];stability=[]
    for name,options in candidates.items():
        chosen,score=select(options,x,y)
        full_parameters.append(dict(training_vintage="through_2024_final",model=name,parameters=parameter_text(chosen),inner_MSE=score))
        fitted[name]=chosen.fit(x,y)
        for row in sensitivity(chosen,x):
            sensitivities.append(dict(model=name,year=int(data.year.iloc[row["observation"]]),**row))
        # Diagnostic only: re-estimate with one year omitted, keeping the selected parameters fixed.
        for omitted in range(len(data)):
            keep=np.arange(len(data))!=omitted
            fit=clone(chosen).fit(x.loc[keep],y.loc[keep])
            for country,col in [("China","log_china_food"),("USA","log_usa_food")]:
                perturbed=x.copy();perturbed[col]+=np.log1p(.01)
                supported=((perturbed>=x.loc[keep].min()) & (perturbed<=x.loc[keep].max()) &
                           (x>=x.loc[keep].min()) & (x<=x.loc[keep].max())).all(axis=1)
                delta=fit.predict(perturbed)-fit.predict(x)
                stability.append(dict(model=name,omitted_year=int(data.year.iloc[omitted]),country=country,
                                      mean_predicted_tfr_change_for_1pct=float(delta[supported].mean()) if supported.any() else np.nan,
                                      supported_points=int(supported.sum())))
    detail=pd.DataFrame(sensitivities);detail.to_csv(DEST/"observed_predictive_sensitivity_detail.csv",index=False)
    stable=pd.DataFrame(stability);stable.to_csv(DEST/"observed_sensitivity_leave_one_year_out.csv",index=False)
    summaries=[]
    for (name,country,change),g in detail.groupby(["model","country","import_value_change_fraction"],sort=False):
        eligible=g[g.within_marginal_training_ranges]
        loo=stable[(stable.model==name)&(stable.country==country)].mean_predicted_tfr_change_for_1pct
        summaries.append(dict(model=name,country=country,import_value_change_fraction=change,
                              mean_predicted_tfr_change=eligible.predicted_tfr_change.mean(),
                              supported_points=len(eligible),total_points=len(g),
                              leave_year_out_1pct_min=loo.min(),leave_year_out_1pct_max=loo.max()))
    sensitivity_summary=pd.DataFrame(summaries)
    sensitivity_summary.to_csv(DEST/"observed_predictive_sensitivity_summary.csv",index=False)
    mde,powers=detection_threshold(data)
    mde.to_csv(DEST/"conditional_OLS_detection_threshold.csv",index=False)
    powers.to_csv(DEST/"conditional_OLS_power_grid.csv",index=False)

    # Five-year projections. All future import values are assumptions in nominal USD.
    anchor=source[source.year.eq(2025)].iloc[0]
    first=source[source.year.eq(2016)].iloc[0]
    growth_china=(anchor.china_food_import_value_current_usd/first.china_food_import_value_current_usd)**(1/9)-1
    growth_usa=(anchor.usa_food_import_value_current_usd/first.usa_food_import_value_current_usd)**(1/9)-1
    scenarios={"flat_2025_import_values":(0.,0.),"China_plus_5pct_USA_flat":(.05,0.),
               "China_minus_5pct_USA_flat":(-.05,0.),"USA_plus_5pct_China_flat":(0.,.05),
               "USA_minus_5pct_China_flat":(0.,-.05),"both_plus_5pct":(.05,.05),
               "both_minus_5pct":(-.05,-.05),"historical_2016_2025_CAGR":(growth_china,growth_usa)}
    forecasts=[];trend_intervals=[]
    for vintage,training in [("through_2024_final",data),("through_2025_provisional_rate",source)]:
        selected={}
        for name,options in candidates.items():
            chosen,score=select(options,training[FEATURES],training.national_tfr)
            selected[name]=chosen.fit(training[FEATURES],training.national_tfr)
            if vintage!="through_2024_final":
                full_parameters.append(dict(training_vintage=vintage,model=name,parameters=parameter_text(chosen),inner_MSE=score))
        trend=sm.OLS(training.national_tfr,sm.add_constant(training[["trend"]])).fit()
        future_trends=pd.DataFrame({"const":1.,"trend":np.arange(2026,2031)-2016})
        interval=trend.get_prediction(future_trends).summary_frame(alpha=.05)
        for i,year in enumerate(range(2026,2031)):
            trend_intervals.append(dict(training_vintage=vintage,year=year,predicted_tfr=interval.iloc[i]["mean"],
                                        iid_linear_trend_prediction_low=interval.iloc[i].obs_ci_lower,
                                        iid_linear_trend_prediction_high=interval.iloc[i].obs_ci_upper))
        for scenario,(gc,gu) in scenarios.items():
            for year in range(2026,2031):
                years=year-2025
                china=anchor.china_food_import_value_current_usd*(1+gc)**years
                usa=anchor.usa_food_import_value_current_usd*(1+gu)**years
                new=pd.DataFrame({"log_china_food":[np.log(china)],"log_usa_food":[np.log(usa)],"trend":[year-2016]})
                point={name:float(fit.predict(new)[0]) for name,fit in selected.items()}
                point["Persistence"]=float(training.national_tfr.iloc[-1])
                point["Linear_trend_only"]=float(trend.predict(sm.add_constant(new[["trend"]],has_constant="add")).iloc[0])
                outside_import_range=bool(((new[FEATURES[:2]]<training[FEATURES[:2]].min()) |
                                          (new[FEATURES[:2]]>training[FEATURES[:2]].max())).any(axis=None))
                for name,value in point.items():
                    forecasts.append(dict(training_vintage=vintage,scenario=scenario,year=year,model=name,
                                          projected_tfr=value,assumed_china_value_usd=china,assumed_usa_value_usd=usa,
                                          assumed_china_growth=gc,assumed_usa_growth=gu,
                                          imports_outside_marginal_training_ranges=outside_import_range,
                                          time_outside_training_range=True,
                                          interpretation="Conditional scenario projection; not a causal estimate or calibrated probabilistic forecast"))
    projections=pd.DataFrame(forecasts)
    projections.to_csv(DEST/"projections_2026_2030.csv",index=False)
    pd.DataFrame(trend_intervals).to_csv(DEST/"illustrative_linear_trend_prediction_intervals.csv",index=False)
    pd.DataFrame(full_parameters).to_csv(DEST/"final_model_parameters.csv",index=False)
    # Synthetic data are evaluated separately with a fixed, disclosed parameter choice per family.
    synth=pd.read_csv(ROOT/"synthetic"/"food_import_simulation"/"SYNTHETIC_food_import_panel.csv")
    synthetic_metrics=[];synthetic_predictions=[];synthetic_sensitivity=[]
    fixed={"OLS_imports_and_trend":[make_pipeline(StandardScaler(),LinearRegression())],
           "Ridge":[make_pipeline(StandardScaler(),Ridge(alpha=1.))],
           "ElasticNet":[make_pipeline(StandardScaler(),ElasticNet(alpha=.001,l1_ratio=.5,max_iter=100000))],
           "SVR_RBF":[make_pipeline(StandardScaler(),SVR(C=.1,epsilon=.01))],
           "RandomForest_shallow":[RandomForestRegressor(n_estimators=100,max_depth=2,min_samples_leaf=2,random_state=SEED,n_jobs=1)]}
    for scenario,g in synth.groupby("scenario",sort=False):
        aggregate=g.groupby("synthetic_period").agg(national_tfr=("synthetic_tfr","mean"),
                    log_china_food=("log_china_food","first"),log_usa_food=("log_usa_food","first")).reset_index()
        aggregate["year"]=aggregate.synthetic_period;aggregate["trend"]=aggregate.synthetic_period-1
        sp,synthetic_score,_=temporal_comparison(aggregate,"SYNTHETIC_"+scenario,20,fixed,tune=False)
        synthetic_metrics.append(synthetic_score);synthetic_predictions.append(sp)
        for name,options in fixed.items():
            fit=clone(options[0]).fit(aggregate[FEATURES],aggregate.national_tfr)
            true_parameters=g[["true_china_beta","true_usa_beta"]].iloc[0]
            for country,col,true_col in [("China","log_china_food","true_china_beta"),("USA","log_usa_food","true_usa_beta")]:
                changed=aggregate[FEATURES].copy();changed[col]+=np.log1p(.01)
                supported=((changed>=aggregate[FEATURES].min()) & (changed<=aggregate[FEATURES].max())).all(axis=1)
                delta=fit.predict(changed)-fit.predict(aggregate[FEATURES])
                synthetic_sensitivity.append(dict(data_status="SYNTHETIC_NOT_OBSERVED",scenario=scenario,model=name,country=country,
                                                  chosen_true_beta=true_parameters[true_col],
                                                  chosen_true_tfr_change_for_1pct=true_parameters[true_col]*np.log1p(.01),
                                                  mean_predictive_tfr_change_for_1pct=delta[supported].mean(),
                                                  supported_points=int(supported.sum()),
                                                  interpretation="Predictive response need not equal the chosen structural effect"))
    pd.concat(synthetic_metrics).to_csv(DEST/"SYNTHETIC_separate_model_comparison.csv",index=False)
    pd.concat(synthetic_predictions).to_csv(DEST/"SYNTHETIC_separate_predictions.csv",index=False)
    pd.DataFrame(synthetic_sensitivity).to_csv(DEST/"SYNTHETIC_predictive_sensitivity_vs_chosen_truth.csv",index=False)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(13,5))
    names=["Persistence","Linear_trend_only","OLS_imports_and_trend","Ridge","ElasticNet","SVR_RBF","RandomForest_shallow"]
    colours={name:plt.get_cmap("tab10")(i) for i,name in enumerate(names)}
    for name,g in pred.groupby("model",sort=False):
        axes[0].plot(g.year,g.predicted,marker="o",label=name,linewidth=1,color=colours[name])
    observed=pred.drop_duplicates("year")
    axes[0].plot(observed.year,observed.actual,color="black",linewidth=2.5,label="Observed TFR")
    axes[0].set_title("Chronological outcome predictions; 4 held-out years")
    axes[0].set_xlabel("Year");axes[0].set_ylabel("National TFR")
    axes[0].set_xticks([2021,2022,2023,2024])
    flat=projections[(projections.training_vintage=="through_2025_provisional_rate") &
                     projections.scenario.eq("flat_2025_import_values")]
    for name,g in flat.groupby("model",sort=False):
        axes[1].plot(g.year,g.projected_tfr,marker="o",label=name,linewidth=1,color=colours[name])
    axes[1].set_title("2026–2030: flat import-value scenario\nIncludes provisional 2025 TFR")
    axes[1].set_xlabel("Year");axes[1].set_ylabel("Scenario-projected TFR")
    axes[1].set_xticks([2026,2027,2028,2029,2030])
    axes[0].legend(fontsize=7);axes[1].legend(fontsize=7)
    fig.tight_layout();fig.savefig(DEST/"ml_validation_and_projections.png",dpi=160);plt.close(fig)

    primary_sensitivity=sensitivity_summary[np.isclose(sensitivity_summary.import_value_change_fraction,.01)]
    flat_latest=flat.pivot(index="year",columns="model",values="projected_tfr").reset_index()
    metadata=dict(observed_n=9,observed_validation_years=[2021,2022,2023,2024],validation="Expanding-window outer folds; hyperparameters selected using past-only inner one-step predictions; all scalers fitted inside each fold",
                  features=FEATURES,organic_interaction=False,seed=SEED,forecast_years=list(range(2026,2031)),
                  forecast_scenarios={k:{"China_growth":v[0],"USA_growth":v[1]} for k,v in scenarios.items()},
                  warning="Contemporaneous import values are supplied for held-out outcomes; evaluation is conditional hindcasting, not a forecast of unknown imports",
                  synthetic_scope="Four scenarios separately aggregated to 30 synthetic periods; fixed declared parameters; no pooling with real data",
                  sensitivity_scope="Finite input perturbations; univariate range checks do not establish joint or causal support; leave-year-out ranges are not confidence intervals",
                  mde_assumptions="Conditional on the observed design, estimated iid homoskedastic Gaussian noise, linear specification; 80% power, 5% two-sided alpha. Sigma is varied 0.5x–2x. Not an actual causal detection guarantee.")
    metadata["software_versions"]={name:version(name) for name in ["numpy","pandas","scipy","statsmodels","scikit-learn"]}
    (DEST/"methods_and_assumptions.json").write_text(json.dumps(metadata,indent=2)+"\n")
    report=["# ML regression, predictive sensitivity and scenario projections", "",
            "Observed data: national TFR and separate China/USA broad food import values. Primary sample: 2016–2024, nine years. No organic interaction. Synthetic evaluation is separate.",
            "", "## Chronological comparison", "",
            "Each outer fit uses only previous years, starting with five training years; outcomes in 2021–2024 are held out in turn. Hyperparameter tuning uses only earlier observations within that outer training set. Scaling is in the fitted pipeline. All four evaluation years and every family are reported.",
            "", "Contemporaneous import values are supplied at prediction time. This is a conditional chronological hindcast of TFR, not a true advance forecast of imports or an untouched prospective validation exercise. Four errors are too few to establish stable model superiority, calibrated prediction intervals or statistical significance of rankings.", "",
            table(metrics.sort_values("MAE"),["model","validation_n","MAE","RMSE","max_absolute_error"]),
            "", "## Predictive sensitivity to +1% import value", "",
            "Predictions are recomputed after increasing one country's value by 1%, holding time and the other country fixed. Only changes within marginal training ranges enter the mean. These ranges do not ensure realistic joint combinations. The figures describe the fitted prediction function, not causal responses or physical food quantities.", "",
            table(primary_sensitivity,["model","country","mean_predicted_tfr_change","supported_points","leave_year_out_1pct_min","leave_year_out_1pct_max"]),
            "", "Leave-one-year-out ranges re-estimate the model with selected parameters fixed, and use supported points for each fit. Evaluation points may differ; these are stability ranges, not confidence intervals. Tree responses can be zero for small changes because a perturbation does not cross a split. Zero local response does not prove irrelevance. ±1%, ±5% and ±10% results, including unsupported perturbations, are exported.",
            "", "## Conditional detection threshold", "",
            "This is a separate linear-model design calculation. It solves a two-sided noncentral-t power equation for 80% power at alpha 0.05, with five residual degrees of freedom. Assumptions: the observed design, correctly specified linear model, iid homoskedastic Gaussian errors, and the estimated residual noise. These assumptions are stronger than the empirical evidence supports. The noise sensitivity below prevents treating its plug-in number as precisely known. It is not post-hoc proof that non-significance was caused by low power.", "",
            table(mde,["country","noise_sd_multiplier","coefficient_MDE","tfr_change_MDE_for_10pct_value_change"]),
            "", "## Future years: 2026–2030", "",
            "Future import values are scenarios, not known observations. The full export includes flat 2025 values, one-origin ±5% annual changes, joint ±5% changes, and continuation of each country's 2016–2025 nominal-dollar CAGR. Separate model fits use final-labelled data through 2024 and a latest-data sensitivity including provisional 2025 TFR. Future inputs are not converted into observed data.",
            "", "Flat 2025 import values, using provisional 2025 TFR:", "",
            table(flat_latest,["year","Linear_trend_only","Persistence","OLS_imports_and_trend","Ridge","ElasticNet","SVR_RBF","RandomForest_shallow"]),
            "", "All projected years are outside the training time range. Trees cannot extrapolate trends beyond terminal leaves; RBF SVR can revert towards its fitted baseline far outside training support. The resulting model spread is not a probability interval. These projections do not justify a policy or causal interpretation. No calibrated ML 95% intervals are claimed from four chronological errors.",
            "", "An illustrative linear-trend 95% prediction interval is exported separately under iid normal-error, stable-linear-trend assumptions. It does not account for structural breaks, import-scenario uncertainty, source revisions or model selection; it is not a calibrated interval for the ML models.",
            "", "![Chronological validation and scenario projections](ml_validation_and_projections.png)",
            "", "## Synthetic benchmark", "",
            "All four synthetic scenarios are evaluated separately on synthetic national means, with 20 initial periods and 10 chronological held-out outcomes. Hyperparameters are fixed to declared conventional choices rather than tuned to simulation truths. Model performance under these chosen DGPs does not establish a causal food effect or validate the observational model. These rows are never pooled with observed data.",
            "", "The separate synthetic sensitivity export compares each fully fitted model's +1% predictive response with the structural response explicitly chosen in the DGP. Shared-confounding scenarios illustrate why predictive feature sensitivity can differ from a causal effect even when prediction is accurate. No oracle shock variable is supplied to these ML models.",
            "", "## Reproduce", "", "```bash", "python scripts/_13_ml_sensitivity_projections.py", "```", "",
            "## References", "", "- Chronological validation: https://scikit-learn.org/stable/modules/cross_validation.html",
            "- Leakage-safe preprocessing: https://scikit-learn.org/stable/common_pitfalls.html",
            "- Counterfactual feature-combination limitations: https://scikit-learn.org/stable/modules/partial_dependence.html",
            "- Noncentral t distribution: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.nct.html", ""]
    (DEST/"ML_SENSITIVITY_AND_PROJECTIONS.md").write_text("\n".join(report))
    print(metrics.sort_values("MAE").to_string(index=False))
    print(primary_sensitivity[["model","country","mean_predicted_tfr_change","leave_year_out_1pct_min","leave_year_out_1pct_max"]].to_string(index=False))
    print(flat_latest.to_string(index=False))
    print(mde[mde.noise_sd_multiplier.eq(1.)].to_string(index=False))


if __name__=="__main__":
    main()
