"""Controlled ANOVA and multiplicity-adjusted prefecture contrasts.

Each prefecture is compared with the equally weighted adjusted prefectural mean.
"""
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multitest import multipletests

from _13_ml_sensitivity_projections import table

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"output/subregion_anova"


def ptable(frame,columns):
    display=frame.copy()
    for col in ["p_classical","year_cluster_p","year_cluster_Holm_p","wild_cluster_p"]:
        if col in display:
            display[col]=display[col].map(lambda p:f"{p:.3g}" if pd.notna(p) else "—")
    return table(display,columns)


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    data=pd.read_csv(ROOT/"output/controlled_food_regressions/balanced_analysis_data.csv")
    assert len(data)==329 and data.groupby("year").size().eq(47).all()
    formula="tfr_children_per_woman ~ C(region_code) + log_food + trend + log_income + log_eating_out"
    classical=smf.ols(formula,data,missing="raise").fit()
    clustered=smf.ols(formula,data,missing="raise").fit(cov_type="cluster",cov_kwds={"groups":data.year,"use_correction":True,"df_correction":True},use_t=True)
    anova=anova_lm(classical,typ=2).reset_index().rename(columns={"index":"term","PR(>F)":"p_classical"})
    anova["inference_assumption"]="Classical conditional iid homoskedastic errors; not cluster-robust"
    anova.to_csv(DEST/"ANOVA_type_II_classical.csv",index=False)
    # Standardise all prefectures to the same values of the continuous controls.
    grid=data[["region_code","prefecture"]].drop_duplicates().sort_values("region_code").reset_index(drop=True)
    for col in ["log_food","trend","log_income","log_eating_out"]:
        grid[col]=data[col].mean()
    design=np.stack([classical.model.exog[np.flatnonzero(data.region_code.eq(code).to_numpy())[0]].copy()
                     for code in grid.region_code])
    for col in ["log_food","trend","log_income","log_eating_out"]:
        design[:,classical.model.exog_names.index(col)]=data[col].mean()
    contrasts=design-design.mean(axis=0)
    beta=np.asarray(classical.params);cov=np.asarray(clustered.cov_params())
    effects=contrasts@beta
    se=np.sqrt(np.einsum('ij,jk,ik->i',contrasts,cov,contrasts))
    df=float(clustered.df_resid_inference)
    p=2*t.sf(abs(effects/se),df)
    iid_se=np.sqrt(np.einsum('ij,jk,ik->i',contrasts,np.asarray(classical.cov_params()),contrasts))
    iid_p=2*t.sf(abs(effects/iid_se),classical.df_resid)
    # Null-restricted wild residual bootstrap for each centred regional contrast.
    X=classical.model.exog;y=classical.model.endog;pinv=np.linalg.pinv(X)
    bread=pinv@pinv.T
    bootstrap_beta=pinv@y
    observed_residual=y-X@bootstrap_beta
    years,inverse=np.unique(data.year,return_inverse=True);g=len(years);n,k=X.shape
    signs=np.array(list(itertools.product([-1.,1.],repeat=g)))
    correction=g/(g-1)*(n-1)/(n-k)
    boot_p=[]
    for i,L in enumerate(contrasts):
        restricted_beta=bootstrap_beta-(bread@L)*((L@bootstrap_beta)/(L@bread@L))
        fitted=X@restricted_beta;errors=y-fitted
        outcomes=fitted[:,None]+errors[:,None]*signs[:,inverse].T
        betas=pinv@outcomes;residual=outcomes-X@betas
        weights=L@pinv
        scores=np.stack([(weights[inverse==j,None]*residual[inverse==j]).sum(axis=0) for j in range(g)])
        bootstrap_se=np.sqrt(correction*np.sum(scores**2,axis=0))
        statistics=(L@betas)/bootstrap_se
        observed_scores=np.array([np.dot(weights[inverse==j],observed_residual[inverse==j]) for j in range(g)])
        assert np.isclose(np.sqrt(correction*np.sum(observed_scores**2)),se[i],rtol=1e-7)
        assert np.isclose(L@restricted_beta,0,atol=1e-9)
        observed_stat=abs((L@bootstrap_beta)/np.sqrt(correction*np.sum(observed_scores**2)))
        # Count numerical ties consistently; all-positive/all-negative signs
        # reproduce the observed absolute statistic under the imposed null.
        absolute=np.abs(statistics)
        exceed=(absolute>observed_stat)|np.isclose(absolute,observed_stat,rtol=1e-7,atol=1e-8)
        probability=float(exceed.mean())
        assert probability>=2/len(signs)
        boot_p.append(probability)
    result=grid[["region_code","prefecture"]].copy()
    result["unadjusted_mean_tfr"]=result.region_code.map(data.groupby("region_code").tfr_children_per_woman.mean())
    result["adjusted_tfr_at_common_controls"]=design@beta
    result["difference_from_adjusted_prefecture_mean"]=effects
    result["year_cluster_se"]=se
    result["year_cluster_p"]=p
    result["year_cluster_Holm_p"]=multipletests(p,method="holm")[1]
    result["year_cluster_Holm_significant_5pct"]=result.year_cluster_Holm_p.lt(.05)
    result["year_cluster_pointwise_ci_low"]=effects-t.ppf(.975,df)*se
    result["year_cluster_pointwise_ci_high"]=effects+t.ppf(.975,df)*se
    result["classical_p"]=iid_p
    result["classical_Holm_p"]=multipletests(iid_p,method="holm")[1]
    result["wild_cluster_p"]=boot_p
    result["wild_cluster_Holm_p"]=multipletests(boot_p,method="holm")[1]
    result["wild_cluster_Holm_significant_5pct"]=result.wild_cluster_Holm_p.lt(.05)
    result.to_csv(DEST/"significance_each_prefecture.csv",index=False)
    # No 46-df omnibus cluster Wald test is interpreted with seven year clusters.
    region_indexes=[i for i,name in enumerate(classical.model.exog_names) if name.startswith('C(region_code)')]
    regional_cov=cov[np.ix_(region_indexes,region_indexes)]
    rank=int(np.linalg.matrix_rank(regional_cov,tol=1e-10))
    metadata=dict(outcome="Prefectural TFR",sample="329 records; 47 prefectures; 2016–2022; seven year clusters",formula=formula,
                  reference="Equally weighted mean of all 47 adjusted prefectural predictions at common mean log-controls and time",
                  comparison="Each regional adjusted effect minus the average regional effect; these are not regional food-import slopes",
                  multiplicity="Holm correction over all 47 prefecture-versus-mean tests separately for each inference method",
                  clustered_t_df=df,regional_cluster_covariance_rank=rank,regional_parameters=46,
                  omnibus_limit="Classical Type II ANOVA only. A 46-parameter year-clustered omnibus Wald test is rank-deficient with seven year clusters and is not reported as valid.",
                  bootstrap="Restricted Rademacher residual bootstrap, CR1 studentisation, all 128 year-sign patterns. Approximate diagnostic, not exact randomisation inference.",
                  bootstrap_resolution="Sign symmetry gives a minimum attainable two-sided p of 2/128 = 0.015625. With 47 Holm comparisons, none can pass 0.05; this is a conservative resolution limit, not proof of no regional differences.",
                  limits="Only seven years; potential dependence across years, heterogeneous regional trends, endogenous proxy controls and national common shocks remain. Pointwise intervals are not simultaneous family intervals. Descriptive in-sample associations, no causal interpretation.")
    (DEST/"methods.json").write_text(json.dumps(metadata,indent=2)+"\n")
    overall=anova.loc[anova.term.eq("C(region_code)")].iloc[0]
    count=int(result.year_cluster_Holm_significant_5pct.sum())
    report=["# ANOVA and significance for every prefecture", "",
        "Outcome: prefectural TFR. Predictor/control model: prefecture categories + log total national food imports + log prefectural income + log capital-city eating-out expenditure + common linear time trend. The balanced observed-control sample is 47 prefectures × 2016–2022, 329 rows. No missing controls are imputed.", "",
        "## Overall ANOVA", "",ptable(anova,["term","sum_sq","df","F","p_classical"]), "",
        f"The conventional Type II prefecture test gives F = {overall.F:.3f} with {int(overall.df)} numerator and {int(classical.df_resid)} residual degrees of freedom; p = {overall.p_classical:.3e}. This is a classical iid-error benchmark, not robust evidence under panel dependence. The year-clustered covariance for the 46 regional parameters has rank {rank}, so a 46-df cluster-robust omnibus Wald test is not interpreted.", "",
        "## Significance for each prefecture", "",
        "ANOVA supplies an overall test, not a separate significance label for each category. The comparisons below test each prefecture's adjusted TFR difference from the equally weighted adjusted mean across all 47 prefectures. Continuous covariates are held at common sample mean log-values/time. The regional mean comparator includes that region with weight 1/47. These are regional level differences, not prefecture-specific import effects.", "",
        "Year-clustered p-values use six t degrees of freedom; Holm adjustment controls the 47-comparison family under valid individual tests. Seven clusters are few and arbitrary temporal dependence is not handled. Confidence intervals in the CSV are pointwise, not simultaneous. The significance labels are conditional on this inference model.", "",
        ptable(result,["prefecture","difference_from_adjusted_prefecture_mean","year_cluster_p","year_cluster_Holm_p","year_cluster_Holm_significant_5pct","wild_cluster_p"]), "",
        f"{count}/47 prefectures meet the 5% Holm threshold under the conventional year-clustered t approximation. The CSV also includes unadjusted means, adjusted predictions, standard errors, confidence intervals and classical-test sensitivity for every prefecture.", "",
        "## Small-cluster bootstrap sensitivity", "",
        "All 128 Rademacher year-sign patterns are evaluated after imposing each contrast's null. This is an approximate restricted residual-bootstrap diagnostic under independent clusters and symmetry assumptions. The minimum attainable two-sided p-value is 2/128 = 0.015625. Consequently no comparison can pass a 47-test Holm adjustment at 5%. This is a resolution/conservatism limit, not evidence that the regional rates are equal. Nominal significance under the cluster-t approximation should therefore not be described as robustly established by this bootstrap.", "",
        "Income and spending proxies may be endogenous, and adjustment does not make a location effect causal. National food imports are common within year. Unrestricted year effects would absorb food imports; the current time trend is a modelling restriction.", "",
        "## Graphs", "",
        "![Adjusted TFR differences with pointwise year-clustered intervals](figures/prefecture_adjusted_tfr_differences.png)", "",
        "![Holm-corrected significance under three inference methods](figures/prefecture_significance_inference_sensitivity.png)", "",
        "![Classical Type II ANOVA terms](figures/controlled_anova_classical_terms.png)", "",
        "## Reproduce", "", "```bash", "python scripts/_22_subregion_anova.py", "python scripts/_23_plot_subregion_anova.py", "```", ""]
    (DEST/"ANOVA_AND_SUBREGION_SIGNIFICANCE.md").write_text("\n".join(report))
    print(anova.to_string(index=False))
    print(f'Year-cluster Holm significant: {count}/47; regional covariance rank {rank}/46')
    print(result[["prefecture","difference_from_adjusted_prefecture_mean","year_cluster_p","year_cluster_Holm_p","wild_cluster_p"]].to_string(index=False))


if __name__=="__main__":
    main()
