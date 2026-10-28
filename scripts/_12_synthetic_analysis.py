"""Analyse the labelled synthetic panel and repeat the DGP across random seeds.

python scripts/_12_synthetic_analysis.py --replications 500
Results describe the chosen simulation, not effects in observed Japan.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf

from _11_synthetic_food import ar1

ROOT=Path(__file__).resolve().parents[1]
FOLDER=ROOT/"synthetic"/"food_import_simulation"
LABEL="SYNTHETIC_NOT_OBSERVED"
METHODS=["omit_shock_prefecture_cluster","omit_shock_aggregate_HAC3","oracle_shock_prefecture_cluster"]


def draw(seed,meta):
    rng=np.random.default_rng(seed)
    t=meta["synthetic_periods"];n=meta["synthetic_prefectures"]
    centres=np.array([meta["log_import_centres"]["China"],meta["log_import_centres"]["USA"]])
    deviation=ar1(rng.multivariate_normal([0.,0.],np.array(meta["import_innovation_covariance"]),size=t),meta["import_ar1"])
    time=np.arange(t)
    imports=centres+np.column_stack([meta["log_import_trends"]["China"]*time,
                                   meta["log_import_trends"]["USA"]*time])+deviation
    intercepts=rng.normal(0.,meta["prefecture_intercept_sd"],size=n)
    loading=rng.uniform(*meta["common_loading_range"],size=n)
    unrelated=ar1(rng.normal(0.,meta["independent_common_shock_innovation_sd"],size=t),meta["common_shock_ar1"])
    error=ar1(rng.normal(0.,meta["idiosyncratic_innovation_sd"],size=(t,n)),meta["idiosyncratic_ar1"])
    china=(deviation[:,0]-deviation[:,0].mean())/deviation[:,0].std(ddof=0)
    for scenario,truth in meta["scenarios"].items():
        u=unrelated+truth["confounding_sign"]*meta["confounded_common_shock_scale"]*china
        contribution=u[:,None]*loading[None,:]
        y=(meta["baseline_tfr"]+intercepts[None,:]+meta["tfr_annual_trend"]*time[:,None]+
           truth["china_beta"]*(imports[:,0]-centres[0])[:,None]+
           truth["usa_beta"]*(imports[:,1]-centres[1])[:,None]+contribution+error)
        yield scenario,truth,imports,time,contribution,y


def panel_fit(imports,time,contribution,y,oracle):
    """Within-prefecture OLS, with CR1 factor counting absorbed FE parameters."""
    t,n=y.shape
    x=np.broadcast_to(np.column_stack([imports,time])[:,None,:],(t,n,3)).copy()
    if oracle:
        x=np.concatenate([x,contribution[:,:,None]],axis=2)
    x=(x-x.mean(axis=0,keepdims=True)).reshape(t*n,-1)
    outcome=(y-y.mean(axis=0,keepdims=True)).reshape(-1)
    inverse=np.linalg.pinv(x)
    beta=inverse@outcome
    residual=outcome-x@beta
    assert np.linalg.matrix_rank(x)==x.shape[1]
    # Influence scores avoid materialising an N*T square covariance matrix.
    score=(inverse[:2].T*residual[:,None]).reshape(t,n,2).sum(axis=0)
    k=n+x.shape[1]
    factor=n/(n-1)*(t*n-1)/(t*n-k)
    se=np.sqrt(factor*(score**2).sum(axis=0))
    return beta[:2],se,n-1


def aggregate_fit(imports,time,y):
    x=np.column_stack([np.ones(len(time)),imports,time])
    fitted=sm.OLS(y.mean(axis=1),x).fit()
    robust=fitted.get_robustcov_results(cov_type="HAC",maxlags=3,use_correction=True,use_t=True)
    return robust.params[1:3],robust.bse[1:3],int(fitted.df_resid)


def analyse_draw(seed,meta,replication):
    rows=[]
    for scenario,truth,imports,time,contribution,y in draw(seed,meta):
        estimates=[panel_fit(imports,time,contribution,y,False),aggregate_fit(imports,time,y),
                   panel_fit(imports,time,contribution,y,True)]
        for method,(beta,se,df) in zip(METHODS,estimates):
            cutoff=stats.t.ppf(.975,df)
            for j,country in enumerate(["China","USA"]):
                true=truth["china_beta" if j==0 else "usa_beta"]
                lo=beta[j]-cutoff*se[j];hi=beta[j]+cutoff*se[j]
                p=2*stats.t.sf(abs(beta[j]/se[j]),df)
                rows.append(dict(data_status=LABEL,replication=replication,seed=int(seed),scenario=scenario,
                                 method=method,country=country,true_beta=true,estimated_beta=beta[j],
                                 error=beta[j]-true,se=se[j],reference_df=df,ci_low=lo,ci_high=hi,p=p,
                                 covers_truth=bool(lo<=true<=hi),rejects_zero=bool(p<.05)))
        # For shared national predictors, FE OLS and OLS of equally weighted period means coincide.
        np.testing.assert_allclose(estimates[0][0],estimates[1][0],rtol=1e-8,atol=1e-9)
    return rows


def table(frame,columns):
    f=frame[columns].copy()
    for col in f.select_dtypes(include="number"):
        f[col]=f[col].map(lambda x:f"{x:.4f}")
    return "| "+" | ".join(columns)+" |\n|"+"|".join(["---"]*len(columns))+"|\n"+"\n".join(
        "| "+" | ".join(map(str,r))+" |" for r in f.itertuples(index=False,name=None))


def verify_against_original(meta):
    data=pd.read_csv(FOLDER/"SYNTHETIC_food_import_panel.csv")
    assert data.data_status.eq(LABEL).all()
    for scenario,truth,imports,time,contribution,y in draw(meta["seed"],meta):
        existing=data[data.scenario.eq(scenario)]
        np.testing.assert_allclose(y.reshape(-1),existing.synthetic_tfr.to_numpy(),atol=1e-12)
        for oracle in [False,True]:
            formula="synthetic_tfr ~ log_china_food + log_usa_food + synthetic_period + C(synthetic_prefecture_id)"
            if oracle:
                formula+=" + true_common_shock_contribution"
            direct=smf.ols(formula,existing).fit(cov_type="cluster",cov_kwds={"groups":existing.synthetic_prefecture_id},use_t=True)
            beta,se,_=panel_fit(imports,time,contribution,y,oracle)
            np.testing.assert_allclose(beta,direct.params[["log_china_food","log_usa_food"]],rtol=1e-8,atol=1e-9)
            np.testing.assert_allclose(se,direct.bse[["log_china_food","log_usa_food"]],rtol=1e-8,atol=1e-9)
    # Both import main effects are fully spanned by period FE; synthetic generation does not change this.
    first=data[data.scenario.eq(next(iter(meta["scenarios"])))]
    year_dummies=pd.get_dummies(first.synthetic_period,dtype=float).to_numpy()
    x=first[["log_china_food","log_usa_food"]].to_numpy()
    unexplained=x-year_dummies@np.linalg.lstsq(year_dummies,x,rcond=None)[0]
    assert np.linalg.norm(unexplained)/np.linalg.norm(x)<1e-12


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replications",type=int,default=500)
    parser.add_argument("--monte-carlo-seed",type=int,default=20261029)
    args=parser.parse_args()
    if args.replications<20:
        parser.error("Use at least 20 replications; the default is 500")
    meta=json.loads((FOLDER/"SYNTHETIC_generation_metadata.json").read_text())
    verify_against_original(meta)
    destination=FOLDER/"analysis"
    destination.mkdir(parents=True,exist_ok=True)
    seeded=pd.DataFrame(analyse_draw(meta["seed"],meta,0))
    seeded.to_csv(destination/"SYNTHETIC_seeded_model_results.csv",index=False)
    streams=np.random.SeedSequence(args.monte_carlo_seed).spawn(args.replications)
    all_rows=[]
    for i,stream in enumerate(streams):
        seed=int(stream.generate_state(1)[0])
        all_rows.extend(analyse_draw(seed,meta,i+1))
        if (i+1)%100==0:
            print(f"Completed {i+1}/{args.replications} simulation replications",flush=True)
    draws=pd.DataFrame(all_rows)
    draws.to_csv(destination/"SYNTHETIC_monte_carlo_draws.csv",index=False)
    summaries=[]
    for (scenario,method,country),g in draws.groupby(["scenario","method","country"],sort=False):
        coverage=g.covers_truth.mean();reject=g.rejects_zero.mean();null=bool(g.true_beta.eq(0).all())
        summaries.append(dict(data_status=LABEL,scenario=scenario,method=method,country=country,
                              replications=len(g),true_beta=g.true_beta.iloc[0],mean_estimate=g.estimated_beta.mean(),
                              bias=g.error.mean(),bias_mcse=g.error.std(ddof=1)/np.sqrt(len(g)),
                              rmse=np.sqrt(np.mean(g.error**2)),coverage_95=coverage,
                              coverage_mcse=np.sqrt(coverage*(1-coverage)/len(g)),
                              reject_zero_rate=reject,rejection_mcse=np.sqrt(reject*(1-reject)/len(g)),
                              false_positive_rate=reject if null else np.nan))
    summary=pd.DataFrame(summaries)
    summary.to_csv(destination/"SYNTHETIC_monte_carlo_summary.csv",index=False)
    metadata=dict(data_status=LABEL,original_dataset_seed=meta["seed"],monte_carlo_seed=args.monte_carlo_seed,
                  replications=args.replications,scenarios_per_replication=4,
                  countries_per_model=2,methods=METHODS,
                  synthetic_prefectures=meta["synthetic_prefectures"],synthetic_periods=meta["synthetic_periods"],
                  randomisation="NumPy SeedSequence child streams; innovations and prefectures shared across scenarios within each replication",
                  covariance="Prefecture cluster CR1 with absorbed FE degrees counted; t(G-1). Aggregate HAC Bartlett lag 3 with finite-sample multiplier and t(T-4).",
                  scope="Monte Carlo results are conditional on the chosen DGP, parameter values and sample size; they are not estimates for Japan")
    (destination/"SYNTHETIC_analysis_metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    point=seeded[seeded.method.isin([METHODS[0],METHODS[2]])]
    report=["# SYNTHETIC RESULTS — NOT EMPIRICAL FINDINGS", "",
            f"Analysis of four synthetic scenarios, each with {meta['synthetic_prefectures']} synthetic prefectures and {meta['synthetic_periods']} simulated periods. Country variables are separate and there is no organic interaction. The four scenarios are analysed separately and never pooled with observed data.",
            "", "## Seeded panel results", "",
            "The no-shock-control model includes prefecture effects, a linear time trend and both import series. The oracle model additionally observes the exact common-shock contribution chosen in the generator; this information is unavailable in the real Japanese study. Intervals here use prefecture-clustered CR1 inference. Significant estimates in a true-zero scenario are false positives within this simulation.", "",
            table(point,["scenario","method","country","true_beta","estimated_beta","ci_low","ci_high","p"]),
            "", "The omitted-shock estimate in the known-effect benchmark can have the wrong sign. The oracle comparison shows recovery under privileged knowledge, not a practical solution to the real identification problem. Increasing synthetic prefectures does not create additional observed national shocks.",
            "", "## Repeated-simulation assessment", "",
            f"The full data-generating process was repeated {args.replications} times using independently seeded streams. All methods, scenarios and countries are reported. Scenarios share innovations within a replication, so scenario contrasts are paired; they are not independent replications. Coverage and rejection rates have Monte Carlo uncertainty recorded in the CSV.", "",
            table(summary,["scenario","method","country","bias","rmse","coverage_95","reject_zero_rate"]),
            "", "For the three true-zero scenarios, rejection of zero is the false-positive rate. For the known nonzero benchmark it is power under this particular DGP, including any misspecification. Coverage refers to the chosen true coefficient, with a nominal target of 0.95. Five per cent is the nominal false-positive target only for a validly specified and calibrated test.",
            "", "## Interpretation", "",
            "- Omitted shared shocks can generate positive or negative food-import coefficients with zero true causal effect. More precise estimates of that biased association do not recover the simulated truth.",
            "- Prefecture clustering alone does not allow residual dependence between prefectures from common national shocks. Aggregate HAC treats the national time dimension explicitly, but short samples, persistence and regressor endogeneity can still undermine its inference.",
            "- Better covariance estimates do not remove omitted-variable bias. The oracle control removes a known simulated source of bias, but the true shock contribution is not observed in the empirical analysis.",
            "- Annual fixed effects absorb both national import main effects, even in these synthetic panels. This rank check was verified directly. The simulation does not manufacture regional exposure.",
            "- Results apply to the stated calibration, chosen effects, shock persistence and confounding structure. They do not establish that imports affect fertility, do not prove a zero empirical effect and do not turn the earlier observational study into confirmatory evidence.",
            "", "## Reproduce", "", "```bash", "python scripts/_11_synthetic_food.py",
            f"python scripts/_12_synthetic_analysis.py --replications {args.replications} --monte-carlo-seed {args.monte_carlo_seed}",
            "```", "", "Independent numerical verification compared the within-prefecture estimator and CR1 SE with direct statsmodels dummy-variable regressions for every original scenario and both panel specifications. Generated outcomes reproduce the supplied synthetic CSV exactly. Raw seeded fits, all Monte Carlo draws, summary rates and metadata are included.", ""]
    (destination/"SYNTHETIC_ANALYSIS_RESULTS.md").write_text("\n".join(report))
    (destination/"validation.txt").write_text("Verified exact reconstruction of the original four synthetic panels; panel FE coefficients and CR1 SE against direct dummy regressions; equality of omitted-shock FE and period-mean point estimates in every replication; absorption of both imports by period effects.\n")
    print(summary[["scenario","method","country","bias","coverage_95","reject_zero_rate"]].to_string(index=False))
    print(f"Synthetic analysis saved to {destination}")


if __name__=="__main__":
    main()
