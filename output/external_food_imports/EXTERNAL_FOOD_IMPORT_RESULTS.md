# Total external food imports: updated analysis

Current question: Japan's total food imports from all origins as one external-import variable. No country split or organic interaction is included.

## Data definition

Use Japan-reported imports with World partner code 0, BEC Rev.4 category 1 (food and beverages), including primary and processed categories. This source aggregate covers all partners directly. It is not China + USA, and individual country totals are not added on top of the World total. Standard reported imports are used; this is not a separately constructed net-import or domestic-food-consumption measure.

Values are current USD, not physical volumes. Aggregate weights are unavailable and are not read as zero. The primary outcome sample uses official national TFR for 2016–2024 (nine observations); the provisional 2025 rate is a separate sensitivity. The broader origin scope does not add independent annual observations. Existing two-origin synthetic panels are not relabelled as World data.

Source quality: some published category-1 totals do not exactly equal categories 11 + 12. Gaps and reconciliation flags are retained in the data, and a component-sum linear-trend sensitivity is included below. The published World category-1 total remains the main measure; values are not silently altered to force additivity. See scope_and_methods.json for affected years and amounts.

## National regression results

Hypothesis: a negative association. Coefficients are unconstrained. The primary results use HC3 SE with a t reference distribution; HAC lag-one sensitivity is exported. Neither covariance method solves confounding or provides exact inference in this small sample. Positive or non-significant coefficients cannot be reported as support for the negative hypothesis.

| spec | coefficient | se | p_two_sided | ci_low | ci_high | n |
|---|---|---|---|---|---|---|
| no_time_trend | -0.94737 | 0.54705 | 0.12692 | -2.24094 | 0.34620 | 9.00000 |
| linear_time_trend | 0.24937 | 0.20769 | 0.27513 | -0.25884 | 0.75757 | 9.00000 |
| quadratic_time_trend | 0.12608 | 0.07301 | 0.14475 | -0.06159 | 0.31375 | 9.00000 |
| first_differences | 0.15604 | 0.11306 | 0.21679 | -0.12062 | 0.43269 | 8.00000 |
| one_year_lag_linear_trend | -0.00997 | 0.19229 | 0.96067 | -0.50426 | 0.48433 | 8.00000 |
| component_sum_linear_trend | 0.24937 | 0.20767 | 0.27508 | -0.25878 | 0.75752 | 9.00000 |

Inference-method sensitivity: the no-trend negative association has lag-one HAC p = 0.017 versus HC3 p = 0.127. Its direction changes after adding the linear trend (HC3 p = 0.275; HAC p = 0.113). The quadratic-trend HAC result is positive with p = 0.044. These small-sample, model-dependent significance differences are not consistent evidence for a negative causal effect. All covariance variants are retained in the CSV rather than selecting a preferred p-value.

Including provisional 2025:

| spec | coefficient | p_two_sided | n |
|---|---|---|---|
| no_time_trend | -1.18025 | 0.12263 | 10.00000 |
| linear_time_trend | 0.24752 | 0.25780 | 10.00000 |
| quadratic_time_trend | 0.18367 | 0.39536 | 10.00000 |
| first_differences | 0.17756 | 0.16201 | 9.00000 |
| one_year_lag_linear_trend | -0.05035 | 0.72348 | 9.00000 |
| component_sum_linear_trend | 0.24751 | 0.25781 | 10.00000 |

A log-level coefficient gives TFR units per log-point higher nominal import value. The first-difference model relates annual changes; the lag model changes the timing. These are associations under different time-pattern restrictions, not interchangeable causal estimates. Annual fixed effects absorb the national main effect entirely.

## ML comparison

Four chronological outcomes (2021–2024), initially trained on five past years. Hyperparameter tuning and scaling use only training data. Contemporary import values are supplied for held-out years, so the evaluation is conditional hindcasting rather than advance prediction of unknown imports. All candidates are shown; four errors cannot establish a reliable winner.

| model | validation_n | MAE | RMSE |
|---|---|---|---|
| Linear_trend_only | 4.00000 | 0.02370 | 0.02671 |
| OLS_imports_and_trend | 4.00000 | 0.02596 | 0.02714 |
| Ridge | 4.00000 | 0.02827 | 0.02926 |
| ElasticNet | 4.00000 | 0.03166 | 0.03286 |
| Persistence | 4.00000 | 0.04500 | 0.04637 |
| SVR_RBF | 4.00000 | 0.10077 | 0.10304 |
| RandomForest_shallow | 4.00000 | 0.10895 | 0.11215 |

## Predictive sensitivity

A +1% nominal import-value perturbation, holding time fixed, is recomputed for every in-range point. The means below are responses of fitted models, not causal derivatives or significance tests. Leave-year-out ranges use fixed selected parameters and varying supported points; they are not confidence intervals. All ±1%, ±5%, ±10% perturbations and support flags are exported.

| model | mean_predicted_tfr_change | supported_points | loo_1pct_min | loo_1pct_max |
|---|---|---|---|---|
| OLS_imports_and_trend | 0.00248 | 8.00000 | 0.00148 | 0.00364 |
| Ridge | 0.00224 | 8.00000 | 0.00133 | 0.00325 |
| ElasticNet | 0.00137 | 8.00000 | 0.00051 | 0.00231 |
| SVR_RBF | 0.00219 | 8.00000 | -0.00061 | 0.00348 |
| RandomForest_shallow | -0.00379 | 8.00000 | -0.00872 | -0.00141 |

## 2026–2030 projections

Future import values are explicit scenarios: flat 2025 values, ±5% annually, or historical 2016–2025 nominal-value CAGR. Separate fits exclude/include provisional 2025 TFR. These are conditional extrapolations, not official forecasts or confidence intervals. Model spread does not quantify all uncertainty; trees and RBF SVR are particularly limited when extrapolating time.

Flat 2025 import values, provisional 2025 rate included:

| year | OLS_imports_and_trend | Ridge | ElasticNet | Linear_trend_only | SVR_RBF | RandomForest_shallow |
|---|---|---|---|---|---|---|
| 2026.00000 | 1.09598 | 1.09858 | 1.10356 | 1.10000 | 1.14505 | 1.19025 |
| 2027.00000 | 1.05616 | 1.05948 | 1.06626 | 1.06309 | 1.16705 | 1.19025 |
| 2028.00000 | 1.01633 | 1.02038 | 1.02896 | 1.02618 | 1.20111 | 1.19025 |
| 2029.00000 | 0.97651 | 0.98128 | 0.99166 | 0.98927 | 1.23615 | 1.19025 |
| 2030.00000 | 0.93669 | 0.94218 | 0.95436 | 0.95236 | 1.26446 | 1.19025 |

## Detection limit

Conditional iid Gaussian linear-model calculation: 80% power at two-sided alpha 0.05. Noise is estimated from this small sample and varied from half to twice that estimate. These are assumed-design thresholds, not empirical power guarantees or a remedy for endogeneity.

| noise_sd_multiplier | coefficient_MDE | tfr_change_MDE_for_10pct_value |
|---|---|---|
| 0.50000 | 0.22242 | 0.02120 |
| 1.00000 | 0.44484 | 0.04240 |
| 2.00000 | 0.88967 | 0.08480 |

## Interpretation limits

The scope now matches all-origin external food imports. This does not remove national demand shocks, reverse causality, food-price movements, exchange-rate changes or common fertility trends. More source countries do not create more annual treatment shocks after aggregation. Previous country coefficients and projections are superseded for this aggregate question; historical outputs are retained for traceability. No synthetic records are used to increase empirical n.

## Reproduce

```bash
python scripts/_14_external_food_imports.py
python scripts/_15_external_food_analysis.py
```

## Sources

- World import selection: https://uncomtrade.org/docs/how-to-retrieve-data-for-world-exports-to-a-country-in-un-comtrade/
- Raw Comtrade URLs and retrieval dates: data/external_food_sources/.
- National TFR provenance: data/national_tfr_2016_2025.csv and its archived MHLW workbook.
