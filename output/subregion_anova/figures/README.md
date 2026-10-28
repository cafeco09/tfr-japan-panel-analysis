# Controlled prefectural ANOVA figures

Source: `../significance_each_prefecture.csv` and `../ANOVA_type_II_classical.csv`. Primary sample: 47 prefectures, 2016–2022, 329 observed records and seven year clusters. Model: prefectural TFR on prefecture categories, log national food imports, log prefectural income, log capital-city eating-out expenditure and a common linear trend.

1. **prefecture_adjusted_tfr_differences.png / .svg**: all 47 adjusted regional differences from the equally weighted adjusted prefectural mean. Bars are pointwise 95% year-clustered intervals. Colours encode the separate 47-test Holm-adjusted cluster-t result, so an interval excluding zero need not imply a coloured significant point.
2. **prefecture_significance_inference_sensitivity.png / .svg**: all 47 Holm-corrected p-values under classical iid, year-clustered t and restricted wild-cluster inference. Cell numbers are actual corrected p-values; colour is −log10(p), capped at 6. Every method uses the same family of 47 contrasts.
3. **controlled_anova_classical_terms.png / .svg**: Type II ANOVA F statistics on a logarithmic axis, with numerator degrees of freedom and p-value labels that use scientific notation for small values. These tests assume iid homoskedastic errors. F values with different degrees of freedom are not directly comparable causal importance scores.

The adjusted predictions hold continuous covariates at common mean log-values/time. They are model-based standardisations, not the observed prefectural average TFR. National imports are shared across prefectures within each year; these graphs do not estimate prefecture-specific import effects.

Thirty prefectures pass the conventional cluster-t Holm threshold. None passes bootstrap Holm: with seven clusters and 128 enumerated Rademacher patterns, the minimum two-sided bootstrap p is 0.015625, too coarse for a 47-test Holm family at 5%. This limit does not establish that prefectural rates are equal. Neither inference method removes possible temporal dependence, endogenous controls or common national shocks.

Reproduce from the repository root:

```bash
python scripts/_22_subregion_anova.py
python scripts/_23_plot_subregion_anova.py
```

The PNGs render directly on GitHub. SVGs retain vector lines and editable text for export.
