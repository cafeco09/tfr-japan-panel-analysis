# Japan fertility and total external food imports

This analysis examines Japan's **total food imports from all origins as one external-import variable**, alongside official national total fertility rate (TFR). The current specification has no country split and no organic-farming interaction.

Repository: https://github.com/cafeco09/tfr-japan-panel-analysis

## Hypothesis and measure

The directional hypothesis is that higher external food imports reduce fertility. Estimates remain unconstrained, and all tested specifications are reported; a hypothesis does not determine the fitted sign.

The import measure is Japan-reported UN Comtrade imports from **World (partner code 0)**, using **BEC Rev.4 category 1: food and beverages**, including primary and processed forms. It directly covers all partners. China and USA totals are not added to the World total, which would double count them. The product perimeter excludes other merchandise; this is not all-goods trade or a net-import measure.

Values are **current US dollars**, not physical food volumes, price-adjusted quantities, prefectural exposure or resident consumption. Aggregate weight fields are unavailable. See [FOOD_IMPORT_SCOPE.md](FOOD_IMPORT_SCOPE.md) for definitions and source flags.

## Updated results

Primary national sample: **2016–2024, nine annual observations**. The provisional 2025 TFR is a separate sensitivity. Adding source countries broadens coverage but does not increase the annual observation count.

| Specification | Log external-import coefficient | HC3 p-value |
|---|---:|---:|
| No time trend | −0.9474 | 0.1269 |
| Linear time trend | +0.2494 | 0.2751 |
| Quadratic time trend | +0.1261 | 0.1447 |
| First differences | +0.1560 | 0.2168 |
| One-year lag plus linear trend | −0.0100 | 0.9607 |

The negative raw association changes sign after time-trend adjustment. These results do not establish a stable negative relationship or a causal food-import effect. Non-significance does not prove that no effect exists. First-difference and lag models change the estimand and timing.

Inference is also sensitive: the negative no-trend association has lag-one HAC p = 0.017, while the positive quadratic-trend association has HAC p = 0.044. With nine years, these model-dependent p-values cannot be used selectively to confirm a hypothesis. HC3 and HAC variants, confidence intervals and provisional-rate sensitivity are included in the [full results](output/external_food_imports/EXTERNAL_FOOD_IMPORT_RESULTS.md).

## ML comparison and sensitivity

Expanding-window validation holds out four outcomes in 2021–2024, with past-only tuning and preprocessing. Import values for each outcome year are supplied, so evaluation is conditional hindcasting, not advance prediction of unknown imports.

| Model | Mean absolute TFR error |
|---|---:|
| Trend-only baseline | 0.0237 |
| OLS: total imports + trend | 0.0260 |
| Ridge | 0.0283 |
| Elastic Net | 0.0317 |
| RBF SVR | 0.1008 |
| Shallow random forest | 0.1090 |

Adding imports does not improve this small chronological comparison. Four errors cannot establish stable model rankings. [Predictive sensitivities](output/external_food_imports/predictive_sensitivity_summary.csv) evaluate ±1%, ±5% and ±10% changes in nominal import value, with support flags and leave-year-out stability checks. These responses are not causal derivatives or significance tests.

## 2026–2030 scenario projections

The [projection export](output/external_food_imports/projections_2026_2030.csv) contains flat 2025 import values, ±5% annual changes and continuation of the 2016–2025 nominal-value CAGR. Separate fits exclude/include provisional 2025 TFR.

With import values flat at 2025 levels and provisional 2025 TFR included:

| Year | OLS: imports + trend | Ridge | Elastic Net | Trend-only baseline |
|---|---:|---:|---:|---:|
| 2026 | 1.096 | 1.099 | 1.104 | 1.100 |
| 2027 | 1.056 | 1.059 | 1.066 | 1.063 |
| 2028 | 1.016 | 1.020 | 1.029 | 1.026 |
| 2029 | 0.977 | 0.981 | 0.992 | 0.989 |
| 2030 | 0.937 | 0.942 | 0.954 | 0.952 |

These are conditional extrapolations, not official forecasts or calibrated prediction intervals. Future import paths, source revisions, structural changes and model uncertainty remain unresolved. Model/scenario spread is not a confidence interval. Trees and RBF SVR extrapolate time poorly in this short dataset.

## Run the current analysis

Use a clean Python 3.11 environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_all.py
```

Alternatively use a separate Conda environment. On Windows, virtual-environment activation uses `.venv\Scripts\activate`.

The default runner validates cached World import snapshots and runs the aggregate regressions, ML checks and projections. Cached sources are reused; missing snapshots require internet access. To fetch a new Comtrade source vintage explicitly, run `python scripts/_14_external_food_imports.py --refresh` and rerun the analysis. Source updates can change results.

## Files and provenance

The optional [named-food breakdown](output/food_names/README.md) separates the aggregate into 154 HS4 food headings for 2025 and retains HS6 product-year details for 2016–2025. Soyabeans, soyabean oil, soy flour/meal and soy sauce are explicit entries. Soyabean oilcake/residues are a separately flagged non-food reference, excluded from food totals. Scope flags identify broad-classification items such as seed for sowing and possible industrial/feed use. Run `python scripts/_16_named_food_imports.py` to reproduce the named data.

- [External import series](data/external_food_imports_world_2016_2025.csv): ten annual World totals, source URLs, retrieval times and aggregation checks.
- `data/external_food_sources/`: raw Comtrade responses.
- [National TFR](data/national_tfr_2016_2025.csv): source workbook, sheet and cell references.
- [Aggregate analysis](output/external_food_imports/EXTERNAL_FOOD_IMPORT_RESULTS.md): complete specification, inference, sensitivity and projection results.
- `scripts/_14_external_food_imports.py`: World source collection and validation.
- `scripts/_15_external_food_analysis.py`: aggregate analysis.

The published World total differs from its primary-plus-processed components by approximately 0.004% in 2024 and 0.006% in 2025. These source discrepancies are flagged and retained, with a component-sum sensitivity; the main total is not silently overwritten. That sensitivity leaves the main conclusion unchanged.

## Identification limits and history

National imports vary only by year. Repeating them across prefectures does not create independent exposure shocks; annual fixed effects absorb the national main effect. Time trends impose restrictions rather than remove all confounding. Prices, exchange rates, domestic demand, reverse causality and shared demographic/economic shocks can explain associations. The current data do not identify a causal negative effect.

Earlier country-specific, organic-interaction, prefectural and synthetic analyses are retained as historical analyses and method tests. The [previous README](docs/history/README_before_world_aggregation.md) documents them. Synthetic observations are not pooled with observed data and are not relabelled as World imports. Run `python run_all.py --legacy` for the original six-stage prefectural pipeline.

## Licence

Code: [MIT](LICENSE). Data retain their original source terms. Cite the source references and repository commit used for any reported result.
