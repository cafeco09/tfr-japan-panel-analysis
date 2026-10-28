# SYNTHETIC DATA — NOT OBSERVED JAPANESE DATA

Generated with seed 20261028. All outcomes, country import paths, prefecture identifiers and common shocks in these files are synthetic.

## Contents

- `SYNTHETIC_food_import_panel.csv`: 5,640 rows = four scenarios × 47 synthetic prefectures × 30 synthetic periods.
- `SYNTHETIC_national_import_series.csv`: separate China and USA values per synthetic period and scenario.
- `SYNTHETIC_estimator_demonstration.csv`: fitted and known coefficients, with and without the simulated common-shock control.
- `SYNTHETIC_generation_metadata.json`: seed, calibration source, every chosen distributional parameter and limitations.

## Four scenarios

1. **Null with unrelated common shocks:** both true food-import effects are zero.
2. **Null with positive shared confounding:** true effects remain zero, but an omitted shared shock tracks the China import path positively.
3. **Null with negative shared confounding:** true effects remain zero, with the opposite shared-shock relationship.
4. **Known-effect benchmark:** chosen true log-import coefficients are China −0.08 and USA +0.04. These values are arbitrary method-testing inputs, not findings about either country's food.

The same underlying innovations and prefectures are reused across scenarios to make contrasts transparent. Scenarios are not independent datasets. The sample is not filtered to obtain a preferred sign or significant result.

## Data-generating process

Synthetic TFR equals 1.5 + a prefecture intercept − 0.008 × time + the two chosen import effects + a heterogeneous common-shock contribution + serially correlated idiosyncratic error. China and USA log-import paths have correlated innovations, persistence and chosen linear trends. Only mean log-import value levels are calibrated to the observed broad-food series; persistence, effects, noise and trends are assumed.

There is **no organic interaction**. Import variables remain national: each synthetic prefecture sees the same origin-specific value in a given synthetic period. The generator does not invent measured regional exposure. Synthetic periods are numbered 1–30, with no real-calendar interpretation; synthetic IDs begin `SYN-P` and do not identify real prefectures.

## What this can and cannot establish

These data support code testing and demonstrations of confounding. The estimator table includes an **oracle** regression controlling the exact simulated shock contribution. That variable is deliberately known in the simulation; it is not available in the real data. A single seeded realisation illustrates behaviour and does not estimate repeated-sampling bias, power or confidence-interval coverage.

Synthetic observations must not be pooled with real observations to increase empirical sample size, establish causality or turn exploratory findings into confirmatory evidence. Generated truths are design assumptions. More synthetic prefectures do not create more actual national import shocks.

## Reproduce

From the repository root:

```bash
python scripts/_11_synthetic_food.py --years 30 --prefectures 47 --seed 20261028
```

Change years, prefectures and seed to test other simulation sizes. Source data and the empirical analysis are not modified.
