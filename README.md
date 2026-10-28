# TFR Determinants in Japan (2016–2025) — Reproducible Package

## What this does
Estimates the association between prefecture-level total fertility rate (TFR) and:
- log income per resident (observed 2016–2023 only)
- log eating-out expenditure per household (all years)
- national China/USA crop imports (year-level only)
- organic farming and gardening context (snapshot z-scores)

Runs core FE specs, import-without-year-FE specs, 2024–2025 eating-out-only
specs, and exploratory import × organic interactions. Produces robustness
table, coefficient plots, scatter/fitted plots, and LaTeX + Word tables.

## Data
Place the 10 CSV files listed in `data/` (unchanged from source).
No external downloads required; all sources are cited in the CSVs.

## Run
```bash
pip install -r requirements.txt
python run_all.py
