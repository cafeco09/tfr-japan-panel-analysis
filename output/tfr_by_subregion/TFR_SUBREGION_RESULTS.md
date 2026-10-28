# TFR explained by subregional indicators

Dependent variable: prefectural TFR, in children per woman. Independent variables: prefecture categories, entered as 46 indicators plus an intercept. Region codes are labels, not a numerical scale. Hokkaido is the reference category.

Primary sample: 47 prefectures, 2016–2024, 423 records. A separate sensitivity adds provisional 2025. Each prefecture has an observed rate in each year; no TFR is imputed.

## Models

```text
TFR = intercept + prefecture indicators + error
TFR = intercept + prefecture indicators + year indicators + error
```

A years-only model is also exported as a descriptive benchmark. These regressions do not include food imports. The earlier import regressions already had TFR on the left-hand side and prefecture fixed effects on the right-hand side; this run isolates the regional predictors explicitly.

| spec | panel_rows | r_squared | adjusted_r_squared | in_sample_RMSE |
|---|---|---|---|---|
| prefectures_only | 423.00000 | 0.65887 | 0.61714 | 0.09728 |
| years_only | 423.00000 | 0.31825 | 0.30508 | 0.13753 |
| prefectures_and_years | 423.00000 | 0.97712 | 0.97376 | 0.02519 |

R-squared is descriptive in-sample fit; it is not a causal contribution or held-out predictive accuracy. With a balanced panel, adding common year effects leaves the prefecture differences unchanged, while accounting for the common annual TFR pattern.

## Lowest and highest average TFR

| prefecture | mean_tfr | difference_from_Hokkaido |
|---|---|---|
| Tokyo | 1.11000 | -0.07778 |
| Hokkaido | 1.18778 | 0.00000 |
| Miyagi | 1.18889 | 0.00111 |
| Shimane | 1.61889 | 0.43111 |
| Miyazaki | 1.63667 | 0.44889 |
| Okinawa | 1.78556 | 0.59778 |

The region-only intercept is Hokkaido's average TFR. Each region coefficient is that prefecture's average difference from Hokkaido. In the region-plus-year model, the intercept is the fitted Hokkaido value at the reference year 2016; year coefficients are common changes relative to 2016. No rank ordering of numerical region codes is used.

## Inference and exports

all_model_coefficients.csv includes the region and year coefficients with year-clustered standard errors. Nine primary year clusters are few. No joint cluster Wald test over all 46 regional indicators is interpreted because the covariance has insufficient rank for that test.

prefecture_contrasts_vs_Hokkaido.csv treats each year's paired TFR difference as one annual observation and reports HC3 and lag-one HAC sensitivity, with BH adjustment across the 46 contrasts within each method and sample vintage. Both inference methods have assumptions that nine years cannot validate. These comparisons describe persistent differences; they do not establish causal effects of living in a prefecture.

prefecture_summary.csv includes all 47 regions, mean/minimum/maximum TFR, and leave-year-out contrast ranges. A range is a stability diagnostic, not a confidence interval.

## Reproduce

```bash
python scripts/_20_tfr_by_subregion.py
```
