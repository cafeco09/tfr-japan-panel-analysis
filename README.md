# Japan TFR panel analysis

Panel analysis of prefecture-level total fertility rate (TFR), income per resident and eating-out expenditure, with exploratory import, organic-farming and gardening specifications.

**Repository:** https://github.com/cafeco09/tfr-japan-panel-analysis

## Reproduced results

The repaired pipeline runs on the included CSV files. The earlier README claimed consistently negative income and eating-out associations; **the executed core models do not support that claim**. Coefficient signs and significance depend on the fixed effects used.

| Variable | OLS + year FE | Prefecture FE | Prefecture + year FE |
|---|---:|---:|---:|
| log(income) | −0.444 (0.113) | −1.128 (0.104) | +0.206 (0.085) |
| log(eating out) | −0.026 (0.098) | +0.211 (0.025) | −0.002 (0.023) |
| Observations | 371 | 371 | 371 |
| R² | 0.404 | 0.838 | 0.978 |

Values in parentheses are standard errors clustered by prefecture (47 clusters). In the two-way fixed-effects model, the income p-value is approximately 0.015 and the eating-out p-value is approximately 0.932. These are conditional associations, not causal effects. See [Table 1](output/tables/table1_core.csv) and the [robustness table](output/tables/robustness_table.csv).

The `DropSynth` row removes no additional observations from the already observed-income-only core sample. It duplicates the OLS + year-FE result and is not an independent sensitivity test.

## Exploratory import analysis

**Status: hypothesis-generating. The current design does not establish that imports affect fertility or that organic farming protects against an import-related effect.**

The analysis asks whether fertility changes differ along the organic-farming-context gradient when national China crop imports change. Its annual fixed-effects comparison uses 324 observed-income observations from 47 prefectures in 2017–2023. Imports supply seven annual national values; they do not measure what households in each prefecture consume.

### Findings and sensitivity

| Specification or inference check | China-import × organic-context coefficient | p-value |
|---|---:|---:|
| Annual and prefecture effects; prefecture-clustered inference | +0.0386 | 0.008 |
| Add geographic-region × year effects | +0.0306 | 0.013 |
| Add prefecture-specific linear trends | +0.0325 | 0.014 |
| Add organic-context linear trends and differential 2020, 2021 and 2022 shocks | +0.0117 | 0.389 |
| Baseline coefficient; year-clustered Webb wild bootstrap | +0.0386 | 0.170 |

The first four p-values use prefecture-clustered standard errors with a t reference distribution. The bootstrap uses 9,999 null-imposed draws and seven year clusters. It assumes independence across year clusters and does not resolve serially correlated national shocks. These checks test different assumptions; they are not independent confirmations. The positive association survives several controls, while stronger differential-shock controls and few-year inference materially weaken the evidence. The results do not establish either a causal effect or an effect of zero.

The future-import interaction is also associated with current fertility after controlling for the current-import interaction (coefficient −0.0193, prefecture-clustered p = 0.025). Correlated imports, anticipation and persistent omitted factors prevent treating this lead check as decisive, but it raises concerns about a contemporaneous causal interpretation.

### What the design cannot distinguish

- Annual effects absorb national shocks with equal effects across prefectures. They do not absorb national shocks whose effects differ along the organic-context gradient.
- The organic score is the standardised **2020 share of farms reporting organic activity**, including uncertified operations. It is a snapshot taken after the panel begins, rather than a validated pre-period measure of imported-food exposure.
- Allowing unrestricted organic-context × year shocks fully absorbs the import interaction. Positive, zero and negative imposed import coefficients then produce the same fitted values. This establishes an identification limit; it does not prove that a particular confounder exists.
- Country-of-origin crop kilograms do not measure household consumption, chemical residues or individual dose. The interaction cannot establish a biological protection mechanism.

A stronger design requires a defined mechanism, validated pre-period prefecture-by-crop exposure weights, a defensible source of external import variation, and inference appropriate to the shocks and exposure structure. Multiplying national imports by an organic score or allocating national totals by population does not supply that evidence.

### Reproducibility and legacy tables

See the [full identification audit](output/import_identification/IMPORT_IDENTIFICATION_AUDIT.md), [shared-shock comparisons](output/import_identification/shared_shock_sensitivity.csv) and [bootstrap results](output/import_identification/wild_year_bootstrap.csv). Run `python scripts/_08_import_identification.py` to reproduce them. The audit exports all tested models, covariance diagnostics, bootstrap draws, lead/lag checks, prefecture influence checks and the non-identification demonstration.

[Table 2](output/tables/table2_imports_interactions.csv) preserves the original coarse-period models for transparency. Its China-import × organic coefficient is +0.040 (SE 0.017). Organic and gardening main effects are absorbed by prefecture effects and are not uniquely identified. National import main effects are algebraically estimable under coarse period effects because imports vary within periods, but remain exposed to annual national confounding; annual effects absorb these national main effects. Rank deficiency does not by itself invalidate every coefficient, and reported significance stars do not establish causal identification.

## Run locally

Use Python 3.10 or newer. A fresh Python 3.11 environment is a practical option.

```bash
git clone https://github.com/cafeco09/tfr-japan-panel-analysis.git
cd tfr-japan-panel-analysis
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_all.py
```

On Windows, activate with `.venv\Scripts\activate` instead. If using Conda, create and activate a separate environment instead of nesting a virtual environment inside Conda:

```bash
conda create -n tfr-japan python=3.11 pip -y
conda activate tfr-japan
python -m pip install -r requirements.txt
python run_all.py
```

Run these commands from the repository root. The runner executes all six analysis/export stages and stops if a stage fails. The console includes coefficient summaries and any statistical warnings. The committed tables and figures are generated outputs; local successful execution must be checked separately.

## Outputs

Generated tables and figures are tracked in Git. Temporary logs and Python environments are ignored.

| Output | Contents |
|---|---|
| [table1_core.csv](output/tables/table1_core.csv) | Three core income/eating-out models |
| [table2_imports_interactions.csv](output/tables/table2_imports_interactions.csv) | Six exploratory period-panel models; identification caveats apply |
| [robustness_table.csv](output/tables/robustness_table.csv) | Core estimates and the duplicate synthetic-exclusion row |
| `output/tables/*.tex` | LaTeX versions of Tables 1 and 2 |
| `output/tables/*.docx` | Word versions of Tables 1 and 2 |
| [scatter_income_tfr.png](output/figures/scatter_income_tfr.png) | Raw income/TFR scatter and partial-residual plot |
| [scatter_pref_means.png](output/figures/scatter_pref_means.png) | Prefecture-mean income/TFR scatter |
| [environment.txt](output/environment.txt) | Python and package versions used for the committed run |

![Income and TFR](output/figures/scatter_income_tfr.png)

## Data and caveats

An optional [model audit](output/audit/MODEL_AUDIT.md) reports annual-effect interaction models, rank checks, trends, first differences, lagged covariates and leave-one-out sensitivity. Run it with `python scripts/_07_diagnostics.py`. The original tables remain unchanged for comparison. The audit refines the rank-deficiency caveat: absorbed context main effects are unidentified, while some other coefficients in the same model can remain identifiable.

The `data/` directory contains 11 CSV files. Included files provide prefecture-year data labelled 2016–2025, period-coded inputs, snapshot context measures, coverage information and source references. Source-file labels and provenance have not been independently audited in this execution exercise.

- Core income models use the observed-income sample for 2016–2023. Five prefecture incomes are missing in 2023; income is unavailable for 2024–2025.
- The loader joins eating-out expenditure from `dated_source_panel_2016_2025.csv` to `input_2016_2023.csv` by prefecture and year, validating a one-to-one match.
- Eating-out expenditure is a capital-city proxy. Measurement error need not bias its coefficient towards zero in these multivariable panel models.
- National imports do not provide prefecture-specific exposure. Shared national shocks remain a concern.
- Organic-farming and gardening measures are snapshots, rather than repeated within-prefecture observations.
- Differences in TFR methodology and release status require review before substantive use. The presence of rows labelled 2025 does not establish that they are final official annual observations.

The code repairs leave source CSVs and existing exploratory formulae unchanged. See [RUN_NOTES.md](RUN_NOTES.md) for repair details and interpretation limits.

## Code layout

- `run_all.py`: pipeline entry point.
- `scripts/_00_load.py`: shared loading and feature construction.
- `scripts/_01_core_models.py`: core models.
- `scripts/_02_imports_no_yearFE.py`: import models with time trends.
- `scripts/_03_eating_out_2024_25.py`: later-year and full-panel eating-out models.
- `scripts/_04_period_panel_interactions.py`: exploratory period models.
- `scripts/_05_plots.py`: figures.
- `scripts/_06_export_tables.py`: CSV, LaTeX and Word exports.

## Licence and attribution

Code is covered by the [MIT licence](LICENSE). Data retain their original source terms; consult the source references in the CSV files. Cite the repository URL and the commit used when reporting results. No `CITATION.cff` is currently included.
