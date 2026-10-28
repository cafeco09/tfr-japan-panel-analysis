"""Generate explicitly synthetic food-import/fertility panels for method testing.

python scripts/_11_synthetic_food.py --years 30 --prefectures 47 --seed 20261028
No simulated row is an observed Japanese prefecture-year or empirical evidence.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT=Path(__file__).resolve().parents[1]
LABEL="SYNTHETIC_NOT_OBSERVED"


def ar1(innovations,rho):
    output=np.zeros_like(innovations)
    for period in range(len(innovations)):
        output[period]=innovations[period]+(rho*output[period-1] if period else 0.)
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years",type=int,default=30)
    parser.add_argument("--prefectures",type=int,default=47)
    parser.add_argument("--seed",type=int,default=20261028)
    parser.add_argument("--output",type=Path,default=ROOT/"synthetic"/"food_import_simulation")
    args=parser.parse_args()
    if args.years<10 or args.prefectures<3:
        parser.error("Use at least 10 synthetic periods and 3 synthetic prefectures")
    destination=args.output.resolve()
    destination.mkdir(parents=True,exist_ok=True)
    rng=np.random.default_rng(args.seed)
    observed_path=ROOT/"data"/"food_imports_china_usa_wide.csv"
    calibration=pd.read_csv(observed_path)
    log_centres=np.log(calibration[["china_food_import_value_current_usd","usa_food_import_value_current_usd"]]).mean().to_numpy()
    # Levels alone are calibrated. Trends, persistence, errors and true effects are chosen simulation inputs.
    covariance=np.array([[1.,.45],[.45,1.]])*.06**2
    deviations=ar1(rng.multivariate_normal([0.,0.],covariance,size=args.years),.55)
    time=np.arange(args.years)
    log_imports=log_centres+np.column_stack([.018*time,.012*time])+deviations
    prefecture_intercepts=rng.normal(0.,.12,size=args.prefectures)
    common_loadings=rng.uniform(.75,1.25,size=args.prefectures)
    common_unrelated=ar1(rng.normal(0.,.025,size=args.years),.35)
    idiosyncratic=ar1(rng.normal(0.,.022,size=(args.years,args.prefectures)),.4)
    china_state=(deviations[:,0]-deviations[:,0].mean())/deviations[:,0].std(ddof=0)
    scenarios={
        "null_unrelated_common_shocks":dict(china_beta=0.,usa_beta=0.,confounding_sign=0.),
        "null_positive_shared_confounding":dict(china_beta=0.,usa_beta=0.,confounding_sign=1.),
        "null_negative_shared_confounding":dict(china_beta=0.,usa_beta=0.,confounding_sign=-1.),
        "known_effect_benchmark":dict(china_beta=-.08,usa_beta=.04,confounding_sign=0.),
    }
    panels=[]
    national=[]
    for scenario,parameters in scenarios.items():
        shared_shock=common_unrelated+parameters["confounding_sign"]*.055*china_state
        for period in time:
            china_causal=parameters["china_beta"]*(log_imports[period,0]-log_centres[0])
            usa_causal=parameters["usa_beta"]*(log_imports[period,1]-log_centres[1])
            national.append(dict(data_status=LABEL,scenario=scenario,synthetic_period=int(period+1),
                                 synthetic_china_food_import_value_usd=float(np.exp(log_imports[period,0])),
                                 synthetic_usa_food_import_value_usd=float(np.exp(log_imports[period,1])),
                                 latent_common_shock=shared_shock[period]))
            for prefecture in range(args.prefectures):
                contribution=common_loadings[prefecture]*shared_shock[period]
                tfr=1.5+prefecture_intercepts[prefecture]-.008*period+china_causal+usa_causal+contribution+idiosyncratic[period,prefecture]
                panels.append(dict(data_status=LABEL,scenario=scenario,
                                   synthetic_prefecture_id=f"SYN-P{prefecture+1:03d}",synthetic_period=int(period+1),
                                   synthetic_tfr=tfr,
                                   synthetic_china_food_import_value_usd=float(np.exp(log_imports[period,0])),
                                   synthetic_usa_food_import_value_usd=float(np.exp(log_imports[period,1])),
                                   log_china_food=log_imports[period,0],log_usa_food=log_imports[period,1],
                                   true_china_beta=parameters["china_beta"],true_usa_beta=parameters["usa_beta"],
                                   latent_common_shock=shared_shock[period],
                                   true_common_shock_contribution=contribution,
                                   true_prefecture_intercept=prefecture_intercepts[prefecture],
                                   true_time_trend=-.008*period,
                                   true_china_contribution=china_causal,true_usa_contribution=usa_causal,
                                   idiosyncratic_error=idiosyncratic[period,prefecture]))
    panel=pd.DataFrame(panels)
    national=pd.DataFrame(national)
    panel.to_csv(destination/"SYNTHETIC_food_import_panel.csv",index=False)
    national.to_csv(destination/"SYNTHETIC_national_import_series.csv",index=False)
    assert panel.data_status.eq(LABEL).all()
    assert len(panel)==4*args.years*args.prefectures
    assert not panel.duplicated(["scenario","synthetic_prefecture_id","synthetic_period"]).any()
    columns=["synthetic_china_food_import_value_usd","synthetic_usa_food_import_value_usd"]
    assert panel.groupby(["scenario","synthetic_period"])[columns].nunique().eq(1).all().all()
    reconstructed=(1.5+panel.true_prefecture_intercept+panel.true_time_trend+
                   panel.true_china_contribution+panel.true_usa_contribution+
                   panel.true_common_shock_contribution+panel.idiosyncratic_error)
    np.testing.assert_allclose(panel.synthetic_tfr,reconstructed,atol=1e-12)
    aligned=panel.pivot(index=["synthetic_prefecture_id","synthetic_period"],columns="scenario",values="synthetic_tfr")
    np.testing.assert_allclose(aligned.null_positive_shared_confounding+aligned.null_negative_shared_confounding,
                               2*aligned.null_unrelated_common_shocks,atol=1e-12)
    assert np.isfinite(panel.select_dtypes(include="number")).all().all()
    estimates=[]
    for scenario,data in panel.groupby("scenario",sort=False):
        base="synthetic_tfr ~ log_china_food + log_usa_food + synthetic_period + C(synthetic_prefecture_id)"
        for name,formula in [("omit_latent_common_shock",base),
                             ("oracle_control_unavailable_in_real_data",base+" + true_common_shock_contribution")]:
            model=smf.ols(formula,data=data,missing="raise").fit()
            assert np.linalg.matrix_rank(model.model.exog)==model.model.exog.shape[1]
            for country,variable,truth in [("China","log_china_food","true_china_beta"),("USA","log_usa_food","true_usa_beta")]:
                estimates.append(dict(data_status=LABEL,scenario=scenario,spec=name,country=country,
                                      chosen_true_beta=data[truth].iloc[0],estimated_beta=model.params[variable],
                                      estimation_error=model.params[variable]-data[truth].iloc[0],
                                      synthetic_n=len(data),synthetic_periods=args.years))
    estimates=pd.DataFrame(estimates)
    estimates.to_csv(destination/"SYNTHETIC_estimator_demonstration.csv",index=False)
    metadata=dict(data_status=LABEL,purpose="Method testing and sensitivity simulation, not empirical augmentation",
                  seed=args.seed,synthetic_periods=args.years,synthetic_prefectures=args.prefectures,
                  scenarios=scenarios,rows=len(panel),organic_interaction=False,
                  observed_input=str(observed_path.relative_to(ROOT)),
                  calibration="Only country-specific mean log value levels use the observed 2016–2025 series; all other DGP parameters are chosen",
                  log_import_centres=dict(China=float(log_centres[0]),USA=float(log_centres[1])),
                  import_innovation_covariance=covariance.tolist(),import_ar1=.55,
                  log_import_trends=dict(China=.018,USA=.012),baseline_tfr=1.5,tfr_annual_trend=-.008,
                  prefecture_intercept_sd=.12,common_loading_range=[.75,1.25],
                  independent_common_shock_innovation_sd=.025,common_shock_ar1=.35,
                  confounded_common_shock_scale=.055,idiosyncratic_innovation_sd=.022,idiosyncratic_ar1=.4,
                  warnings=["Synthetic sample size does not increase empirical Japanese information",
                            "Chosen true effects are assumptions, not estimated Japanese effects",
                            "Oracle controls expose the simulation truth and are unavailable in the real study",
                            "One realisation is not a Monte Carlo assessment of estimator bias or coverage",
                            "National imports remain identical across synthetic prefectures within a period",
                            "There is no mapping between synthetic_period and a real calendar year"])
    (destination/"SYNTHETIC_generation_metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    readme=f'''# SYNTHETIC DATA — NOT OBSERVED JAPANESE DATA

Generated with seed {args.seed}. All outcomes, country import paths, prefecture identifiers and common shocks in these files are synthetic.

## Contents

- `SYNTHETIC_food_import_panel.csv`: {len(panel):,} rows = four scenarios × {args.prefectures} synthetic prefectures × {args.years} synthetic periods.
- `SYNTHETIC_national_import_series.csv`: separate China and USA values per synthetic period and scenario.
- `SYNTHETIC_estimator_demonstration.csv`: fitted and known coefficients, with and without the simulated common-shock control.
- `SYNTHETIC_generation_metadata.json`: seed, calibration source, every chosen distributional parameter and limitations.

## Four scenarios

1. **Null with unrelated common shocks:** both true food-import effects are zero.
2. **Null with positive shared confounding:** true effects remain zero, but an omitted shared shock tracks the China import path positively.
3. **Null with negative shared confounding:** true effects remain zero, with the opposite shared-shock relationship.
4. **Known-effect benchmark:** chosen true log-import coefficients are China −0.08 and USA +0.04. These values are arbitrary method-testing inputs, not findings about either country's food.

The same underlying innovations and prefectures are reused across scenarios to make contrasts transparent. Scenarios are not independent datasets. The sample is not filtered to obtain a preferred sign or significant result.

## Data-generating process

Synthetic TFR equals 1.5 + a prefecture intercept − 0.008 × time + the two chosen import effects + a heterogeneous common-shock contribution + serially correlated idiosyncratic error. China and USA log-import paths have correlated innovations, persistence and chosen linear trends. Only mean log-import value levels are calibrated to the observed broad-food series; persistence, effects, noise and trends are assumed.

There is **no organic interaction**. Import variables remain national: each synthetic prefecture sees the same origin-specific value in a given synthetic period. The generator does not invent measured regional exposure. Synthetic periods are numbered 1–{args.years}, with no real-calendar interpretation; synthetic IDs begin `SYN-P` and do not identify real prefectures.

## What this can and cannot establish

These data support code testing and demonstrations of confounding. The estimator table includes an **oracle** regression controlling the exact simulated shock contribution. That variable is deliberately known in the simulation; it is not available in the real data. A single seeded realisation illustrates behaviour and does not estimate repeated-sampling bias, power or confidence-interval coverage.

Synthetic observations must not be pooled with real observations to increase empirical sample size, establish causality or turn exploratory findings into confirmatory evidence. Generated truths are design assumptions. More synthetic prefectures do not create more actual national import shocks.

## Reproduce

From the repository root:

```bash
python scripts/_11_synthetic_food.py --years {args.years} --prefectures {args.prefectures} --seed {args.seed}
```

Change years, prefectures and seed to test other simulation sizes. Source data and the empirical analysis are not modified.

For a separate repeated-simulation assessment, run `python scripts/_12_synthetic_analysis.py --replications 500`. Its results are saved under `analysis/` and describe performance under the chosen DGP; they do not estimate Japanese effects.
'''
    (destination/"README_SYNTHETIC.md").write_text(readme)
    (destination/"validation.txt").write_text("Verified scenario/prefecture/period uniqueness, exact DGP outcome reconstruction, opposite-confounding scenario symmetry, finite numeric values, explicit synthetic labels, row counts, nationally shared import paths and full-rank demonstration models.\n")
    print(estimates.to_string(index=False))
    print(f"Generated {len(panel):,} clearly labelled synthetic rows in {destination}")


if __name__=="__main__":
    main()
