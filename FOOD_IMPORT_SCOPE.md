# Revised scope: food imports from China and the USA

The revised import question uses two separate country series: Japan's food imports from China and Japan's food imports from the USA. Organic farming is not part of this new import specification, and the series do not distinguish organic or non-organic certification.

## Product definition

Use UN Comtrade's BEC Revision 4 category **1: Food and beverages**, covering category 11 (primary) and category 12 (processed). Both industrial-use and household-consumption subcategories are included. This is a reproducible broad product definition, including beverages; it is not an ad hoc extension of maize, rice and soybeans. Revision 4 is held constant across years. BEC Revision 5 has a different category structure and must not be substituted using the same category number.

The product perimeter is the official BEC category, not every agricultural product or a measure of food safety, individual consumption or nutritional intake. The category labels and included uses should accompany every result.

## New source files

- `data/food_imports_china_usa_2016_2025.csv`: 20 country-year rows; total, primary and processed import values.
- `data/food_imports_china_usa_wide.csv`: 10 annual rows and two separate country variables, `china_food_import_value_current_usd` and `usa_food_import_value_current_usd`.
- `data/food_import_sources/`: annual raw Comtrade responses with source URLs, retrieval timestamps and classification flags.
- `scripts/_09_food_imports.py`: reproducible retrieval and validation; cached snapshots are reused unless `--refresh` is requested.

Importer: Japan (392). Partners: China (156) and USA (842), as defined by Comtrade. Flow: imports. Frequency: annual. Customs and transport coverage: aggregate. The source's classification-conversion flags are retained. Converted BEC aggregate rows marked `isReported=false` are not relabelled as originally reported BEC data.

Values are **current US dollars**, with the source's primary import value retained. They are not deflated volumes. The aggregate weight field is not used: zero/unavailable weight must not be interpreted as zero food imports. Total value is checked against primary + processed value for each country-year. Country-year uniqueness and complete 2016–2025 coverage are required before the final files are written.

## Analysis consequences

The existing three-crop kilogram variables cannot be renamed or interpreted as all-food imports. The earlier organic-interaction outputs remain a historical exploratory analysis; they do not estimate the revised question. The new data are not automatically substituted into those models.

These new imports still vary nationally by year. Annual fixed effects absorb their main effects in the prefectural panel. Repeating each annual total across prefectures does not create independent country-specific exposure observations. Dropping year effects leaves annual national shocks as potential confounders. A new causal effect is therefore not claimed by this data update.

Before fitting a revised effect model, specify the estimand, price/currency basis, treatment timing, source release coverage and identification strategy. China and USA series can be examined separately and jointly, but ten annual observations limit what can be learned, particularly with correlated country series, trends and lags. Additional exogenous variation or validated regional exposure would still be needed for a stronger causal design.

A separate descriptive [national comparison](output/food_import_results/UPDATED_FOOD_IMPORT_RESULTS.md) now reports both countries, time-trend sensitivity, first differences, lags and covariance sensitivity. It uses official national TFR and nine final-labelled annual rates as the primary sample. Its statistical comparisons do not resolve the identification limitations above.

## Reproduce

```bash
python scripts/_09_food_imports.py
```

Use `--refresh` only to fetch a new source vintage. The public API is rate limited; the script makes sequential requests and retries HTTP 429 responses. The existing `run_all.py` remains unchanged, so the old analysis is not silently presented as the revised one.

## Sources

- UN classification manual: https://unstats.un.org/unsd/publication/SeriesM/SeriesM_53rev4e.pdf
- UN Comtrade category definitions: https://uncomtrade.org/docs/intermediate-goods-in-trade-statistics/
- Source API URLs and retrieval dates are recorded in every exported country-year row and raw response.
