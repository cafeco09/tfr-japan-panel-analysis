# Food imports as predictors of prefectural TFR, with controls

The balanced fully controlled model estimates a total-food coefficient of −0.0503 (year-cluster p = 0.6647; restricted wild-cluster p = 0.7344). In the joint model, soyabeans are negative (−0.0872): conventional year-cluster p = 0.0146, but wild-cluster p = 0.1875. The extended incomplete 2023 panel gives a stronger soyabean result (−0.0960; wild p = 0.0234), while the total-food coefficient changes sign. The negative soyabean association is sensitive to sample and inference; it is not a demonstrated causal effect.

Dependent variable: prefectural TFR. Main independent variable: log national food imports from all origins. Prefecture indicators are categorical control variables. Controls also include a common time trend, log observed prefectural income per resident and log capital-city eating-out expenditure. A separate specification splits whole soyabeans and other mapped food without double counting.

```text
TFR_it = prefecture intercept_i + beta log(food imports_t)
         + gamma log(income_it) + delta log(eating-out proxy_it)
         + common time trend_t + error_it
```

## Matched balanced sample

All controlled comparisons use the same 329 observations: 47 prefectures × 2016–2022. Income is complete through 2022; 2023 has only 42 observed prefectural incomes, and 2024–2025 have none. Missing income is not imputed. Using a shared sample separates the effect of adding controls from changing the sample years.

| spec | term | coefficient | year_cluster_p | wild_cluster_p | ci_low | ci_high | tfr_change_for_10pct |
|---|---|---|---|---|---|---|---|
| total_prefecture_trend | log_food | 0.08913 | 0.46026 | 0.50000 | -0.18737 | 0.36564 | 0.00850 |
| total_plus_income | log_food | -0.05443 | 0.66737 | 0.70312 | -0.34928 | 0.24043 | -0.00519 |
| total_full_controls | log_food | -0.05034 | 0.66469 | 0.73438 | -0.32068 | 0.22001 | -0.00480 |
| total_full_controls_quadratic | log_food | 0.06982 | 0.40099 | 0.53125 | -0.11924 | 0.25888 | 0.00665 |
| soy_other_prefecture_trend | log_soyabeans | -0.07080 | 0.07153 | 0.15625 | -0.15006 | 0.00847 | -0.00675 |
| soy_other_prefecture_trend | log_other_food | 0.23953 | 0.08108 | 0.21875 | -0.04029 | 0.51934 | 0.02283 |
| soy_other_full_controls | log_soyabeans | -0.08720 | 0.01458 | 0.18750 | -0.15004 | -0.02436 | -0.00831 |
| soy_other_full_controls | log_other_food | 0.19238 | 0.12640 | 0.31250 | -0.07295 | 0.45772 | 0.01834 |

Year-cluster inference uses six t degrees of freedom, not 329 independent import observations. Restricted wild cluster bootstrap p-values enumerate all 128 year-sign patterns; they are approximate diagnostics under independent cluster and error-symmetry assumptions, not exact significance guarantees. Neither approach handles arbitrary dependence across years.

## Control coefficients

| spec | term | coefficient | year_cluster_p | ci_low | ci_high |
|---|---|---|---|---|---|
| total_full_controls | trend | -0.02797 | 0.00016 | -0.03620 | -0.01975 |
| total_full_controls | log_income | 0.25254 | 0.00819 | 0.09318 | 0.41190 |
| total_full_controls | log_eating_out | -0.00201 | 0.88964 | -0.03600 | 0.03198 |
| soy_other_full_controls | trend | -0.02807 | 0.00003 | -0.03425 | -0.02190 |
| soy_other_full_controls | log_income | 0.25833 | 0.00971 | 0.08898 | 0.42768 |
| soy_other_full_controls | log_eating_out | -0.03744 | 0.12424 | -0.08873 | 0.01384 |

Income is a broad nominal prefectural income measure per resident, not disposable household income. Its fiscal year is matched to the calendar-year label. Eating-out spending is measured in the prefectural capital's household survey and is used as a proxy; it is not measured prefecture-wide consumption. Both may be endogenous; including them is an association sensitivity, not automatic causal adjustment.

## Extended complete-case sensitivity

The unbalanced 2016–2023 sensitivity includes 371 records and eight year clusters. It adds 42 prefectures in 2023; the five missing incomes remain excluded. All 256 bootstrap sign patterns are evaluated.

| spec | term | coefficient | year_cluster_p | wild_cluster_p | ci_low | ci_high |
|---|---|---|---|---|---|---|
| total_full_controls | log_food | 0.24457 | 0.08969 | 0.20312 | -0.04922 | 0.53835 |
| soy_other_full_controls | log_soyabeans | -0.09595 | 0.00084 | 0.02344 | -0.13670 | -0.05521 |
| soy_other_full_controls | log_other_food | 0.41197 | 0.00014 | 0.04688 | 0.28128 | 0.54266 |

## Leave-one-year-out stability

| spec | term | min | max |
|---|---|---|---|
| soy_other_full_controls | log_other_food | 0.05674 | 0.26125 |
| soy_other_full_controls | log_soyabeans | -0.11411 | -0.05236 |
| total_full_controls | log_food | -0.15650 | 0.16149 |

These ranges are diagnostics, not confidence intervals. Import values are identical across prefectures within each year. Unrestricted year fixed effects would absorb all import main effects, even with these additional controls. A time trend imposes a common path rather than removing all shared national shocks.

Organic-farming and gardening snapshots are not copied across years as controls. No synthetic observations, arbitrary allocation of national imports, or numerical encoding of prefecture labels is used.

## Reproduce

```bash
python scripts/_21_controlled_food_regressions.py
```

Analysis CSVs retain control source URLs, source cells, release vintage and capital-city names. Food and TFR provenance remain in the merged source data.
