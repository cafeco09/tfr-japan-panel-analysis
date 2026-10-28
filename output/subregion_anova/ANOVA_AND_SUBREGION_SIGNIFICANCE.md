# ANOVA and significance for every prefecture

Outcome: prefectural TFR. Predictor/control model: prefecture categories + log total national food imports + log prefectural income + log capital-city eating-out expenditure + common linear time trend. The balanced observed-control sample is 47 prefectures × 2016–2022, 329 rows. No missing controls are imputed.

## Overall ANOVA

| term | sum_sq | df | F | p_classical |
|---|---|---|---|---|
| C(region_code) | 4.72276 | 46.00000 | 133.91969 | 5.38e-164 |
| log_food | 0.00045 | 1.00000 | 0.58532 | 0.445 |
| trend | 0.14542 | 1.00000 | 189.68958 | 2.96e-33 |
| log_income | 0.00966 | 1.00000 | 12.60175 | 0.000452 |
| log_eating_out | 0.00001 | 1.00000 | 0.01512 | 0.902 |
| Residual | 0.21313 | 278.00000 | — | — |

The conventional Type II prefecture test gives F = 133.920 with 46 numerator and 278 residual degrees of freedom; p = 5.381e-164. This is a classical iid-error benchmark, not robust evidence under panel dependence. The year-clustered covariance for the 46 regional parameters has rank 6, so a 46-df cluster-robust omnibus Wald test is not interpreted.

## Significance for each prefecture

ANOVA supplies an overall test, not a separate significance label for each category. The comparisons below test each prefecture's adjusted TFR difference from the equally weighted adjusted mean across all 47 prefectures. Continuous covariates are held at common sample mean log-values/time. The regional mean comparator includes that region with weight 1/47. These are regional level differences, not prefecture-specific import effects.

Year-clustered p-values use six t degrees of freedom; Holm adjustment controls the 47-comparison family under valid individual tests. Seven clusters are few and arbitrary temporal dependence is not handled. Confidence intervals in the CSV are pointwise, not simultaneous. The significance labels are conditional on this inference model.

| prefecture | difference_from_adjusted_prefecture_mean | year_cluster_p | year_cluster_Holm_p | year_cluster_Holm_significant_5pct | wild_cluster_p |
|---|---|---|---|---|---|
| Hokkaido | -0.20747 | 6.81e-08 | 3.13e-06 | True | 0.0156 |
| Aomori | -0.05077 | 0.0205 | 0.287 | False | 0.0156 |
| Iwate | -0.07214 | 0.00461 | 0.0738 | False | 0.0156 |
| Miyagi | -0.21823 | 9.46e-07 | 3.69e-05 | True | 0.0156 |
| Akita | -0.13245 | 0.000111 | 0.00289 | True | 0.0156 |
| Yamagata | -0.04570 | 0.00087 | 0.0174 | True | 0.0156 |
| Fukushima | 0.00441 | 0.857 | 1 | False | 0.875 |
| Ibaraki | -0.09815 | 0.000313 | 0.00752 | True | 0.0156 |
| Tochigi | -0.11145 | 4.46e-05 | 0.00129 | True | 0.0156 |
| Gunma | -0.06556 | 0.000444 | 0.0102 | True | 0.0156 |
| Saitama | -0.17493 | 1.31e-07 | 5.77e-06 | True | 0.0156 |
| Chiba | -0.18190 | 8.26e-08 | 3.72e-06 | True | 0.0156 |
| Tokyo | -0.47112 | 3.91e-05 | 0.00117 | True | 0.0156 |
| Kanagawa | -0.19207 | 4.31e-08 | 2.02e-06 | True | 0.0156 |
| Niigata | -0.08538 | 2.88e-07 | 1.21e-05 | True | 0.0156 |
| Toyama | 0.01214 | 0.513 | 1 | False | 0.422 |
| Ishikawa | 0.02060 | 0.0565 | 0.622 | False | 0.0625 |
| Fukui | 0.11901 | 2.06e-05 | 0.000659 | True | 0.0156 |
| Yamanashi | 0.00712 | 0.521 | 1 | False | 0.547 |
| Nagano | 0.06407 | 0.00112 | 0.0212 | True | 0.0156 |
| Gifu | -0.00129 | 0.831 | 1 | False | 0.766 |
| Shizuoka | -0.04373 | 0.00425 | 0.0723 | False | 0.0156 |
| Aichi | -0.03951 | 0.0429 | 0.514 | False | 0.0938 |
| Mie | 0.00074 | 0.947 | 1 | False | 0.953 |
| Shiga | 0.02161 | 0.172 | 1 | False | 0.172 |
| Kyoto | -0.19057 | 3.24e-07 | 1.3e-05 | True | 0.0156 |
| Osaka | -0.14859 | 2.32e-06 | 7.89e-05 | True | 0.0156 |
| Hyogo | -0.05053 | 2.07e-05 | 0.000659 | True | 0.0156 |
| Nara | -0.11354 | 0.000266 | 0.00665 | True | 0.0156 |
| Wakayama | 0.00008 | 0.993 | 1 | False | 1 |
| Tottori | 0.18229 | 0.000466 | 0.0102 | True | 0.0156 |
| Shimane | 0.22019 | 3.16e-07 | 1.29e-05 | True | 0.0156 |
| Okayama | 0.05094 | 0.000566 | 0.0119 | True | 0.0156 |
| Hiroshima | 0.02530 | 0.0249 | 0.323 | False | 0.0312 |
| Yamaguchi | 0.06682 | 0.00128 | 0.0231 | True | 0.0156 |
| Tokushima | 0.00970 | 0.488 | 1 | False | 0.453 |
| Kagawa | 0.11080 | 9.91e-05 | 0.00268 | True | 0.0156 |
| Ehime | 0.04254 | 0.018 | 0.27 | False | 0.0469 |
| Kochi | 0.03777 | 0.0638 | 0.638 | False | 0.109 |
| Fukuoka | -0.00301 | 0.357 | 1 | False | 0.312 |
| Saga | 0.17204 | 1.42e-06 | 5.24e-05 | True | 0.0156 |
| Nagasaki | 0.23046 | 1.62e-06 | 5.82e-05 | True | 0.0156 |
| Kumamoto | 0.19137 | 2.79e-07 | 1.2e-05 | True | 0.0156 |
| Oita | 0.14001 | 6.89e-05 | 0.00193 | True | 0.0156 |
| Miyazaki | 0.28478 | 2.06e-06 | 7.2e-05 | True | 0.0156 |
| Kagoshima | 0.22213 | 4.88e-06 | 0.000161 | True | 0.0156 |
| Okinawa | 0.46117 | 1.04e-06 | 3.94e-05 | True | 0.0156 |

30/47 prefectures meet the 5% Holm threshold under the conventional year-clustered t approximation. The CSV also includes unadjusted means, adjusted predictions, standard errors, confidence intervals and classical-test sensitivity for every prefecture.

## Small-cluster bootstrap sensitivity

All 128 Rademacher year-sign patterns are evaluated after imposing each contrast's null. This is an approximate restricted residual-bootstrap diagnostic under independent clusters and symmetry assumptions. The minimum attainable two-sided p-value is 2/128 = 0.015625. Consequently no comparison can pass a 47-test Holm adjustment at 5%. This is a resolution/conservatism limit, not evidence that the regional rates are equal. Nominal significance under the cluster-t approximation should therefore not be described as robustly established by this bootstrap.

Income and spending proxies may be endogenous, and adjustment does not make a location effect causal. National food imports are common within year. Unrestricted year effects would absorb food imports; the current time trend is a modelling restriction.

## Reproduce

```bash
python scripts/_22_subregion_anova.py
```
