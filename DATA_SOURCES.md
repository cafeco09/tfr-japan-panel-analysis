# Data sources

Documentation checked on **28 October 2026**. This page describes the sources actually retained in the repository and distinguishes the current all-country food analysis from historical country/crop analyses. This documentation update does not refresh observations or change regression results.

Observation years, accounting years, publication dates and API retrieval dates are different concepts. In particular, the prefectural TFR source below was published on 16 September 2025, and the FY2023 income tables were posted in 2026; neither should be labelled a "2023 release".

## Where to find observation-level provenance

| Data | Retained file | Source fields or references |
|---|---|---|
| Prefectural TFR | [data/prefectural_tfr_2016_2025.csv](data/prefectural_tfr_2016_2025.csv) | `tfr_source`, `tfr_source_cell`, `tfr_release_status` |
| National TFR | [data/national_tfr_2016_2025.csv](data/national_tfr_2016_2025.csv) | `source_url`, `source_sheet`, `source_cell`, `release_status` |
| Income, eating-out expenditure and historical snapshots | [data/dated_source_panel_2016_2025.csv](data/dated_source_panel_2016_2025.csv) | Variable-specific source URLs, cells, years, status and measure notes; fields are not populated for every historical variable/year |
| Current World food aggregate | [data/external_food_imports_world_2016_2025.csv](data/external_food_imports_world_2016_2025.csv) | `source_url`, `retrieved_utc`, classification, weight and reconciliation flags; raw replies in [data/external_food_sources/](data/external_food_sources/) |
| Named food products and groups | [output/food_names/](output/food_names/) | `source_batch_id` joins to [source_batches.csv](output/food_names/source_batches.csv), containing the full query URL and retrieval time for each of 89 batches |
| HS classifications and food conversion | [data/food_names_references/](data/food_names_references/) | Official spreadsheets, H4/H5/H6 product-name dictionaries, conversion CSV and [reference_sources.json](data/food_names_references/reference_sources.json) |
| Historical China/USA broad-food series | [data/food_imports_china_usa_2016_2025.csv](data/food_imports_china_usa_2016_2025.csv) | Origin-specific values and source/retrieval fields; raw BEC replies in [data/food_import_sources/](data/food_import_sources/) |

The machine-readable [source catalogue](data/source_catalogue.csv) collects retained URLs and source roles. The files above remain authoritative for the exact observation, cell, product or batch.

## Current primary sources

| Variable | Original provider | Dataset and coverage | Vintage/status | Official source |
|---|---|---|---|---|
| Prefectural TFR, 2016–2024 | Ministry of Health, Labour and Welfare (MHLW), via e-Stat | Vital Statistics, final data, Volume 1, Table 4-5: trends in total fertility rates by prefecture | Source table covers 2024 and historical years; published **16 September 2025**, not a 2023 release | [Metadata](https://www.e-stat.go.jp/en/stat-search/files?stat_infid=000040320380); [CSV](https://www.e-stat.go.jp/en/stat-search/file-download?fileKind=1&statInfId=000040320380) |
| Prefectural TFR, 2025 | MHLW | 2025 annual provisional Vital Statistics report, Table 9; original sheet/cell retained per prefecture | **Provisional** in the retained source; excluded from final-only samples | [Report](https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai25/index.html); [workbook](https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai25/xls/R7toukeihyou.xlsx) |
| National TFR, 2016–2025 | MHLW | Same provisional-report workbook, Table 2 (`第2表`), cells Q120–Q129 | 2016–2024 historical rates marked final in the analysis; 2025 provisional. National TFR is not an average of prefectural TFRs | [Workbook](https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai25/xls/R7toukeihyou.xlsx); archived as [mhlw_2025_provisional_tables.xlsx](data/national_tfr_sources/mhlw_2025_provisional_tables.xlsx) |
| Prefectural income per resident | Economic and Social Research Institute (ESRI), Cabinet Office | Prefectural Accounts, summary Table 7; nominal JPY per resident | FY2023 table family, posted **7 August 2026**, covers 42 prefectures; FY2022 table family supplies earlier observations for five prefectures. Table-family years are accounting vintages, not publication years | [Release/coverage page](https://www.esri.cao.go.jp/jp/sna/sonota/kenmin/kenmin_top.html); [FY2023 Table 7](https://www.esri.cao.go.jp/jp/sna/data/data_list/kenmin/files/contents/tables/2023/soukatu7.xlsx); [FY2022 Table 7](https://www.esri.cao.go.jp/jp/sna/data/data_list/kenmin/files/contents/tables/2022/soukatu7.xlsx) |
| Eating-out expenditure, 2016–2025 | Statistics Bureau of Japan, via e-Stat | Family Income and Expenditure Survey; annual expenditure by the prefectural capital/survey city | Annual tables; nominal JPY per household. This is a **city-level household-survey proxy**, not measured prefecture-wide spending | Full year-specific URLs are listed below and in `eating_out_source`; the source city and cell are retained per row |
| **Total external food imports, 2016–2025** | United Nations Comtrade | Japan reporter 392, **World partner 0**, flow M, BEC Rev.4 category 1 (food and beverages), with categories 11/12 as reconciliation components | Annual source snapshots retrieved 28 October 2026; **current USD**, not physical quantities | [Example 2025 API query](https://comtradeapi.un.org/public/v1/preview/C/A/B4?period=2025&reporterCode=392&cmdCode=1%2C11%2C12&flowCode=M&partnerCode=0&partner2Code=0&customsCode=C00&motCode=0&maxRecords=500); each exact annual URL is retained in the aggregate CSV |
| **Named food imports, 2016–2025** | United Nations Comtrade | HS6 product records for Japan imports from World; HS4 names and HS2 food groups derived from the retained product records | HS2012/H4 for 2016, HS2017/H5 for 2017–2021, HS2022/H6 for 2022–2025; API retrieval times retained per batch | [Full API queries](output/food_names/source_batches.csv); [raw replies](data/food_names_sources/); [named-product methodology](output/food_names/README.md) |
| **Food classification perimeter** | United Nations Statistics Division (UNSD) | Classification by Broad Economic Categories, Revision 4, and version-specific HS-to-BEC4 conversion tables | Category 1 includes primary and processed food/beverages and some non-dietary uses; classification revision is retained | [BEC Rev.4 manual](https://unstats.un.org/unsd/publication/SeriesM/SeriesM_53rev4e.pdf); conversion-table URLs below |
| **Official food/product names** | UN Comtrade | H4 (HS2012), H5 (HS2017) and H6 (HS2022) reference dictionaries | Revision-specific names, retained in local JSON files | [H4](https://comtradeapi.un.org/files/v1/app/reference/H4.json), [H5](https://comtradeapi.un.org/files/v1/app/reference/H5.json), [H6](https://comtradeapi.un.org/files/v1/app/reference/H6.json) |

### Eating-out sources by observation year

These are the exact source URLs retained in the panel; one representative 2016 link does not document the other years.

| Year | e-Stat file |
|---|---|
| 2016 | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031586374&fileKind=0 |
| 2017 | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031705247&fileKind=0 |
| 2018 | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031828518&fileKind=0 |
| 2019 | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000031964810&fileKind=0 |
| 2020 | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032106645&fileKind=4 |
| 2021 | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032220992&fileKind=4 |
| 2022 | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040079025&fileKind=4 |
| 2023 | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040193355&fileKind=4 |
| 2024 | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040297542&fileKind=4 |
| 2025 | https://www.e-stat.go.jp/stat-search/file-download?statInfId=000040424637&fileKind=4 |

### HS-to-BEC conversion sources

Use the **conversion** sheets; do not expand an ambiguous correlation table into duplicate product records.

| Import years | Comtrade revision | UNSD conversion source |
|---|---|---|
| 2016 | H4 / HS2012 | [HS2012 to BEC correlation and conversion workbook](https://unstats.un.org/unsd/classifications/Econ/tables/HS%202012%20to%20BEC%20Correlation%20and%20conversion%20tables.xls) |
| 2017–2021 | H5 / HS2017 | [HS2017 to BEC conversion and correlation workbook](https://unstats.un.org/unsd/classifications/Econ/tables/HS2017toBECConversionAndCorrelationTables.xlsx) |
| 2022–2025 | H6 / HS2022 | [HS2022 to BEC4 conversion and correlation workbook](https://unstats.un.org/unsd/classifications/Econ/tables/HS2022toBEC4ConversionAndCorrelationTables.xlsx) |

Product descriptions and source classifications are preserved. Whole soyabeans (HS1201) include sowing seed. Soy flour (120810), crude/other soy oil (150710/150790) and soy sauce (210310) are separately named. Soy oilcake/extraction residues (230400) are supplementary, classified outside BEC food and **excluded from food totals**. Some other BEC-selected products have potential seed, feed or industrial uses; an oral-nicotine code is also flagged. These records are not measured human food consumption. Prepared products may contain soya without having a soy-specific product code.

## Historical and supplementary sources

These remain relevant to reproducing earlier analyses, but are not additional independent inputs to the current total-food/control specification.

| Variable | Original provider | Dataset/status | Source |
|---|---|---|---|
| China/USA **broad-food values**, 2016–2025 | UN Comtrade | Japan imports, BEC Rev.4 category 1 and components, partners China 156 and USA 842; current USD; superseded by World for the aggregate question | [Example 2016 query](https://comtradeapi.un.org/public/v1/preview/C/A/B4?period=2016&reporterCode=392&cmdCode=1%2C11%2C12&flowCode=M&partnerCode=156%2C842&partner2Code=0&customsCode=C00&motCode=0&maxRecords=500); retained replies in `data/food_import_sources/` |
| China/USA **three-crop mass basket** | UN Comtrade / historical supplied panel | Maize HS1005, rice HS1006 and soyabeans HS1201; **different scope and units** from broad food. Explicit retained panel API URLs cover 2024–2025; earlier panel observations do not all carry populated import-source fields | [2024 query](https://comtradeapi.un.org/public/v1/preview/C/A/HS?period=2024&reporterCode=392&cmdCode=1005%2C1006%2C1201&flowCode=M&partnerCode=156%2C842&partner2Code=0&customsCode=C00&motCode=0&maxRecords=500), [2025 query](https://comtradeapi.un.org/public/v1/preview/C/A/HS?period=2025&reporterCode=392&cmdCode=1005%2C1006%2C1201&flowCode=M&partnerCode=156%2C842&partner2Code=0&customsCode=C00&motCode=0&maxRecords=500) |
| Population denominator for the historical 2024–2025 crop proxy | World Bank, World Development Indicators | `SP.POP.TOTL`, Japan/JPN; national people. Retained panel records API `lastupdated 2026-10-08`; this is a source-snapshot label, not a claim about the latest live revision | [API](https://api.worldbank.org/v2/country/JPN/indicator/SP.POP.TOTL?date=2024:2025&format=json); [indicator metadata](https://data.worldbank.org/indicator/SP.POP.TOTL) |
| Organic-farming activity | Ministry of Agriculture, Forestry and Fisheries (MAFF), via e-Stat | 2020 Census of Agriculture and Forestry, Volume 2, Table II57; counts and gross cropped area for reported organic activity, including uncertified operations | [Workbook](https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032101935&fileKind=0); [official catalogue](https://data.e-gov.go.jp/data/dataset/maff_20210909_0048/resource/f7530d2e-af38-4f9e-a7f1-6c55075fd2d8) |
| Gardening/horticulture participation | Statistics Bureau of Japan, via e-Stat | **2021 Survey on Time Use and Leisure Activities**, Table 93-1 / sheet `a093_1`; participants aged 10+, counts rounded to thousands | [Metadata](https://www.e-stat.go.jp/stat-search/files?stat_infid=000032223420); [workbook](https://www.e-stat.go.jp/stat-search/file-download?statInfId=000032223420&fileKind=0) |
| Five synthetic FY2023 income values | Project-generated sensitivity data | Ishikawa, Nara, Tokushima, Kagawa and Miyazaki; **not an official provider series and not used as observed controls** | [data/synthetic_income_sensitivity_only.csv](data/synthetic_income_sensitivity_only.csv) |
| Simulated food/fertility panels | Project-generated method benchmarks | Declared simulation assumptions and random seeds; no real-calendar interpretation or pooling into observed Japanese samples | [synthetic/food_import_simulation/README_SYNTHETIC.md](synthetic/food_import_simulation/README_SYNTHETIC.md) |

### Historical crop-basket units and provenance limits

The three-crop basket is maize (HS1005), rice (HS1006) and soyabeans (HS1201). Its retained mass variables are kilograms, and the explicit 2024–2025 per-resident construction uses the national population denominator. Source-estimated mass flags are retained where available. It is not the all-food BEC series and is not measured prefectural consumption.

Do not claim that every historical crop observation has a complete independently archived API/cell trace: `import_source` and `population_source` in the historical panel are populated for 2024–2025, while earlier values are inherited from the retained panel inputs. The source catalogue records populated fields without inventing URLs or denominators for missing provenance. This limitation does not change the provenance of the separately collected World/BEC and named-HS food series.

## Coverage and interpretation notes

- **TFR vintages:** prefectural 2016–2024 values come from the final-data historical table published in 2025. The retained 2025 prefectural/national rates are provisional; consult the provider for subsequent final releases rather than treating a projected publication date as verification.
- **Income publication versus accounting year:** the official FY2023 table family was posted on 7 August 2026 and covers 42 prefectures. The CSV's `income_release_vintage` values 2023/2022 denote the source table families, not calendar publication dates. Fiscal-year labels are matched to calendar-year fertility labels in the analysis.
- **Observed control coverage:** all 47 prefectures have income for 2016–2022, only 42 for 2023, and none for 2024–2025 in the retained harmonised extract. The controlled primary sample is **329 rows, 2016–2022**; the 2023 complete-case sensitivity has **371 rows**. Missing incomes are not replaced by the separate synthetic values. No unsupported claim that dropping synthetic values leaves current results unchanged is needed: current models never include them.
- **Import geography:** World partner 0 includes China and the USA. Their country totals are not added again. National imports are repeated within year when joined to prefectural TFR; this is not local exposure. Prefecture effects alone do not remove shared time shocks; unrestricted **year effects** absorb the national import main effects.
- **Import units:** the current food models use nominal current USD, not tonnes, inflation-adjusted quantity, net imports or diet. Historical crop mass/per-resident variables are a separate measure. No World Bank denominator is used to construct the current nominal-dollar food variable.
- **Classification and reconciliation:** the published BEC World total is retained even where it differs slightly from component or mapped-product sums. Named-product gaps are exported; no rescaling forces exact agreement. HS revisions and BEC conversion flags remain visible.
- **Snapshots:** organic activity is observed in **2020** and gardening in **2021**. In the dated source panel, values are available for those observation years, not measured annually from 2016–2025. Copying a snapshot across years would not create annual observations; an unchanged prefectural snapshot would be absorbed by prefecture effects. Neither snapshot is a control in the current income/eating-out regressions or ANOVA.
- **Measure boundaries:** organic-farming activity does not establish certified-organic food consumption; gardening is not specifically terrace gardening or growing food. Eating-out data describe the surveyed city/household population, not all prefectural residents.
- **Story inspiration:** the motivating graph/repost is not an input dataset. Its exact post URL has not been supplied and is not invented here.

## Citing the data

Cite the original providers and the exact dataset/table/version used:

- MHLW / e-Stat: Vital Statistics, prefectural Table 4-5 and provisional-report Tables 2/9.
- ESRI, Cabinet Office: Prefectural Accounts, nominal income per resident, Table 7, with FY2023/FY2022 table family and publication date distinguished.
- Statistics Bureau of Japan / e-Stat: Family Income and Expenditure Survey annual city tables; Survey on Time Use and Leisure Activities 2021, Table 93-1, when using the historical snapshot.
- MAFF / e-Stat: Census of Agriculture and Forestry 2020, Table II57, when using the historical organic snapshot.
- United Nations Comtrade Database: reporter, partner, flow, classification revision, product codes, year, unit and retrieval date.
- UNSD: BEC Rev.4 manual and the applicable HS-to-BEC conversion workbooks.
- World Bank: WDI `SP.POP.TOTL`, JPN, and retained source vintage, only when using the historical population-based proxy.

Also cite the repository URL and commit. Derived regressions, ANOVA, graphs and synthetic simulations are project outputs, not additional official datasets. Original provider terms continue to apply.
