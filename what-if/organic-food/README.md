# Organic-food what-if scenarios, 2026–2050

![Annual TFR and food quantities](results/annual_organic_scenarios.png)

**Scenario assumption:** From 2026, all imports represented in this model are treated as organic, regardless of their unknown historical classification. Historical records are not reclassified. The modelled physical basket is China/USA maize, rice and soybeans, not all countries or all food imports. Results must retain this scope limitation.

**Organic status does not provide an estimated fertility effect.** The historical regression supplies the background association with time and general crop-import mass. Additional organic benefits are imposed scenario assumptions, explicitly separate from the historical volume coefficient. No final TFR is fixed or used to calibrate these effects.

## What is compared each year

The main output is one annual row per scenario for every year from 2026 through 2050, including physical import volume, organic import volume, domestic organic production, estimated background TFR and simulated TFR.

The background comes from the observed-data age-rate models in `background/`: primary fits use nine years, 2016–2024, and provisional 2025 rates provide the starting point. Future general crop-import volume is held constant, decreases 1% annually or increases 1% annually. The corresponding historical volume association remains fixed as a control in each comparison. It is not re-estimated using synthetic outcomes.

Within a given volume-control path, organic imports equal 100% of that modelled import mass from 2026. Under the constant-volume case, this is approximately **145.95 kg/person/year**. Domestic organic production is assumed to increase from a reference of 5 kg/person/year in 2025 to 100 in 2050. That reference and the production path are unmeasured assumptions, not historical organic observations. Kilograms may include crop uses such as feed in the underlying import data; they are not measured human consumption or pesticide exposure. No money-to-mass or hectares-to-yield conversion is made.

## Organic response assumptions

Four cases apply an additional −0.001, 0, +0.001 or +0.004 TFR units per effective kg/person/year, using the same response for domestic and imported organic food. Thus 10 effective additional kg/person/year correspond to −0.01, 0, +0.01 or +0.04 TFR units under the respective assumptions. These values are illustrative, not estimates or a complete plausible range.

The import term represents a possible benefit or harm relative to **continuation of the unknown historical mix**. It is applied to all future organic imports; this does not assert that historical imports were entirely non-organic. The domestic term applies only to assumed additional domestic organic production above the 5 kg reference. Historical organic shares, dose–response relationships and actual exposure are not inferred.

Both terms use the arbitrary gradual-response rule `E[t]=E[t−1]+(quantity[t]−E[t−1])/3`, starting with zero incremental effect at the end of 2025. The lag is not a biological estimate. The scenario TFR is:

```
estimated background TFR
  + assumed response × effective organic import quantity
  + assumed response × effective additional domestic organic quantity
```

Internally, each annual uplift is allocated proportionally across the estimated fertility-rate contributions so that their sum equals the reported annual TFR. This allocation is another assumption, not an estimated age-specific organic response. Annual results are the primary presentation.

## Emergent results

| Assumed response per effective kg/person/year | 2050 TFR: imports −1%/year | Imports constant | Imports +1%/year |
|---|---:|---:|---:|
| −0.001 | 0.445 | 0.417 | 0.381 |
| 0 | 0.648 | 0.650 | 0.652 |
| +0.001 | 0.852 | 0.884 | 0.923 |
| +0.004 | 1.461 | 1.584 | 1.736 |

The zero-response case reproduces the estimated background exactly. The smaller positive assumption slows the net decline but does not regain the 2025 TFR by 2050. The larger assumption gives an end-point above the historical rate in all three volume paths, without a target being specified. This does not always mean uninterrupted recovery: under constant imports the larger-benefit path has a temporary rise, subsequent decline and a sustained annual rise only from 2044. Annual paths, rather than end-points alone, should be inspected.

These outcomes demonstrate the consequences of the chosen assumptions. They do **not** establish that changing organic food supply would cause these fertility outcomes. No p-values on invented outcomes are used to validate the assumptions. There are no calibrated probabilities or forecast intervals. Physical capacity, food quality, food waste, substitution, competing fertility determinants, future population and production feasibility are not modelled.

Because organic imports equal total modelled imports after 2025, those two regressors would be perfectly collinear in future-only data. We therefore hold the historical volume coefficient fixed and layer the explicit organic contrast on top; separate future organic and volume coefficients are not estimated.

## Files and reproduction

- `results/annual_food_volumes_and_tfr_2026_2050.csv`: 300 annual scenario rows with quantities and contributions.
- `results/year_by_year_constant_volume_comparison.csv`: 25 annual rows comparing all four response assumptions.
- `results/emergent_2050_results.csv`: end-points and first sustained-rise years; no target used.
- `results/supporting_age_contribution_reconciliation.csv`: internal aggregation checks, not the main presentation.
- `assumptions.json`, `validation.txt`, and PNG/SVG graphs.

From the repository root:

```bash
python -m pip install -r what-if/organic-food/requirements.txt
python what-if/organic-food/fit_background.py
python what-if/organic-food/run_scenarios.py
```

Both scripts run locally without downloading data. The first estimates the background from observed inputs; the second generates annual scenarios. Neither uses a fertility target.

Suggested results wording: **“For 2026–2050, the modelled imports were assumed to be organic, while general import-volume paths were retained as controls. Fertility outcomes emerged from the estimated historical background and explicitly assumed organic-food responses, without specifying a final TFR. Recovery in the larger-benefit cases reflects those assumptions and is not an estimated causal benefit of organic food.”**

## Input provenance

The two national fertility CSVs in `inputs/` retain MHLW URLs, sheets and cell references. Age contributions for 2006–2021 come from the [2022 workbook](https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai22/xls/R4zu.xlsx), sheet 図１～２データ; 2022–2025 come from the [2025 workbook](https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai25/xls/R7zuhyou.xlsx), sheet 図表2-4. National TFR comes from the [2025 statistical workbook](https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai25/xls/R7toukeihyou.xlsx), sheet 第2表. The retained 2025 vintage is provisional. Age contributions are sums of single-age rates, not rates to multiply by five. The 2025 sum is 1.1351, versus published rounded TFR 1.14. The dated source panel retains physical crop masses and source-estimate flags; see [Data Sources](../../Data_Sources.md).
