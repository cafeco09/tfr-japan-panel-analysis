# Data Sources

This repository retains source URLs and cell references per row. The table
below summarises the primary sources; for the exact URL and cell of any
single observation, consult the corresponding `*_source` / `*_source_cell`
column in `data/dated_source_panel_2016_2025.csv`.

## Primary sources

| Variable | Provider | Dataset | Vintage | URL |
|---|---|---|---|---|
| TFR (2016–2024) | e-Stat / MHLW | Vital statistics, prefectural period TFR | 2023 release | https://www.e-stat.go.jp/en/stat-search/file-download?fileKind=1&statInfId=000040320380 |
| TFR (2025, provisional) | MHLW | Monthly vital statistics, Table 9 | Provisional | https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai25/xls/R7toukeihyou.xlsx |
| Prefectural income | ESRI / Cabinet Office | Prefectural accounts, Table 7 | FY2023 (some FY2022) | https://www.esri.cao.go.jp/jp/sna/data/data_list/kenmin/files/contents/tables/2023/soukatu7.xlsx |
| Eating out 2016–2023 | e-Stat | Family Income & Expenditure Survey | Annual | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031586374&fileKind=0 (representative; yearly variants in CSV) |
| Eating out 2024 | e-Stat | Family Income & Expenditure Survey | Annual | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040297542&fileKind=4 |
| Eating out 2025 | e-Stat | Family Income & Expenditure Survey | Annual | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040424637&fileKind=4 |
| Organic farming | e-Stat | 2020 Census of Agriculture, Table Ⅱ57 | 2020 census | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032101935&fileKind=0 |
| Gardening | e-Stat | 2021 Survey, Table a093_1 | 2021 survey | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032223420&fileKind=0 |
| China imports | UN Comtrade | HS 1005, 1006, 1201; reporter JP; partner CN (156) | Annual | https://comtradeapi.un.org/public/v1/preview/C/A/HS?period=YYYY&reporterCode=392&cmdCode=1005%2C1006%2C1201&flowCode=M&partnerCode=156%2C842&partner2Code=0&customsCode=C00&motCode=0&maxRecords=500 |
| USA imports | UN Comtrade | HS 1005, 1006, 1201; reporter JP; partner US (842) | Annual | (same URL, partnerCode includes 842) |
| Population denominator | World Bank | Indicator `SP.POP.TOTL`, country JPN | Last updated 2026-10-08 | https://api.worldbank.org/v2/country/JPN/indicator/SP.POP.TOTL?date=2024:2025&format=json |

## Crop basket definition

The "three crops with mass" basket is defined as:

- **Maize** — HS 1005
- **Rice** — HS 1006
- **Soybeans** — HS 1201

Imports are reported by UN Comtrade as total kilograms per year; per-resident
values divide by the World Bank population denominator.

## Notes on vintage and reliability

- **TFR 2025 is provisional**; final prefectural rates are scheduled for November 2026.
- **Income is available through FY2023** (published 2023 release). FY2024–FY2025 are not yet in the checked harmonised ESRI release, and no imputation is applied.
- **Imports vary only by year** (national totals). They are not prefectural observations and cannot be separated from national time shocks in prefecture FE models.
- **Organic (2020) and gardening (2021) are single snapshots**; they are constant within prefecture across 2016–2025 and identified only in cross-section.
- **Five 2023 income values are synthetic** (Ishikawa, Nara, Tokushima, Kagawa, Miyazaki) and flagged in `synthetic_income_sensitivity_only.csv`; dropping them leaves headline results essentially unchanged.

## Citing the data

If you reuse these files, cite the original providers:

- Statistics Bureau of Japan / MHLW (e-Stat)
- Economic and Social Research Institute (ESRI), Cabinet Office
- World Bank (World Development Indicators)
- United Nations Comtrade Database