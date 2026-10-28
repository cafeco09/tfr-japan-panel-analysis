# Current scope: total external food imports

Use one annual national proxy: Japan's total food and beverage imports from all partners, as published by UN Comtrade with Japan reporter code 392, World partner code 0 and import flow M. There is no origin split or organic-context interaction in the current analysis.

## Boundary and units

BEC Revision 4 category 1 covers primary (11) and processed (12) food and beverages, including industry-use and household-consumption subcategories. The revision is held fixed across years. This is the official product perimeter, not all agricultural commodities or all merchandise. It is not a food-safety measure, net imports or actual dietary consumption. Organic certification and chemical treatment are not distinguished.

The primary variable is published category-1 World import value in current USD. Aggregate net weights are unavailable and are not interpreted as zero imports. Values include price, currency and composition changes, not just quantities. The World total already covers China, USA and other partners; adding country totals would double count them. Standard reported imports are used under source reporting rules, without constructing a separate re-import adjustment.

## Source quality

Annual raw responses, query URLs, retrieval dates and classification flags are retained in data/external_food_sources/. Converted BEC aggregates are not relabelled as originally reported BEC records. The 2024 and 2025 published totals differ slightly from primary + processed values. Differences and reconciliation flags are exported, and the analysis tests the component sum as a sensitivity. Source totals are not changed to force reconciliation.

## Sample and interpretation

The primary national sample is 2016–2024 (nine annual observations). Provisional 2025 national TFR is a separate sensitivity. Expanding origins to World does not add time observations. Estimates are unconstrained tests of the negative-association hypothesis. Annual fixed effects absorb the national import main effect; other time controls impose assumptions and do not create exogenous variation.

Previous China/USA, organic-interaction and synthetic analyses are historical outputs. They are not the current total-import specification, and synthetic rows do not increase empirical n. The [previous country-specific scope](docs/history/FOOD_IMPORT_SCOPE_china_usa.md) is retained for traceability.

## Reproduce

```bash
python run_all.py
```

The current runner collects/validates cached World snapshots and runs the aggregate analysis. Results are in output/external_food_imports/. The original pipeline remains available with python run_all.py --legacy.

Source documentation:

- https://uncomtrade.org/docs/how-to-retrieve-data-for-world-exports-to-a-country-in-un-comtrade/
- https://uncomtrade.org/docs/intermediate-goods-in-trade-statistics/
- https://unstats.un.org/unsd/publication/SeriesM/SeriesM_53rev4e.pdf
