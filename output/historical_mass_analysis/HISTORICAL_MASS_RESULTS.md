# Historical food-volume analysis

Actual trade mass replaces nominal spending as the main predictor in this supplementary analysis. Maize (HS1005), rice (HS1006) and soybeans (HS1201) are modelled separately and as a combined basket. The primary origin scope is China plus the USA; World and individual-country fits are secondary. This is not a mass reconstruction of all-world, all-food BEC imports. Earlier broad-food dollar results remain separate.

## National results: 2016–2024

Nine published national TFR observations; each primary regression includes a linear time trend and one log physical-volume predictor. Volumes are kg per resident per year. Effects below correspond to 10% more physical mass. HC3 uses a t reference with six residual degrees of freedom.

| product | tfr_change_for_10pct | hc3_p | holm_p_primary_family | hac1_p |
|---|---|---|---|---|
| basket | 0.0038 | 0.6802 | 1.0000 | 0.4807 |
| maize | 0.0025 | 0.7667 | 1.0000 | 0.5643 |
| rice | 0.0011 | 0.9084 | 1.0000 | 0.7721 |
| soybeans | 0.0185 | 0.0768 | 0.3073 | 0.0165 |

No primary HC3 result is significant at 5%, before or after the four-test Holm correction. Soybeans have a positive association, with HC3 p = 0.0768 and Holm p = 0.3073. HAC1 gives p = 0.0165 for this same positive association; this inference sensitivity is retained rather than selecting the smaller p-value. Joint-crop models are also exported, with only four residual degrees of freedom.

## Prefectural regressions with controls

The primary balanced sample has 329 rows: 47 prefectures over 2016–2022. Controls are prefecture indicators, a common linear time trend, observed log prefectural income per resident and log capital-city eating-out spending. No synthetic incomes are used. Seven independent annual exposure values are repeated across prefectures; 329 rows do not create 329 import shocks.

| product | tfr_change_for_10pct | year_cluster_p | wild_cluster_p | holm_wild_p_primary_family |
|---|---|---|---|---|
| basket | 0.0112 | 0.0008 | 0.2188 | 0.8125 |
| maize | 0.0090 | 0.0007 | 0.2031 | 0.8125 |
| rice | -0.0015 | 0.7791 | 0.7500 | 1.0000 |
| soybeans | -0.0296 | 0.2136 | 0.6250 | 1.0000 |

The basket and maize are positively associated with TFR under conventional year clustering, but the restricted wild-cluster diagnostic does not confirm either at 5%. Rice and soybeans are negative in this balanced sample but also unsupported under this diagnostic. The bootstrap enumerates 128 Rademacher sign patterns, is an approximate few-cluster diagnostic rather than an exact randomisation test, and does not resolve serial dependence.

### Complete-case extension through 2023

This secondary sample has 371 rows and eight annual clusters; five prefectures lack observed income in 2023. It is not a balanced extension and involves no imputation.

| product | coefficient | year_cluster_p | wild_cluster_p |
|---|---|---|---|
| basket | 0.1371 | 0.0001 | 0.0078 |
| maize | 0.1147 | 0.0001 | 0.0156 |
| rice | 0.1133 | 0.0196 | 0.1250 |
| soybeans | 0.2233 | 0.0192 | 0.1484 |

The extended sample gives positive basket and maize coefficients, with unadjusted wild p = 0.0078 and 0.0156. These positive associations should be reported, while retaining the sample sensitivity and small number of years. Soybeans change from negative in the balanced sample to positive in the extension. The extension is secondary and its displayed p-values are not the primary four-test family. Controls and statistical significance do not establish causality.

![Physical-volume effects and inference sensitivity](physical_volume_coefficients.png)

## Matched volume versus value comparison

Dollar comparisons use exactly the same three crops, origins, annual rows and population denominator, in current USD per resident. Thus price/value and physical quantity can be compared without changing the basket. This matched-value specification is distinct from the previous broad BEC food-dollar model.

| metric | product | coefficient | hc3_p |
|---|---|---|---|
| physical_mass | basket | 0.0397 | 0.6802 |
| physical_mass | maize | 0.0259 | 0.7667 |
| physical_mass | rice | 0.0120 | 0.9084 |
| physical_mass | soybeans | 0.1940 | 0.0768 |
| matched_value | basket | 0.0598 | 0.2309 |
| matched_value | maize | 0.0474 | 0.2370 |
| matched_value | rice | 0.0170 | 0.8029 |
| matched_value | soybeans | 0.0353 | 0.5259 |

Four expanding held-out years (2021–2024) give MAE 0.02370 for trend only, 0.02632 for the physical basket and 0.03616 for the matched-value basket. Mass improves on the matched dollar model but does not beat trend only. These checks supply realised same-year imports and are conditional predictions, not operational forecasts.

## Data quality and interpretation

UN Comtrade net-weight records were collected directly, with current dollar values retained only for comparison. All 90 origin-product-year masses are present; missing weights are never zero-filled, and money is never converted into kilograms. All 20 refreshed China/USA annual basket totals exactly match the retained historical masses.

Five of ten combined China/USA annual baskets contain at least one source-estimated weight, including four of nine primary national years. China alone has one flagged year; USA four; every World annual basket has at least one flagged component. Source estimates are retained and labelled, not presented as unestimated measurements. Flags and individual component weights are exported.

Population denominators preserve the existing source-panel vintage, reconstructed through and checked against both countries’ total/per-resident identities. This is not a fresh population-vintage update. Each total is divided by that denominator once; World is never added to China and USA.

These quantities can include feed and processing uses. They are not measured household diets, pesticide exposure or prefectural import exposure. Historical organic status remains unknown. Unrestricted year effects absorb the national import main effects; time-trend models impose restrictions and cannot remove all shared national shocks. The organic what-if scenarios remain separate assumptions and are not recalibrated to claim a benefit from these historical associations.

## Reproduction and outputs

From the repository root:

```bash
python scripts/_32_crop_mass_data.py
python scripts/_33_historical_mass_regressions.py
```

The collector reuses saved raw responses by default; `--refresh` explicitly requests a new vintage. Analysis runs offline from the supplied CSVs. Dependencies: NumPy, pandas, SciPy, statsmodels and matplotlib. National, controlled, joint-crop, country/World, provisional-2025, level-per-10kg, leave-year-out and held-out results are all retained in this folder. See [methods](methods.json), [data sources](../../Data_Sources.md) and [component records](../../data/crop_mass_components_2016_2025.csv).
