# Running the analysis

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_all.py
```

Outputs are written to `output/tables/` and `output/figures/`.

## Pipeline repairs

- Moved the runner to the repository root to match its path logic.
- Renamed the loader and core-model files to match the expected imports.
- Implemented the missing core regressions using the same three specifications as the existing table exporter.
- Renamed the dependency file to `requirements.txt`, corrected the malformed python-docx version constraint, and added Jinja2 for LaTeX exports.
- Joined eating-out expenditure from the included dated source panel by prefecture and year, with a one-to-one validation. The 2016–2023 input file does not contain that column.

The source CSVs and existing exploratory model formulae were not changed.

## Interpretation limits

The executed results do not reproduce the earlier README's headline estimates. For example, the core two-way fixed-effects specification gives log-income about +0.206 (SE 0.085) and log-eating-out about -0.002 (SE 0.023), with 371 observations. The updated README reports the executed coefficients and withdraws the earlier claim of consistently negative coefficients.

The exploratory period models report rank-deficient design matrices. Their reported main-effect coefficients are not uniquely identified when absorbed by the fixed effects. Successful execution is not validation of those estimates or of the data provenance.

The synthetic-income exclusion in the existing robustness exporter removes no additional observations from the already observed-income-only core sample. That row should not be interpreted as an independent robustness result.
