# National imports: identification and shared-shock audit

28 October 2026. All results use the supplied data. No new exposure data were invented or imputed.

## Finding

The national import series multiplied by organic context identifies a differential temporal association under restrictions on context-specific national shocks. It does not identify prefecture-specific import exposure, a national average import effect, or an organic-farming protection mechanism.

In this run, the baseline interaction is +0.0386 (prefecture-clustered p = 0.0081). Adding organic-context trends and separate pandemic-year responses gives +0.0117 (p = 0.389). The year-clustered Webb bootstrap p-value is 0.170. These are evidence of sensitivity, not proof of a zero effect.

![Specification and bootstrap diagnostics](import_identification_diagnostics.png)

The core identifying restriction is substantive: after controls and fixed effects, omitted national shocks must not differentially move fertility along the organic-context gradient in a way correlated with imports. Year effects remove equal-loading common shocks, not heterogeneous responses to those shocks. Baseline imports, COVID, food prices, urbanisation, marriage and migration can share time patterns; adding annual FE alone does not resolve this.

## Data and timing

- Primary comparison: the same 324 eligible rows, 47 prefectures, 2017–2023. There are seven national import values, not 324 independent import shocks. The precision of inference also depends on the maintained cross-prefecture error assumptions; counting shocks alone does not determine all possible inferential validity.
- Organic context is exactly the standardised share of farms reporting organic activity in the 2020 census. It is not a local imported-food consumption share, pesticide measurement or pre-2017 exposure measure. It includes uncertified operations. Its timing raises the possibility of post-treatment measurement; it cannot simply be assumed exogenous.
- Country-of-origin kilograms of a crop basket are not chemical residues, individual consumption, or biologically relevant dose. No health mechanism can be inferred from this interaction.
- Centring imports and organic context changes only terms absorbed by FE; the interaction coefficient remains comparable to the previous annual-FE audit. No observation exclusions are chosen by statistical significance.

## Explicit non-identification demonstration

Write TFR_it = prefecture_FE_i + year_FE_t + controls_it + theta × organic_i × imports_t + organic_i × h_t + error_it. With unrestricted h_t, any candidate theta can be offset by h_t. The original data cannot distinguish these explanations.

After including unrestricted organic-context × year effects, the residual treatment norm is 3.58e-14 of its raw norm. The interaction is fully absorbed. This is an identification result, not a numerical failure.

| imposed_import_interaction | ssr | max_prediction_difference_vs_unrestricted |
|---|---|---|
| -0.0386 | 0.1524 | 0.0000 |
| 0.0000 | 0.1524 | 0.0000 |
| 0.0386 | 0.1524 | 0.0000 |

Positive, zero and negative imposed import coefficients fit equally well when the allowed organic-context-specific national shocks adjust. This does not prove a particular confounder exists; it proves the data cannot rule it out without extra restrictions.

## Shared-shock specification sensitivity

All rows below use the same sample. p-values use prefecture-clustered CR1 SE and t(46); they are specification diagnostics, not independent confirmations. More flexible trends use scarce time variation and can reduce both bias and precision. Income and eating out may themselves be outcomes of trade; the no-controls row is included because controlling mediators can change the estimand.

| spec | coefficient | prefecture_cluster_se | p_prefecture_t | treatment_information_fraction_vs_baseline |
|---|---|---|---|---|
| annual_FE | 0.0386 | 0.0139 | 0.0081 | 1.0000 |
| organic_linear_trend | 0.0309 | 0.0112 | 0.0082 | 0.6626 |
| organic_quadratic_trend | 0.0416 | 0.0132 | 0.0028 | 0.4754 |
| organic_pandemic_year_shocks | 0.0322 | 0.0141 | 0.0265 | 0.7372 |
| organic_trend_and_pandemic_shocks | 0.0117 | 0.0135 | 0.3893 | 0.4031 |
| prefecture_specific_linear_trends | 0.0325 | 0.0127 | 0.0141 | 0.6621 |
| geographic_block_by_year_effects | 0.0306 | 0.0118 | 0.0126 | 0.8369 |
| current_and_next_year_imports | 0.0283 | 0.0126 | 0.0299 | 0.7717 |
| current_and_previous_year_imports | 0.0389 | 0.0144 | 0.0095 | 0.9910 |
| no_contemporaneous_income_or_eating_out | 0.0395 | 0.0149 | 0.0108 | 1.0011 |

Pandemic controls are organic context interacted with separate 2020, 2021 and 2022 indicators; they allow differential rather than merely average shocks. Geographic controls allow each of eight explicitly listed blocks a separate annual shock. See identification_checks.json for the block mapping. Prefecture trends use one omitted reference trend alongside year effects to keep full rank.

## Covariance and few-year sensitivity

| method | coefficient | se | reference_df | p | ci_low | ci_high |
|---|---|---|---|---|---|---|
| prefecture_clusters_47 | 0.0386 | 0.0139 | 46.0000 | 0.0081 | 0.0105 | 0.0666 |
| year_clusters_7 | 0.0386 | 0.0130 | 6.0000 | 0.0252 | 0.0067 | 0.0704 |
| two_way_prefecture_and_year | 0.0386 | 0.0156 | 6.0000 | 0.0480 | 0.0005 | 0.0766 |

Prefecture clustering permits serial dependence within a prefecture but assumes independence between prefectures. Year clustering permits arbitrary same-year cross-prefecture dependence but assumes independence across years. Two-way clustering combines those dimensions but does not generally allow serially correlated common factors across different prefectures and years. Seven year clusters make the latter two estimates fragile. The two-way covariance matrix has a materially negative eigenvalue in this run; its target variance is positive, but the indefinite full matrix is a further warning against treating its borderline p-value as reliable. No eigenvalues or negative target variances were silently clipped; full diagnostics are exported.

### Restricted wild cluster bootstrap-t by year

| method | year_clusters | replications | observed_t | bootstrap_p | monte_carlo_se |
|---|---|---|---|---|---|
| webb_six_point | 7.0000 | 9999.0000 | 2.9616 | 0.1702 | 0.0038 |
| rademacher_enumerated | 7.0000 | 128.0000 | 2.9616 | 0.2188 | 0.0000 |

Webb six-point weights use 9,999 draws with a fixed seed. The Rademacher diagnostic enumerates all 128 sign patterns. Each imposes theta=0, generates restricted-residual bootstrap outcomes with a common weight per year, refits the full model, and studentises using year-clustered CR1 SE. Exhaustive sign enumeration does not make this an exact randomisation test. Independent year clusters, valid residual approximations and regressor exogeneity are maintained assumptions; serial national shocks and endogenous imports remain unresolved.

## Lead/lag diagnostic

| spec | variable | coefficient | prefecture_cluster_se | p_prefecture_t |
|---|---|---|---|---|
| current_and_next_year_imports | china_lead_x_organic | -0.0193 | 0.0084 | 0.0255 |
| current_and_previous_year_imports | china_lag_x_organic | 0.0037 | 0.0102 | 0.7216 |

These rows jointly include current imports and one adjacent-year series on the same 324 observations. A future-import association would weaken a contemporaneous mechanism, but a null lead would not establish exogeneity. Highly correlated annual imports, anticipatory behaviour and persistent unobservables prevent treating this as a definitive falsification test. Adjacent-year import values come from supplied annual data; lead values include 2024.

## Influence and information

Omitting each prefecture in turn gives interaction coefficients from 0.0333 to 0.0484. All 47 fits are exported. These are influence diagnostics, not independent replications.

| year | cn_import | information_share |
|---|---|---|
| 2017.0000 | 0.3929 | 0.6453 |
| 2018.0000 | 0.6992 | 0.0447 |
| 2019.0000 | 0.5832 | 0.0303 |
| 2020.0000 | 0.7701 | 0.2001 |
| 2021.0000 | 0.6435 | 0.0008 |
| 2022.0000 | 0.6423 | 0.0008 |
| 2023.0000 | 0.7211 | 0.0779 |

Information shares are sums of squared treatment residuals after projecting out baseline nuisance controls. They measure design concentration, not exogenous-shock probabilities or causal weights. Pairwise residual correlations are noisy with seven years and are exported only as descriptive diagnostics.

## What would address the problem

1. Specify the mechanism and target first: imported food consumption, agricultural competition, or another pathway imply different exposure measures and confounders. Do not label the current context interaction as exposure.
2. Obtain pre-2016 prefecture-by-crop exposure weights, with a defensible link to the chosen mechanism. Food purchases, supply-chain deliveries or interregional commodity flows are candidates requiring verification. Port-of-entry trade is not automatically local consumption; local organic production is not automatically a substitute for imported consumption.
3. Construct E_it = sum_k s_ik,pre × M_kt only after validating s. Prefer multiple crop/source shocks rather than one national series. Frozen pre-period weights avoid mechanically using contemporaneous outcomes to define exposure, but do not establish exogeneity.
4. Imports respond to Japanese demand. Consider external supply variation such as origin-country harvest or policy shocks, or exports to destinations excluding Japan, only with a defensible exclusion restriction and documented pre-period shares. Weather, prices and global food shocks can also affect fertility through other channels. Neither an instrument nor shift-share construction is automatically valid.
5. Obtain a longer pre-period and audit pre-trends, regional price/demographic changes, spillovers, share concentration and influential shocks. Test validity at the shock/exposure level as appropriate; conventional prefecture clustering alone may be inadequate.
6. Decide in advance whether identification is justified by the shares, by external shocks, or a specified conditional parallel-trends assumption. Choose inference for that design. Do not manufacture regional exposure by simply allocating national imports by population; per-capita allocation leaves all prefectures with the same exposure.
7. Until those inputs exist, report the interaction as an exploratory national-time-pattern association by organic context. Keep the inability to distinguish heterogeneous common shocks in the main conclusion.

## References

- Borusyak, Hull and Jaravel, A Practical Guide to Shift-Share Instruments: https://www.nber.org/papers/w33236
- Adão, Kolesár and Morales, Shift-Share Designs: Theory and Inference: https://www.nber.org/papers/w24944
- MacKinnon, Nielsen and Webb, Cluster-robust inference: A guide to empirical practice: https://doi.org/10.1016/j.jeconom.2022.04.001
- Statsmodels two-way covariance implementation: https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster_2groups.html
