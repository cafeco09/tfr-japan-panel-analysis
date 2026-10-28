# ML rerun: named foods and soyabeans

Nine observed annual outcomes, 2016–2024. Identical expanding-window held-out years 2021–2024. Tuning and scaling use past data only. Contemporaneous import inputs make these conditional hindcasts. No synthetic rows are pooled.

## Chronological comparison

| dataset | model | validation_n | MAE | RMSE |
|---|---|---|---|---|
| total_external_food | Persistence | 4.00000 | 0.04500 | 0.04637 |
| total_external_food | Linear_trend_only | 4.00000 | 0.02370 | 0.02671 |
| total_external_food | OLS_imports_and_trend | 4.00000 | 0.02596 | 0.02714 |
| total_external_food | Ridge | 4.00000 | 0.02827 | 0.02926 |
| total_external_food | ElasticNet | 4.00000 | 0.03166 | 0.03286 |
| total_external_food | SVR_RBF | 4.00000 | 0.10077 | 0.10304 |
| total_external_food | RandomForest_shallow | 4.00000 | 0.10895 | 0.11215 |
| soyabeans_and_other_food | Persistence | 4.00000 | 0.04500 | 0.04637 |
| soyabeans_and_other_food | Linear_trend_only | 4.00000 | 0.02370 | 0.02671 |
| soyabeans_and_other_food | OLS_imports_and_trend | 4.00000 | 0.32139 | 0.60263 |
| soyabeans_and_other_food | Ridge | 4.00000 | 0.11475 | 0.18731 |
| soyabeans_and_other_food | ElasticNet | 4.00000 | 0.08346 | 0.12455 |
| soyabeans_and_other_food | SVR_RBF | 4.00000 | 0.10534 | 0.10598 |
| soyabeans_and_other_food | RandomForest_shallow | 4.00000 | 0.11039 | 0.11266 |
| named_food_groups | Persistence | 4.00000 | 0.04500 | 0.04637 |
| named_food_groups | Linear_trend_only | 4.00000 | 0.02370 | 0.02671 |
| named_food_groups | Ridge | 4.00000 | 0.06785 | 0.07968 |
| named_food_groups | ElasticNet | 4.00000 | 0.02552 | 0.02861 |
| named_food_groups | SVR_RBF | 4.00000 | 0.13193 | 0.13555 |
| named_food_groups | RandomForest_shallow | 4.00000 | 0.12389 | 0.12552 |

Trend-only MAE is 0.02370 TFR units. At least one import model beats it: False. All import specifications and model families are retained rather than selecting a favourable result.

The soyabean OLS model predicts approximately 0.096 for 2021 versus observed 1.30. This failure is retained in the scores. Whole-soyabean values varied little in the initial five training years before rising sharply in 2021; the short-sample multivariable fit extrapolates poorly. A small full-sample coefficient cannot be interpreted as evidence of reliable prediction.

The first set reproduces the total-import benchmark. The second separates whole soyabeans (HS1201, including sowing seed) from other mapped food, without double counting. Soy oil, flour and sauce remain in other food. The third includes named HS2 groups that had complete positive records in the initial 2016–2020 training window. No missing values are replaced with zero. Underidentified OLS is omitted from the group model.

Named group model: 20 groups plus trend. Excluded initial-coverage groups: 24. The number of predictors is large relative to nine outcomes. Regularisation does not create independent information. Comparing many specifications against four errors risks selecting chance winners; these results are exploratory and no fresh untouched test set remains.

## Soyabean predictive sensitivity

| model | feature | change_fraction | mean_tfr_change | supported_points |
|---|---|---|---|---|
| OLS_imports_and_trend | log_soyabeans_usd | 0.01000 | -0.00049 | 8.00000 |
| OLS_imports_and_trend | log_other_mapped_food_usd | 0.01000 | 0.00367 | 8.00000 |
| Ridge | log_soyabeans_usd | 0.01000 | -0.00054 | 8.00000 |
| Ridge | log_other_mapped_food_usd | 0.01000 | 0.00353 | 8.00000 |
| ElasticNet | log_soyabeans_usd | 0.01000 | -0.00033 | 8.00000 |
| ElasticNet | log_other_mapped_food_usd | 0.01000 | 0.00297 | 8.00000 |
| SVR_RBF | log_soyabeans_usd | 0.01000 | 0.00083 | 8.00000 |
| SVR_RBF | log_other_mapped_food_usd | 0.01000 | -0.00027 | 8.00000 |
| RandomForest_shallow | log_soyabeans_usd | 0.01000 | 0.00039 | 8.00000 |
| RandomForest_shallow | log_other_mapped_food_usd | 0.01000 | -0.00269 | 8.00000 |

A 1% increase in one nominal import value holds time and the other import value fixed. Marginal support checks do not ensure realistic joint inputs. These are fitted responses, not causal effects or significance tests. Leave-year-out stability results are exported separately; those ranges are not confidence intervals.

| model | feature | min | max |
|---|---|---|---|
| ElasticNet | log_other_mapped_food_usd | 0.00127 | 0.00366 |
| ElasticNet | log_soyabeans_usd | -0.00066 | 0.00000 |
| OLS_imports_and_trend | log_other_mapped_food_usd | 0.00094 | 0.00455 |
| OLS_imports_and_trend | log_soyabeans_usd | -0.00079 | 0.00021 |
| RandomForest_shallow | log_other_mapped_food_usd | -0.00510 | -0.00031 |
| RandomForest_shallow | log_soyabeans_usd | 0.00000 | 0.00092 |
| Ridge | log_other_mapped_food_usd | 0.00138 | 0.00431 |
| Ridge | log_soyabeans_usd | -0.00084 | 0.00002 |
| SVR_RBF | log_other_mapped_food_usd | -0.00082 | 0.00122 |
| SVR_RBF | log_soyabeans_usd | 0.00011 | 0.00102 |

## Flat-import scenario, 2026–2030

This table includes provisional 2025 TFR in training. Fits excluding that rate and all five import scenarios are also exported. These are extrapolations, not official forecasts or calibrated intervals. Tree and RBF models extrapolate time poorly.

| year | OLS_imports_and_trend | Ridge | ElasticNet | SVR_RBF | RandomForest_shallow |
|---|---|---|---|---|---|
| 2026.00000 | 1.10482 | 1.10763 | 1.10430 | 1.14856 | 1.19355 |
| 2027.00000 | 1.06565 | 1.06919 | 1.06567 | 1.16651 | 1.19355 |
| 2028.00000 | 1.02648 | 1.03076 | 1.02704 | 1.19279 | 1.19355 |
| 2029.00000 | 0.98731 | 0.99233 | 0.98842 | 1.22125 | 1.19355 |
| 2030.00000 | 0.94814 | 0.95390 | 0.94979 | 1.24705 | 1.19355 |

## Reproduce

```bash
python scripts/_15_external_food_analysis.py
python scripts/_17_named_food_ml.py
```

Inputs, source hashes, coverage rules and software versions are in methods.json. Product provenance is retained in output/food_names/source_batches.csv and the archived Comtrade responses.
