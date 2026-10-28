# Imported foods by name

Japan's imports from World, 2016–2025. Product names and codes come from UN Comtrade HS references. Products inside BEC Rev.4 food category 1 are selected using the UN's version-specific conversion tables: HS2012 for 2016, HS2017 for 2017–2021 and HS2022 for 2022–2025.

## Files

- `food_names_2025.csv`: 154 named HS4 food headings in the latest year, ranked by current-USD value.
- `named_food_products_2016_2025.csv`: 6,801 returned HS6 product-year records, including scope flags and source batch identifiers.
- `named_food_headings_2016_2025.csv`: named HS4 headings by year.
- `food_groups_2016_2025.csv`: readable food-category totals by year.
- `soyabean_products_2016_2025.csv`: soyabeans for sowing, other soyabeans, flour/meal, crude and other oil, soy sauce, and supplementary oilcake/residues.
- `source_batches.csv`: 89 API batches with query URLs and retrieval times.
- `requested_products_not_returned.csv`: requested codes with no returned record. These are not silently replaced with zero values.
- `reconciliation_to_world_food_total.csv`: named-product sums versus the separately published World food total.

## Scope and reconciliation

The broad BEC category includes some uses beyond food actually consumed by people. Sowing seed, live animals, food-industry residues, albumins/enzymes and an oral-nicotine product code are explicitly flagged. The official classification is retained for traceability; these items must not be interpreted as measured dietary consumption. Soyabean oilcake/residues (HS230400) are classified outside BEC food and are included only as a supplementary reference, excluded from food totals.

The named-product sums differ from the published BEC World total by less than 0.1% in every year. Values are not rescaled to force exact agreement. Source aggregation, conversion and coverage differences remain visible. HS6 definitions change with revision, so code-level longitudinal comparisons require care; revision and official descriptions are retained.

All values are nominal current USD. Reported net weights and estimation flags are retained at product level but are not aggregated into an assumed dietary dose. These are customs product categories, not brands, individual consumption or nutritional measurements. Prepared products may combine ingredients; soy-specific headings do not identify every processed food containing soya.

## Reproduce

```bash
python scripts/_16_named_food_imports.py
```

Source snapshots and official classification references are retained under `data/food_names_sources/` and `data/food_names_references/`. The named-food extraction does not change the existing fertility regression estimates.
