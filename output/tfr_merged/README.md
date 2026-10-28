# Prefectural TFR merged with national food imports

The merge key is calendar year. Each prefecture retains its own observed TFR. Japan's national food-import values are joined many-to-one and are identical across prefectures within each year. These imports are not measured prefectural consumption, port-level exposure or allocated local imports.

- `prefecture_food_imports_and_tfr_2016_2025.csv`: 470 prefecture-year rows, 47 prefectures and ten years. Includes provisional 2025 TFR.
- `prefecture_food_imports_and_tfr_final_2016_2024.csv`: 423 rows excluding provisional 2025 rates.

Fields include prefecture codes and English/Japanese names, year, TFR and release status, the import geography flag, published and mapped food totals, whole soyabeans and other mapped food, seven soy product series, 21 HS2 food groups, and the original TFR source URL and cell. Import values are nominal current USD from all origins. Missing returned product records remain blank in CSV and `n.a.` in the spreadsheet; they are not zero.

Whole soyabeans are HS1201, including sowing seed. Soy oil, flour and sauce remain within other mapped food. The separately reported HS230400 oilcake series is outside the food total. Aggregate, group and soy columns overlap and must not all be summed. Other mapped food equals mapped food minus whole soyabeans; the published total is not silently forced to equal the mapped total.

The supplied food workbook is the import input. TFR comes from `data/prefectural_tfr_2016_2025.csv`; names are resolved through `data/dated_source_panel_2016_2025.csv`. No income, crop-basket or organic variables from that historical panel are merged. TFR sources and release statuses are retained without re-estimation or imputation.

Although there are 470 rows, imports contain only ten distinct annual observations (nine in the final-only sample). A random row split would share annual import values between training and validation. These data do not identify a prefecture-specific import effect; year fixed effects absorb the common national import main effect.

Reproduce CSVs using `python scripts/_18_merge_food_tfr.py INPUT.xlsx PAYLOAD.json`. The JS builder imports that same input workbook, preserves its existing sheets, and adds the prefectural source records and the merged panel with formula links.
