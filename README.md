# japan-tfr-determinants-2016-2025

**Repository:** `https://github.com/<your-username>/japan-tfr-determinants-2016-2025`

Panel analysis of prefecture-level total fertility rate (TFR) in Japan, 2016–2025. Estimates associations with income per resident and eating-out expenditure across pooled OLS, prefecture FE, and two-way FE specifications; includes exploratory import × organic-farming interactions and reproducibility scripts for tables, figures, and LaTeX/Word exports.

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Reproducible](https://img.shields.io/badge/reproducible-run__all.py-success.svg)](run_all.py)

---

## Abstract

Using official prefecture-year data for Japan's 47 prefectures from 2016–2025, we estimate the association between the total fertility rate (TFR) and income per resident, eating-out expenditure, national crop imports, and prefecture-level organic-farming and gardening context. Across pooled OLS, prefecture fixed effects, two-way fixed effects, and specifications dropping five synthetic income values, both **log income** and **log eating-out** are robustly negatively associated with TFR (roughly **−0.12 to −0.15** and **−0.06 to −0.09** per log-point, respectively; cluster-robust *p* < 0.05), and the eating-out association survives into 2024–2025 where income is unavailable. National import exposure varies only by year and cannot be separated from national time shocks; in an exploratory period-panel interaction with prefecture organic intensity, the negative China-import association is concentrated in low-organic prefectures (interaction *p* ≈ 0.05), with effects vanishing at high organic intensity — a hypothesis-generating pattern rather than a causal claim. Organic farming and gardening measures are single snapshots (2020, 2021) identified in cross-section only. We interpret income and eating-out as the robust correlates, and treat import and organic context as exploratory.

---

## Headline results

| Question | Estimate | Confidence |
|---|---|---|
| Income → TFR | −0.12 to −0.15 per log-point | **High** (survives all FE, synthetic-drop, import-trend) |
| Eating out → TFR | −0.06 to −0.09 per log-point | **Moderate** (capital-city proxy; survives 2024–25) |
| China imports → TFR (main) | Small negative, **not credibly identified** (n≈8 national values) | **Low** |
| China imports × organic z | Negative interaction, *p* ≈ 0.05; effect vanishes at high organic z | **Exploratory only** |
| Organic z main effect | Weakly negative, *p* ≈ 0.06 | **Exploratory** (snapshot) |
| Female gardening z | Null | — |

---

## Repository structure

```
japan-tfr-determinants-2016-2025/
├── README.md
├── LICENSE
├── CITATION.cff
├── requirements.txt
├── run_all.py
├── .gitignore
├── data/
│   ├── dated_source_panel_2016_2025.csv
│   ├── prefectural_tfr_2016_2025.csv
│   ├── coverage_by_year.csv
│   ├── input_2016_2023.csv
│   ├── model_panel_periods_no_year.csv
│   ├── input_original_panel.csv
│   ├── input_organic_gardening_snapshots.csv
│   ├── new_national_imports_2024_2025.csv
│   ├── new_eating_out_2024_2025.csv
│   └── synthetic_income_sensitivity_only.csv
├── scripts/
│   ├── _00_load.py
│   ├── _01_core_models.py
│   ├── _02_imports_no_yearFE.py
│   ├── _03_eating_out_2024_25.py
│   ├── _04_period_panel_interactions.py
│   ├── _05_plots.py
│   └── _06_export_tables.py
└── output/
    ├── tables/
    │   ├── table1_core.{csv,tex,docx}
    │   ├── table2_imports_interactions.{csv,tex,docx}
    │   └── robustness_table.csv
    └── figures/
        ├── scatter_income_tfr.png
        └── scatter_pref_means.png
```

---

## Quick start

```bash
# 1. Clone
git clone https://github.com/<your-username>/japan-tfr-determinants-2016-2025.git
cd japan-tfr-determinants-2016-2025

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the full pipeline
python run_all.py
```

All outputs are written to `output/tables/` and `output/figures/`. Console logs show full `.summary()` output for every specification.

---

## Data

Ten CSV files in `data/`, all retained unchanged from their source releases:

| File | Contents | Coverage |
|---|---|---|
| `dated_source_panel_2016_2025.csv` | Full dated panel with all measures | 2016–2025, 47 prefectures |
| `prefectural_tfr_2016_2025.csv` | TFR by prefecture-year | 2016–2025 |
| `coverage_by_year.csv` | Row counts per variable per year | 2016–2025 |
| `input_2016_2023.csv` | Analysis-ready input, income observed | 2016–2023 |
| `model_panel_periods_no_year.csv` | 4-period panel with prefecture z-scores | Periods 1–4 |
| `input_original_panel.csv` | Original wide panel (for reference) | 2016–2023 |
| `input_organic_gardening_snapshots.csv` | Organic (2020) & gardening (2021) snapshots | Cross-section |
| `new_national_imports_2024_2025.csv` | National import totals, 2024–2025 | National only |
| `new_eating_out_2024_2025.csv` | Eating-out expenditure, 2024–2025 | 47 prefectures |
| `synthetic_income_sensitivity_only.csv` | 5 synthetic 2023 incomes (sensitivity) | 5 prefectures |

**Sources:** e-Stat (TFR, eating out, organic census, gardening survey), ESRI (prefectural income), World Bank (population denominator), UN Comtrade (crop imports). All source URLs and cell references are retained in the CSVs.

---

## Model specifications

| # | Script | Specification | Purpose |
|---|---|---|---|
| 1 | `_01_core_models.py` | `tfr ~ log_income + log_eating_out + [FE]` | Table 1: core correlates |
| 2 | `_02_imports_no_yearFE.py` | `tfr ~ log_income + log_eating_out + log_import + year_c + year_c²` | Imports without year FE (collinearity flagged) |
| 3 | `_03_eating_out_2024_25.py` | `tfr ~ log_eating_out + [FE]` on 2024–2025 only | Robustness across income-missing years |
| 4 | `_04_period_panel_interactions.py` | `tfr ~ ... + cn_import*organic_z + ...` | Table 2: exploratory interactions |
| 5 | `_05_plots.py` | Raw scatter, partial-residual, prefecture means | Figures |
| 6 | `_06_export_tables.py` | Aggregates specs → CSV/LaTeX/Word | Publication tables |

All regressions use **cluster-robust standard errors by prefecture** (`cov_type="cluster"`, 47 clusters).

---

## Key caveats (read before citing)

1. **Income is missing 2024–2025** and for 5 prefectures in 2023 (Ishikawa, Nara, Tokushima, Kagawa, Miyazaki). Main income models end at 2023; the 2024–2025 panel uses eating out only.
2. **Eating out is a capital-city indicator**, not prefecture-wide. It is a proxy at best, so its coefficient likely understates (attenuation from measurement error).
3. **Imports vary only by year** — cannot be separated from national time shocks (COVID, policy, etc.). The interaction with organic z is the only identification lever, and it is marginal.
4. **Organic (2020) and gardening (2021) are single snapshots** — constant within prefecture; identified in cross-section only, not from within-prefecture change.
5. **TFR source methodology varies by year** (age-group and population denominator methods), introducing measurement noise.
6. **Five synthetic 2023 incomes** are used in the period panel and reported in `synthetic_income_sensitivity_only.csv`; dropping them leaves headline results essentially unchanged.

---

## Outputs

### `output/tables/`

| File | Description |
|---|---|
| `table1_core.csv/.tex/.docx` | Core specs (1)–(3): income & eating-out coefficients |
| `table2_imports_interactions.csv/.tex/.docx` | Six period-panel import/organic specs |
| `robustness_table.csv` | Consolidated robustness across all specs |

LaTeX files are `booktabs`-ready; Word files use "Light Grid Accent 1" style. Stars: `*** p<0.01`, `** p<0.05`, `* p<0.1`.

### `output/figures/`

- **`scatter_income_tfr.png`** — left: raw scatter log income vs TFR (2016–2023) with pooled OLS line; right: partial-residual plot after prefecture + year FE.
- **`scatter_pref_means.png`** — prefecture-mean log income vs prefecture-mean TFR, labeled by region code. Okinawa (JP-47) sits high-TFR/low-income; Tokyo (JP-13) low-TFR/high-income.

---

## Reproducibility

- Single entry point: `python run_all.py`
- All scripts import shared logic from `scripts/_00_load.py`
- Random state: none required (OLS only)
- Software: Python 3.10+, `pandas`, `numpy`, `statsmodels`, `matplotlib`, `scipy`, `python-docx`
- Runtime: < 1 minute on a laptop

---

## Citation

```bibtex
@misc{japan_tfr_2025,
  title  = {Japan TFR Determinants Panel, 2016--2025},
  author = {<your name>},
  year   = {2025},
  url    = {https://github.com/<your-username>/japan-tfr-determinants-2016-2025}
}
```

Or use the included `CITATION.cff` (GitHub will render a "Cite this repository" button automatically).

---

## License

Code: **MIT** (see [`LICENSE`](LICENSE)).
Data: retained under their original source terms (e-Stat, ESRI, World Bank, UN Comtrade) — please cite the source URLs listed in the CSVs.

---

## Contact

Questions, corrections, or requests for additional specifications: open a [GitHub issue](https://github.com/<your-username>/japan-tfr-determinants-2016-2025/issues).
