# Model audit

Audit date: 28 October 2026. Source CSVs and original model outputs are unchanged.

## Data and identification

- The core sample contains 371 observed-income rows across 47 prefectures and eight years.
- The period file is annual data with year labels removed, not period averages. Exact matching recovers years for every row: period 1 = 2017–2019, 2 = 2020–2021, 3 = 2022–2023, 4 = 2024–2025.
- The eligible period sample has 324 rows from 2017–2023; there are no eligible income rows in period 4.
- Both context variables are constant within prefecture. National imports are constant within year.
- Annual fixed effects absorb national import main effects. Prefecture fixed effects absorb context main effects. The full-rank annual interaction models therefore omit those absorbed terms.
- The 2025 TFR entries are explicitly labelled provisional in the supplied data. This audit checks internal structure, not every external source value.

## Core sensitivity estimates

Cluster standard errors use a t reference distribution with cluster degrees of freedom. The original tables use the normal reference distribution. Sensitivity specifications change the estimand and are not interchangeable estimates of one causal effect.

| spec | variable | coefficient | cluster_se | p | n | incremental_r2_over_FE |
|---|---|---|---|---|---|---|
| annual_two_way_FE | log_income | 0.2058 | 0.0846 | 0.0190 | 371.0000 | 0.0341 |
| annual_two_way_FE | log_eating_out | -0.0019 | 0.0227 | 0.9321 | 371.0000 | 0.0341 |
| balanced_42_prefectures | log_income | 0.2062 | 0.0866 | 0.0219 | 336.0000 | 0.0377 |
| balanced_42_prefectures | log_eating_out | -0.0021 | 0.0231 | 0.9290 | 336.0000 | 0.0377 |
| pre_COVID_2016_2019 | log_income | 0.1899 | 0.1380 | 0.1755 | 188.0000 | 0.0215 |
| pre_COVID_2016_2019 | log_eating_out | 0.0144 | 0.0284 | 0.6152 | 188.0000 | 0.0215 |
| exclude_2020_2021 | log_income | 0.2080 | 0.1073 | 0.0586 | 277.0000 | 0.0342 |
| exclude_2020_2021 | log_eating_out | -0.0004 | 0.0280 | 0.9880 | 277.0000 | 0.0342 |
| exclude_Tokyo | log_income | 0.2113 | 0.0864 | 0.0184 | 363.0000 | 0.0351 |
| exclude_Tokyo | log_eating_out | -0.0024 | 0.0228 | 0.9170 | 363.0000 | 0.0351 |
| exclude_Okinawa | log_income | 0.1648 | 0.0814 | 0.0489 | 363.0000 | 0.0220 |
| exclude_Okinawa | log_eating_out | 0.0020 | 0.0225 | 0.9301 | 363.0000 | 0.0220 |
| exclude_Tokyo_Okinawa | log_income | 0.1693 | 0.0833 | 0.0481 | 355.0000 | 0.0226 |
| exclude_Tokyo_Okinawa | log_eating_out | 0.0016 | 0.0226 | 0.9453 | 355.0000 | 0.0226 |
| annual_2017_2023_period_sample | log_income | 0.1700 | 0.0789 | 0.0365 | 324.0000 | 0.0246 |
| annual_2017_2023_period_sample | log_eating_out | 0.0052 | 0.0225 | 0.8185 | 324.0000 | 0.0246 |
| prefecture_specific_linear_trends | log_income | 0.0603 | 0.0514 | 0.2470 | 371.0000 | 0.0058 |
| prefecture_specific_linear_trends | log_eating_out | -0.0152 | 0.0202 | 0.4574 | 371.0000 | 0.0058 |
| one_year_lagged_covariates | lag_log_income | 0.2105 | 0.0826 | 0.0143 | 324.0000 | 0.0637 |
| one_year_lagged_covariates | lag_log_eating_out | 0.0492 | 0.0209 | 0.0230 | 324.0000 | 0.0637 |
| first_differences_with_year_effects | d_log_income | 0.0729 | 0.0556 | 0.1967 | 324.0000 | — |
| first_differences_with_year_effects | d_log_eating_out | -0.0313 | 0.0202 | 0.1286 | 324.0000 | — |

The incremental R² measures improvement over the matching fixed-effects-only model, not the total R² dominated by prefecture and year effects. It is in-sample, not predictive validation.

## Leave-one-prefecture-out

- log_eating_out: coefficients range -0.0098 (omit JP-25) to 0.0040 (omit JP-05); 0/47 fits have p < 0.05. These dependent fits are influence diagnostics, not 47 replications.
- log_income: coefficients range 0.1648 (omit JP-47) to 0.2305 (omit JP-32); 47/47 fits have p < 0.05. These dependent fits are influence diagnostics, not 47 replications.

## Rank checks

| spec | rank | columns | n |
|---|---|---|---|
| legacy_base | 51.0000 | 53.0000 | 324.0000 |
| legacy_China_interaction | 53.0000 | 55.0000 | 324.0000 |
| period_FE_identified_China_interaction | 53.0000 | 53.0000 | 324.0000 |
| annual_FE_base | 55.0000 | 55.0000 | 324.0000 |
| annual_FE_China_interaction | 56.0000 | 56.0000 | 324.0000 |
| annual_FE_USA_interaction | 56.0000 | 56.0000 | 324.0000 |
| annual_FE_both_interactions | 57.0000 | 57.0000 | 324.0000 |
| annual_FE_China_gardening_interaction | 56.0000 | 56.0000 | 324.0000 |
| annual_FE_China_interaction_context_trend | 57.0000 | 57.0000 | 324.0000 |

## Interaction sensitivity

| spec | variable | coefficient | cluster_se | p | n |
|---|---|---|---|---|---|
| legacy_China_interaction | cn_import:organic_farming_context_z | 0.0397 | 0.0172 | 0.0256 | 324.0000 |
| period_FE_identified_China_interaction | cn_import:organic_farming_context_z | 0.0397 | 0.0172 | 0.0251 | 324.0000 |
| annual_FE_China_interaction | cn_import:organic_farming_context_z | 0.0386 | 0.0139 | 0.0081 | 324.0000 |
| annual_FE_USA_interaction | us_import:organic_farming_context_z | -0.0002 | 0.0001 | 0.0368 | 324.0000 |
| annual_FE_both_interactions | cn_import:organic_farming_context_z | 0.0329 | 0.0127 | 0.0131 | 324.0000 |
| annual_FE_both_interactions | us_import:organic_farming_context_z | -0.0001 | 0.0001 | 0.1228 | 324.0000 |
| annual_FE_China_gardening_interaction | cn_import:female_gardening_context_z | -0.0042 | 0.0159 | 0.7913 | 324.0000 |
| annual_FE_China_interaction_context_trend | cn_import:organic_farming_context_z | 0.0309 | 0.0112 | 0.0082 | 324.0000 |

Legacy context main effects are not uniquely identified because they are absorbed by prefecture effects. The import main effect is algebraically estimable under coarse period effects, since imports still vary within periods, but remains exposed to annual national confounding. Removing the absorbed context main effects leaves the legacy China interaction unchanged; the rank warning alone does not invalidate every coefficient.

With annual effects, the national import main effect is absorbed and absolute import marginal effects cannot be estimated. The annual-FE interaction describes differential exposure by context, conditional on common year shocks; it is not a national average import effect or proof of a protective organic-farming mechanism.

Only seven annual exposure values enter the eligible interaction sample. Prefecture clustering does not establish robustness to residual common national shocks. Few-year inference, multiple exploratory tests and context-specific trends remain unresolved.

### China interaction: omit each year

| spec | coefficient | cluster_se | p | n |
|---|---|---|---|---|
| 2017 | 0.0766 | 0.0225 | 0.0014 | 277.0000 |
| 2018 | 0.0416 | 0.0156 | 0.0104 | 277.0000 |
| 2019 | 0.0347 | 0.0126 | 0.0083 | 277.0000 |
| 2020 | 0.0324 | 0.0158 | 0.0466 | 277.0000 |
| 2021 | 0.0386 | 0.0141 | 0.0086 | 277.0000 |
| 2022 | 0.0388 | 0.0139 | 0.0074 | 277.0000 |
| 2023 | 0.0333 | 0.0133 | 0.0161 | 282.0000 |

The spec label is the omitted year. These are dependent influence checks, not independent replications. The context-trend specification above tests whether the interaction survives a linear trend proportional to organic context; it does not control all context-specific shocks.

## Eating-out sensitivity

| spec | coefficient | cluster_se | p | n |
|---|---|---|---|---|
| EO_2016_2024_final_labelled | 0.0089 | 0.0202 | 0.6625 | 423.0000 |
| EO_2016_2025_with_provisional | -0.0067 | 0.0172 | 0.6977 | 470.0000 |
| EO_2024_2025_only | 0.0073 | 0.0362 | 0.8402 | 94.0000 |

## Next improvements

1. Replace the legacy exploratory models with full-rank annual-FE interaction models and remove unidentified main effects and absolute marginal-effect claims from exports.
2. Pre-specify the main estimand and sensitivity set; retain sign changes and null results rather than choosing models by p-value.
3. Audit the raw income measure, price basis and source vintages; a national deflator only shifts log covariates by year and is absorbed by annual fixed effects. Prefecture-specific living costs require extra data.
4. Seek repeated demographic controls such as age structure, marriage, migration and urbanisation with a causal rationale. Avoid treating mediators as routine controls.
5. Separate provisional/final data, replace the duplicate synthetic-exclusion check with a real observed-versus-imputed comparison if imputation is scientifically justified, and add source checks and explicit finite-value/sample checks to every model.
6. If prediction is the goal, define a forecast horizon and use forward-in-time evaluation against simple baselines. R² from fixed-effect regressions is insufficient.
