# What if our food became organic?

**If organic food had the bigger benefit we tested, the simulation showed fertility rising from about 1.14 to 1.58 by 2050 - roughly 39% higher.** It reached about 1.56 by 2030 and stayed close to that higher level. No final fertility target was fixed in advance.

This exercise asks what might follow if the modelled imports became organic from 2026 and more organic food were grown in Japan. It uses the historical fertility pattern as a starting point and tries different possible benefits from that food change.

## What we saw

| If organic food provides... | Fertility rate in 2050 |
|---|---:|
| No added benefit | 0.65 |
| A small benefit | 0.88 |
| A bigger benefit | 1.58 |

The small benefit kept fertility above the no-benefit path in every year, although it did not fully offset the longer-term decline. The bigger benefit produced recovery and a broad plateau around 1.58, with a small dip and later rise. In this model, the benefit's size made the difference between slowing the decline and turning it around.

![Yearly fertility paths and food quantities](results/annual_organic_scenarios.png)

**These are results under chosen assumptions.** The historical records do not tell us the fertility benefit of switching to organic. The exercise helps identify what would be worth measuring and testing, rather than demonstrating a proven way to raise fertility.

## What changed in our imagined future

- **Imported food becomes organic in 2026.** The main comparison keeps the amount imported at about 146 kg per person each year, while retaining the estimated historical relationship with general import volume as a control.
- **More organic food is grown in Japan.** It rises from an assumed 5 kg per person in 2025 to 100 kg in 2050. Those production amounts are scenario choices, not measured historical organic output.
- **The possible benefit builds over time.** Imported and locally grown organic food receive the same assumed benefit per kg. We try small, bigger, zero and negative responses.
- **The final fertility rate is calculated, not chosen.** Each annual result follows from the background pattern, food quantities and stated response.

The available physical import records cover maize, rice and soybeans from China and the USA, including possible feed uses. They are not all food or a measure of what people ate. We assume this modelled basket becomes organic after 2025; its historical organic share stays unknown.

## How big a benefit did we try?

In the small-benefit version, every 10 kg per person per year covered by the assumption eventually adds **0.01** to the fertility rate. In the bigger-benefit version it adds **0.04**. These sizes are inputs chosen for exploration, not measured effects.

For imports, the possible benefit is compared with continuing the unknown historical food mix. For food grown in Japan, it applies to extra production above the assumed 5 kg starting amount. Each year, one third of the remaining change takes effect, allowing the response to build gradually.

The fertility rate, or TFR, describes how many children a woman would have if one year's birth rates continued through her childbearing years.

## What should we investigate next?

1. Measure organic food quantities separately from general imports and record whether the crops are used as human food.
2. Find out how much reaches different places and households, rather than treating national trade as everyone's diet.
3. Test whether the proposed fertility benefit appears in real reproductive-outcome data.
4. Check the land, yields, costs and distribution needed for the production path explored here.

## Explore the full results

- [Every year, 2026-2050](results/year_by_year_constant_volume_comparison.csv): the main constant-import comparison.
- [All annual food quantities and fertility outcomes](results/annual_food_volumes_and_tfr_2026_2050.csv): 300 rows across the assumptions.
- [2050 results and timing of sustained rises](results/emergent_2050_results.csv).
- [Exact assumptions](results/assumptions.json) and [calculation checks](results/validation.txt).

<details>
<summary>Other import paths and the negative-response check</summary>

| Assumed response per effective kg/person/year | Imports fall 1%/year: TFR in 2050 | Imports constant | Imports rise 1%/year |
|---|---:|---:|---:|
| -0.001 | 0.445 | 0.417 | 0.381 |
| 0 | 0.648 | 0.650 | 0.652 |
| +0.001 | 0.852 | 0.884 | 0.923 |
| +0.004 | 1.461 | 1.584 | 1.736 |

These are different assumptions, not probability ranges. Under constant imports, the bigger-benefit path rises at first, dips slightly and begins a sustained annual rise from 2044. End-points alone do not describe every year's path.

</details>

<details>
<summary>Calculation method and data boundaries</summary>

The historical background is fitted on nine annual observations, 2016-2024, using observed fertility-rate contributions and physical crop imports. Provisional 2025 rates provide the starting point. Future annual TFR is obtained by summing projected fertility-rate contributions and adding the assumed organic response, allocated proportionally across those contributions. Neither the organic response nor its allocation is an estimated historical organic-food effect.

The gradual-response rule is `E[t] = E[t-1] + (quantity[t] - E[t-1]) / 3`, starting with zero added effect at the end of 2025. The import quantity is all modelled organic imports; the domestic quantity is the increase above the assumed 5 kg reference.

Organic imports equal total modelled imports in these future scenarios. Their separate effects therefore cannot be estimated from those years. The historical general-volume coefficient is held fixed and the organic contrast remains explicit. Physical production capacity, diets, costs, population change and competing fertility determinants are not modelled; there are no calibrated forecast intervals or policy-success probabilities.

Source CSVs in `inputs/` retain URLs, worksheets and cell references. Age contributions for 2006-2021 come from the [MHLW 2022 workbook](https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai22/xls/R4zu.xlsx), sheet 図１～２データ; 2022-2025 come from the [2025 workbook](https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai25/xls/R7zuhyou.xlsx), sheet 図表2-4. National TFR comes from the [2025 statistical workbook](https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai25/xls/R7toukeihyou.xlsx), sheet 第2表. The retained 2025 vintage is provisional. Published age contributions sum to 1.1351 in 2025, which rounds to 1.14; do not multiply these contributions by five. See [Data Sources](../../Data_Sources.md) for the crop masses and source-estimate flags.

</details>

## Run the exercise

From the repository root:

```bash
python -m pip install -r what-if/organic-food/requirements.txt
python what-if/organic-food/fit_background.py
python what-if/organic-food/run_scenarios.py
```

Both scripts use the supplied inputs locally. The first estimates the historical background; the second produces the yearly what-if results. Neither uses a fertility target.
