# SYNTHETIC RESULTS — NOT EMPIRICAL FINDINGS

Analysis of four synthetic scenarios, each with 47 synthetic prefectures and 30 simulated periods. Country variables are separate and there is no organic interaction. The four scenarios are analysed separately and never pooled with observed data.

## Seeded panel results

The no-shock-control model includes prefecture effects, a linear time trend and both import series. The oracle model additionally observes the exact common-shock contribution chosen in the generator; this information is unavailable in the real Japanese study. Intervals here use prefecture-clustered CR1 inference. Significant estimates in a true-zero scenario are false positives within this simulation.

| scenario | method | country | true_beta | estimated_beta | ci_low | ci_high | p |
|---|---|---|---|---|---|---|---|
| null_unrelated_common_shocks | omit_shock_prefecture_cluster | China | 0.0000 | -0.0032 | -0.0299 | 0.0234 | 0.8083 |
| null_unrelated_common_shocks | omit_shock_prefecture_cluster | USA | 0.0000 | -0.2187 | -0.2490 | -0.1885 | 0.0000 |
| null_unrelated_common_shocks | oracle_shock_prefecture_cluster | China | 0.0000 | 0.0061 | -0.0205 | 0.0326 | 0.6490 |
| null_unrelated_common_shocks | oracle_shock_prefecture_cluster | USA | 0.0000 | 0.0046 | -0.0275 | 0.0367 | 0.7753 |
| null_positive_shared_confounding | omit_shock_prefecture_cluster | China | 0.0000 | 0.9501 | 0.9027 | 0.9974 | 0.0000 |
| null_positive_shared_confounding | omit_shock_prefecture_cluster | USA | 0.0000 | -0.2187 | -0.2490 | -0.1885 | 0.0000 |
| null_positive_shared_confounding | oracle_shock_prefecture_cluster | China | 0.0000 | -0.0216 | -0.0729 | 0.0297 | 0.4015 |
| null_positive_shared_confounding | oracle_shock_prefecture_cluster | USA | 0.0000 | 0.0013 | -0.0299 | 0.0326 | 0.9331 |
| null_negative_shared_confounding | omit_shock_prefecture_cluster | China | 0.0000 | -0.9565 | -1.0144 | -0.8987 | 0.0000 |
| null_negative_shared_confounding | omit_shock_prefecture_cluster | USA | 0.0000 | -0.2187 | -0.2490 | -0.1885 | 0.0000 |
| null_negative_shared_confounding | oracle_shock_prefecture_cluster | China | 0.0000 | 0.0534 | -0.0042 | 0.1110 | 0.0682 |
| null_negative_shared_confounding | oracle_shock_prefecture_cluster | USA | 0.0000 | 0.0058 | -0.0265 | 0.0380 | 0.7215 |
| known_effect_benchmark | omit_shock_prefecture_cluster | China | -0.0800 | -0.0832 | -0.1099 | -0.0566 | 0.0000 |
| known_effect_benchmark | omit_shock_prefecture_cluster | USA | 0.0400 | -0.1787 | -0.2090 | -0.1485 | 0.0000 |
| known_effect_benchmark | oracle_shock_prefecture_cluster | China | -0.0800 | -0.0739 | -0.1005 | -0.0474 | 0.0000 |
| known_effect_benchmark | oracle_shock_prefecture_cluster | USA | 0.0400 | 0.0446 | 0.0125 | 0.0767 | 0.0075 |

The omitted-shock estimate in the known-effect benchmark can have the wrong sign. The oracle comparison shows recovery under privileged knowledge, not a practical solution to the real identification problem. Increasing synthetic prefectures does not create additional observed national shocks.

## Repeated-simulation assessment

The full data-generating process was repeated 500 times using independently seeded streams. All methods, scenarios and countries are reported. Scenarios share innovations within a replication, so scenario contrasts are paired; they are not independent replications. Coverage and rejection rates have Monte Carlo uncertainty recorded in the CSV.

| scenario | method | country | bias | rmse | coverage_95 | reject_zero_rate |
|---|---|---|---|---|---|---|
| null_unrelated_common_shocks | omit_shock_prefecture_cluster | China | -0.0047 | 0.1069 | 0.2220 | 0.7780 |
| null_unrelated_common_shocks | omit_shock_prefecture_cluster | USA | -0.0028 | 0.1068 | 0.2120 | 0.7880 |
| null_unrelated_common_shocks | omit_shock_aggregate_HAC3 | China | -0.0047 | 0.1069 | 0.8620 | 0.1380 |
| null_unrelated_common_shocks | omit_shock_aggregate_HAC3 | USA | -0.0028 | 0.1068 | 0.8460 | 0.1540 |
| null_unrelated_common_shocks | oracle_shock_prefecture_cluster | China | 0.0005 | 0.0143 | 0.9440 | 0.0560 |
| null_unrelated_common_shocks | oracle_shock_prefecture_cluster | USA | -0.0001 | 0.0129 | 0.9700 | 0.0300 |
| null_positive_shared_confounding | omit_shock_prefecture_cluster | China | 0.8510 | 0.8706 | 0.0000 | 1.0000 |
| null_positive_shared_confounding | omit_shock_prefecture_cluster | USA | -0.0028 | 0.1068 | 0.2120 | 0.7880 |
| null_positive_shared_confounding | omit_shock_aggregate_HAC3 | China | 0.8510 | 0.8706 | 0.0000 | 1.0000 |
| null_positive_shared_confounding | omit_shock_aggregate_HAC3 | USA | -0.0028 | 0.1068 | 0.8460 | 0.1540 |
| null_positive_shared_confounding | oracle_shock_prefecture_cluster | China | 0.0010 | 0.0289 | 0.9480 | 0.0520 |
| null_positive_shared_confounding | oracle_shock_prefecture_cluster | USA | -0.0001 | 0.0130 | 0.9640 | 0.0360 |
| null_negative_shared_confounding | omit_shock_prefecture_cluster | China | -0.8605 | 0.8788 | 0.0000 | 1.0000 |
| null_negative_shared_confounding | omit_shock_prefecture_cluster | USA | -0.0028 | 0.1068 | 0.2120 | 0.7880 |
| null_negative_shared_confounding | omit_shock_aggregate_HAC3 | China | -0.8605 | 0.8788 | 0.0000 | 1.0000 |
| null_negative_shared_confounding | omit_shock_aggregate_HAC3 | USA | -0.0028 | 0.1068 | 0.8460 | 0.1540 |
| null_negative_shared_confounding | oracle_shock_prefecture_cluster | China | -0.0013 | 0.0265 | 0.9660 | 0.0340 |
| null_negative_shared_confounding | oracle_shock_prefecture_cluster | USA | -0.0001 | 0.0128 | 0.9720 | 0.0280 |
| known_effect_benchmark | omit_shock_prefecture_cluster | China | -0.0047 | 0.1069 | 0.2220 | 0.8500 |
| known_effect_benchmark | omit_shock_prefecture_cluster | USA | -0.0028 | 0.1068 | 0.2120 | 0.8060 |
| known_effect_benchmark | omit_shock_aggregate_HAC3 | China | -0.0047 | 0.1069 | 0.8620 | 0.2720 |
| known_effect_benchmark | omit_shock_aggregate_HAC3 | USA | -0.0028 | 0.1068 | 0.8460 | 0.1860 |
| known_effect_benchmark | oracle_shock_prefecture_cluster | China | 0.0005 | 0.0143 | 0.9440 | 0.9980 |
| known_effect_benchmark | oracle_shock_prefecture_cluster | USA | -0.0001 | 0.0129 | 0.9700 | 0.8160 |

For the three true-zero scenarios, rejection of zero is the false-positive rate. For the known nonzero benchmark it is power under this particular DGP, including any misspecification. Coverage refers to the chosen true coefficient, with a nominal target of 0.95. Five per cent is the nominal false-positive target only for a validly specified and calibrated test.

## Interpretation

- Omitted shared shocks can generate positive or negative food-import coefficients with zero true causal effect. More precise estimates of that biased association do not recover the simulated truth.
- Prefecture clustering alone does not allow residual dependence between prefectures from common national shocks. Aggregate HAC treats the national time dimension explicitly, but short samples, persistence and regressor endogeneity can still undermine its inference.
- Better covariance estimates do not remove omitted-variable bias. The oracle control removes a known simulated source of bias, but the true shock contribution is not observed in the empirical analysis.
- Annual fixed effects absorb both national import main effects, even in these synthetic panels. This rank check was verified directly. The simulation does not manufacture regional exposure.
- Results apply to the stated calibration, chosen effects, shock persistence and confounding structure. They do not establish that imports affect fertility, do not prove a zero empirical effect and do not turn the earlier observational study into confirmatory evidence.

## Reproduce

```bash
python scripts/_11_synthetic_food.py
python scripts/_12_synthetic_analysis.py --replications 500 --monte-carlo-seed 20261029
```

Independent numerical verification compared the within-prefecture estimator and CR1 SE with direct statsmodels dummy-variable regressions for every original scenario and both panel specifications. Generated outcomes reproduce the supplied synthetic CSV exactly. Raw seeded fits, all Monte Carlo draws, summary rates and metadata are included.
