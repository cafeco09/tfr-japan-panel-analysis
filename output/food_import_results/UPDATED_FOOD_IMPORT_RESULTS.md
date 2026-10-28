# Broad food imports from China and USA: updated descriptive results

28 October 2026. Country series are separate. No organic term is included.

## Conclusion

The 2016–2024 data do not establish a reliable association between national fertility and broad food-import values from either origin. Signs, magnitudes and uncertainty depend on the time specification. Non-significance is not evidence that an effect is absent. The new analysis does not support a causal claim.

## Measurement and sample

The outcome is official national TFR from MHLW Table 2, cells Q120–Q129 of the archived workbook, not the unweighted mean of prefectural rates. The primary sample excludes the provisional 2025 rate: nine annual observations, 2016–2024. Including 2025 gives ten observations and is a separate sensitivity. National imports are not duplicated across prefectures to inflate the information count.

Imports use UN Comtrade BEC Rev.4 category 1 (food and beverages), covering primary and processed forms. China and USA values enter as separate log covariates. They are nominal US-dollar import values: prices, exchange rates, quantities and product composition can all change the series. They do not measure prefectural or individual food exposure, organic status or chemical treatment.

## Joint-country models: primary sample

Both country covariates are included together. HC3 standard errors and t reference distributions are reported below. A coefficient is the TFR difference associated with one log-point higher import value conditional on included terms; multiply by log(1.10) for a 10% value difference. Causal or biological interpretations are not justified.

| spec | country | coefficient | se | p | ci_low | ci_high | n | residual_df |
|---|---|---|---|---|---|---|---|---|
| joint_no_trend | China | -0.5503 | 1.4268 | 0.7130 | -4.0414 | 2.9409 | 9.0000 | 6.0000 |
| joint_no_trend | USA | 0.3013 | 1.1492 | 0.8019 | -2.5106 | 3.1132 | 9.0000 | 6.0000 |
| joint_linear_trend | China | 0.0225 | 0.2322 | 0.9267 | -0.5743 | 0.6193 | 9.0000 | 5.0000 |
| joint_linear_trend | USA | 0.1976 | 0.1086 | 0.1284 | -0.0815 | 0.4767 | 9.0000 | 5.0000 |
| joint_quadratic_trend | China | 0.0916 | 0.1893 | 0.6538 | -0.4339 | 0.6171 | 9.0000 | 4.0000 |
| joint_quadratic_trend | USA | 0.0680 | 0.1529 | 0.6795 | -0.3564 | 0.4924 | 9.0000 | 4.0000 |
| joint_first_differences | China | -0.0173 | 0.2641 | 0.9504 | -0.6962 | 0.6617 | 8.0000 | 5.0000 |
| joint_first_differences | USA | 0.1832 | 0.1291 | 0.2149 | -0.1486 | 0.5150 | 8.0000 | 5.0000 |
| joint_one_year_lags | China | -0.1752 | 0.1906 | 0.4099 | -0.7044 | 0.3539 | 8.0000 | 4.0000 |
| joint_one_year_lags | USA | 0.1649 | 0.1921 | 0.4390 | -0.3684 | 0.6981 | 8.0000 | 4.0000 |

Inference-method sensitivity is material: for USA in the joint linear-trend primary model, HC3 gives p = 0.128 while HAC with one lag gives p = 0.021. With nine observations, the smaller HAC p-value is not a reliable basis for selecting a significant result. The country coefficients are the same under both covariance methods; only estimated uncertainty changes.

## Including provisional 2025

| spec | country | coefficient | se | p | n |
|---|---|---|---|---|---|
| joint_linear_trend | China | 0.0962 | 0.2113 | 0.6647 | 10.0000 |
| joint_linear_trend | USA | 0.1522 | 0.1198 | 0.2509 | 10.0000 |

## Uncertainty and identification

- Nine annual observations give only five residual degrees of freedom in the joint linear-trend model and four in the quadratic-trend model. Precision and diagnostics are fragile.
- HC3 addresses heteroskedasticity and leverage, not serial dependence. HAC with one lag is also exported; with so few observations it is not a dependable asymptotic remedy. Neither is an exact finite-sample test.
- Linear and quadratic trends impose different restrictions on unobserved national time patterns. Full year effects would absorb both import series, making their main effects unidentifiable. A high R² driven by the fertility trend is not evidence that imports explain fertility.
- The series share national demand, exchange-rate and food-price determinants. Reverse causality and omitted economic/demographic factors remain possible. Lags and first differences do not automatically address these problems.
- All predefined country-only, joint, trend, difference and lag comparisons, both covariance choices, and provisional-rate sensitivity are exported. They are exploratory specifications; do not select a conclusion using whichever p-value is smallest.
- Leave-one-year-out estimates are exported to reveal influence. They are dependent diagnostics, not independent replications.

## Moving towards stronger evidence

1. Extend comparable historical national food series and harmonised TFR data, using a fixed definition and consistent source vintages. More years improve estimation but do not remove endogeneity.
2. Measure price/quantity changes appropriately. Deflate values or use a documented volume index; converting currencies alone is not deflation. State whether the estimand concerns spending, physical imports or actual consumption.
3. Obtain validated regional exposure or a defensible external supply/policy shock, with explicit assumptions about other channels. National time-series controls cannot substitute for an identification strategy.
4. Specify the hypothesis, estimand, lag window, confounders, main model and sensitivity set before further result-driven model selection. Historical checks already inspected cannot be made confirmatory by relabelling them as pre-specified.
5. Reserve a genuinely new period or dataset for validation and, if the aim is individual fertility or health mechanisms, obtain appropriately linked individual exposure/outcome data.

## Reproduce

```bash
python scripts/_10_food_import_results.py
```

`national_food_import_models.csv` contains all numerical results. `analysis_data.csv`, `leave_one_year_out.csv` and `source_and_method.json` retain the analysis sample, influence checks and provenance.

## Sources

- MHLW national TFR workbook: https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai25/xls/R7toukeihyou.xlsx
- TFR provisional-rate note: https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai25/dl/tfr.pdf
- Comtrade query URLs and retrieval dates: `data/food_import_sources/`.
