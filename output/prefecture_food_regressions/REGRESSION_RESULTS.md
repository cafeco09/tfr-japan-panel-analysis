# Prefectural TFR and national food imports: regressions

The negative hypothesis is not supported consistently. The total-import coefficient is negative without a time trend but positive with linear or quadratic trends. The quadratic specification is positive and significant under the reported HC3 inference. The joint soyabean coefficient is not significant and changes sign under year omission. None of the 27 exploratory product/group tests passes BH q < 0.05.

Primary sample: 47 prefectures × 2016–2024 = 423 records, but only nine annual import observations. The 470-row sensitivity adds provisional 2025 TFR. Import values are national, nominal current USD, and identical across prefectures within year.

The outcome is prefectural TFR. Annual checks use its unweighted mean across the 47 prefectures, which differs from Japan's official national TFR. No population weighting, consumption allocation or synthetic observations are introduced.

## Prefecture fixed effects, year-clustered inference

| spec | term | coefficient | se | p_two_sided | ci_low | ci_high | tfr_change_for_10pct |
|---|---|---|---|---|---|---|---|
| total_no_time_trend | log_total_food | -0.86241 | 0.29609 | 0.01951 | -1.54520 | -0.17962 | -0.08220 |
| total_linear_time_trend | log_total_food | 0.30653 | 0.14534 | 0.06798 | -0.02863 | 0.64168 | 0.02921 |
| total_quadratic_time_trend | log_total_food | 0.14866 | 0.02372 | 0.00024 | 0.09395 | 0.20336 | 0.01417 |
| soyabeans_and_other_linear_trend | log_soyabeans | -0.04337 | 0.04696 | 0.38271 | -0.15166 | 0.06492 | -0.00413 |
| soyabeans_and_other_linear_trend | log_other_food | 0.41662 | 0.11461 | 0.00664 | 0.15233 | 0.68092 | 0.03971 |

The primary reference uses eight cluster degrees of freedom, not 423 independent import observations. Nine year clusters are few, and clustering by year does not handle arbitrary serial correlation across years. Time trends restrict common changes; they do not remove all confounding.

## Annual-mean inference sensitivity

| spec | inference | term | coefficient | p_two_sided | ci_low | ci_high |
|---|---|---|---|---|---|---|
| total_no_time_trend | annual_mean_HC3 | log_total_food | -0.86241 | 0.14483 | -2.10519 | 0.38038 |
| total_no_time_trend | annual_mean_HAC_lag1 | log_total_food | -0.86241 | 0.02177 | -1.55645 | -0.16836 |
| total_linear_time_trend | annual_mean_HC3 | log_total_food | 0.30653 | 0.23260 | -0.25846 | 0.87151 |
| total_linear_time_trend | annual_mean_HAC_lag1 | log_total_food | 0.30653 | 0.08259 | -0.05385 | 0.66690 |
| total_quadratic_time_trend | annual_mean_HC3 | log_total_food | 0.14866 | 0.01513 | 0.04325 | 0.25406 |
| total_quadratic_time_trend | annual_mean_HAC_lag1 | log_total_food | 0.14866 | 0.00254 | 0.08021 | 0.21711 |
| soyabeans_and_other_linear_trend | annual_mean_HC3 | log_soyabeans | -0.04337 | 0.68529 | -0.30282 | 0.21608 |
| soyabeans_and_other_linear_trend | annual_mean_HC3 | log_other_food | 0.41662 | 0.26186 | -0.43046 | 1.26371 |
| soyabeans_and_other_linear_trend | annual_mean_HAC_lag1 | log_soyabeans | -0.04337 | 0.33644 | -0.14827 | 0.06152 |
| soyabeans_and_other_linear_trend | annual_mean_HAC_lag1 | log_other_food | 0.41662 | 0.03528 | 0.04256 | 0.79068 |

Because the panel is balanced and regressors vary only by year, the import coefficients equal those from annual unweighted prefecture-mean regressions. This equality is checked numerically. HC3 and lag-one HAC provide different assumptions, not additional observations or exact small-sample inference. All variants are reported.

In particular, the no-trend negative coefficient has year-cluster p = 0.0195 but annual HC3 p = 0.1448. The positive other-food coefficient in the joint model has year-cluster p = 0.0066 but annual HC3 p = 0.2619. The positive quadratic-trend total-import coefficient has annual HC3 p = 0.0151. These differences must remain visible; selecting one covariance method or trend specification to obtain significance would misrepresent the uncertainty.

## Leave-one-year-out stability

| spec | term | min | max |
|---|---|---|---|
| soyabeans_and_other_linear_trend | log_other_food | 0.10789 | 0.48170 |
| soyabeans_and_other_linear_trend | log_soyabeans | -0.08446 | 0.03570 |
| total_linear_time_trend | log_total_food | 0.20208 | 0.44258 |

These ranges omit each year in turn. They are coefficient stability diagnostics, not confidence intervals.

## Provisional 2025 sensitivity

| spec | term | coefficient | p_two_sided | ci_low | ci_high |
|---|---|---|---|---|---|
| total_no_time_trend | log_total_food | -1.10089 | 0.14241 | -2.66129 | 0.45952 |
| total_linear_time_trend | log_total_food | 0.30649 | 0.19401 | -0.19803 | 0.81101 |
| total_quadratic_time_trend | log_total_food | 0.21205 | 0.30582 | -0.25153 | 0.67563 |
| soyabeans_and_other_linear_trend | log_soyabeans | -0.02467 | 0.62382 | -0.14148 | 0.09214 |
| soyabeans_and_other_linear_trend | log_other_food | 0.37832 | 0.13991 | -0.16599 | 0.92263 |

## Food-group and soy-product screening

27 separate log-import-plus-linear-trend regressions, each with nine annual outcomes. All results are exported, with Benjamini–Hochberg adjustment across the full family. Incomplete series are excluded, not imputed as zero. A significant screen is exploratory and does not identify a causal or regional food effect.

| feature | coefficient | p_HC3 | BH_q_value |
|---|---|---|---|
| group_hs02_usd | 0.32645 | 0.03469 | 0.36526 |
| group_hs08_usd | 0.30582 | 0.03860 | 0.36526 |
| group_hs16_usd | 0.31747 | 0.04058 | 0.36526 |
| group_hs04_usd | 0.22663 | 0.07507 | 0.48729 |
| group_hs19_usd | 0.48362 | 0.09024 | 0.48729 |
| group_hs17_usd | -0.09762 | 0.11589 | 0.52149 |
| group_hs18_usd | -0.12812 | 0.15196 | 0.53303 |
| soy_hs120810_usd | -0.03352 | 0.15848 | 0.53303 |
| group_hs03_usd | 0.22073 | 0.18694 | 0.53303 |
| group_hs11_usd | -0.11279 | 0.21054 | 0.53303 |
| group_hs21_usd | 0.35158 | 0.21716 | 0.53303 |
| soy_hs150710_usd | 0.01474 | 0.30357 | 0.65760 |
| group_hs10_usd | 0.08381 | 0.31662 | 0.65760 |
| group_hs12_usd | 0.06307 | 0.41705 | 0.80431 |
| group_hs09_usd | -0.10093 | 0.44832 | 0.80697 |
| group_hs22_usd | 0.15567 | 0.48986 | 0.82665 |
| soy_hs210310_usd | 0.12265 | 0.55256 | 0.85832 |
| group_hs15_usd | 0.05384 | 0.65319 | 0.85832 |
| soy_hs120190_usd | 0.03670 | 0.66706 | 0.85832 |
| soy_hs150790_usd | 0.01041 | 0.68381 | 0.85832 |
| group_hs01_usd | 0.07185 | 0.72909 | 0.85832 |
| group_hs07_usd | 0.10793 | 0.78063 | 0.85832 |
| soy_hs230400_usd | 0.04654 | 0.78641 | 0.85832 |
| group_hs23_usd | 0.04540 | 0.78946 | 0.85832 |
| soy_hs120110_usd | -0.01060 | 0.79474 | 0.85832 |
| group_hs35_usd | 0.00309 | 0.95617 | 0.97368 |
| group_hs20_usd | -0.02390 | 0.97368 | 0.97368 |

Whole soyabeans include sowing seed. Soyabean oilcake is a supplementary non-food series and is not added to food totals. Soyabeans, derivatives and food groups overlap; screening coefficients describe separate specifications, not a decomposition of a total effect.

## Unrestricted year effects

All import regressors have zero residual variation after year indicators (verified to tolerance 1e-10). Thus a prefecture-and-year fixed-effects model cannot estimate their main effects. Pseudoinverse output from that rank-deficient design is not reported as an identified result.

## Reproduce

```bash
python scripts/_19_prefecture_food_regressions.py
```

Detailed coefficients, intervals, inference degrees of freedom, screening exclusions and source merge documentation are retained with the CSV exports and methods.json.
