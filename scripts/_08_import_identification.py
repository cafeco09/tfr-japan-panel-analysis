"""National-import identification stress tests; descriptive, not causal validation.

python scripts/_08_import_identification.py
Uses only supplied data; does not alter the existing pipeline or source CSVs.
"""
from itertools import product
from pathlib import Path
import json
import sys

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.sandwich_covariance import cov_cluster, cov_cluster_2groups

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _00_load import DATA, OUT, load_full_panel, load_period_panel

DEST = Path(OUT)/"import_identification"
BASE = "tfr ~ log_income + log_eating_out + C(region_code) + C(year)"
TARGET = "china_x_organic"
SEED = 20261028


def model(formula, data):
    result=smf.ols(formula,data=data,missing="raise").fit()
    rank=np.linalg.matrix_rank(result.model.exog)
    if rank!=result.model.exog.shape[1]:
        raise ValueError(f"Not full rank: {rank}/{result.model.exog.shape[1]} {formula}")
    return result


def estimate(name, result, data, variable=TARGET):
    j=result.model.exog_names.index(variable)
    codes=pd.factorize(data.region_code)[0]
    covariance=cov_cluster(result,codes,use_correction=True)
    se=np.sqrt(covariance[j,j])
    df=data.region_code.nunique()-1
    beta=result.params[variable]
    cutoff=stats.t.ppf(.975,df)
    return dict(spec=name,variable=variable,coefficient=beta,prefecture_cluster_se=se,
                p_prefecture_t=2*stats.t.sf(abs(beta/se),df),ci_low=beta-cutoff*se,ci_high=beta+cutoff*se,
                n=len(data),prefectures=data.region_code.nunique(),years=data.year.nunique(),
                rank=np.linalg.matrix_rank(result.model.exog),columns=result.model.exog.shape[1])


def residualise(x, controls):
    return x-controls@np.linalg.lstsq(controls,x,rcond=None)[0]


def bootstrap_year(result,data,distribution,draws=9999):
    """Restricted wild cluster bootstrap-t with year clusters, CR1 studentisation.

    Webb six-point weights are Monte Carlo; Rademacher weights enumerate 2**G.
    Neither yields an exact randomisation test or addresses serial year dependence.
    """
    x=result.model.exog
    y=result.model.endog
    j=result.model.exog_names.index(TARGET)
    groups=pd.factorize(data.year,sort=True)[0]
    g=len(np.unique(groups))
    n,k=x.shape
    pinv=np.linalg.pinv(x)
    influence=pinv[j]
    restricted=np.delete(x,j,axis=1)
    y0=restricted@np.linalg.lstsq(restricted,y,rcond=None)[0]
    e0=y-y0
    correction=g/(g-1)*(n-1)/(n-k)
    observed_se=np.sqrt(cov_cluster(result,groups,use_correction=True)[j,j])
    observed_t=result.params[TARGET]/observed_se
    if distribution=="rademacher_enumerated":
        weights=np.array(list(product([-1.,1.],repeat=g))).T
    else:
        support=np.array([-np.sqrt(1.5),-1.,-np.sqrt(.5),np.sqrt(.5),1.,np.sqrt(1.5)])
        weights=np.random.default_rng(SEED).choice(support,size=(g,draws))
    simulated=y0[:,None]+e0[:,None]*weights[groups]
    beta=pinv@simulated
    residuals=simulated-x@beta
    scores=np.vstack([(influence[groups==c,None]*residuals[groups==c]).sum(axis=0)
                       for c in range(g)])
    se=np.sqrt(correction*(scores**2).sum(axis=0))
    tstar=beta[j]/se
    assert np.isfinite(tstar).all()
    count=int((abs(tstar)>=abs(observed_t)-1e-12).sum())
    b=len(tstar)
    p=(count+1)/(b+1) if distribution=="webb_six_point" else count/b
    pd.DataFrame({"bootstrap_t":tstar}).to_csv(DEST/f"bootstrap_{distribution}_draws.csv",index=False)
    return dict(method=distribution,year_clusters=g,replications=b,seed=SEED,
                observed_t=observed_t,bootstrap_p=p,
                monte_carlo_se=(np.sqrt(p*(1-p)/b) if distribution=="webb_six_point" else 0.),
                caveat="Independent-year cluster assumption; seven years; not an exact randomisation test; not causal validation")


def markdown_table(frame,columns):
    f=frame[columns].copy()
    for col in f.select_dtypes(include="number"):
        f[col]=f[col].map(lambda x:f"{x:.4f}" if pd.notna(x) else "—")
    return "| "+" | ".join(columns)+" |\n|"+"|".join(["---"]*len(columns))+"|\n"+"\n".join(
        "| "+" | ".join(map(str,r))+" |" for r in f.itertuples(index=False,name=None))


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    annual=load_full_panel()
    period=load_period_panel()
    key=["region_code","tfr","eating_out"]
    period=period.merge(annual[key+["year"]],on=key,how="left",validate="one_to_one")
    assert period.year.notna().all()
    data=period[period.eligible_observed_income_regression.eq(True)].copy()
    data=data.sort_values(["year","region_code"]).reset_index(drop=True)
    raw=pd.read_csv(Path(DATA)/"dated_source_panel_2016_2025.csv")
    imports=raw.groupby("year").china_national_crop_import_kg_per_resident.first()
    assert raw.groupby("year").china_national_crop_import_kg_per_resident.nunique().eq(1).all()
    assert data.groupby("region_code").organic_farming_context_z.nunique().eq(1).all()
    snapshots=pd.read_csv(Path(DATA)/"input_organic_gardening_snapshots.csv")
    context=period.drop_duplicates("region_code")[["region_code","organic_farming_context_z"]]
    snapshot_check=context.merge(snapshots,on="region_code",validate="one_to_one")
    shares=snapshot_check.organic_census_reporting_operations/snapshot_check.organic_census_all_farm_operations
    reconstructed=(shares-shares.mean())/shares.std(ddof=0)
    np.testing.assert_allclose(reconstructed,snapshot_check.organic_farming_context_z,atol=1e-12)
    context_mean=context.organic_farming_context_z.mean()
    data["org"]=data.organic_farming_context_z-context_mean
    data["m"]=data.cn_import-imports.loc[sorted(data.year.unique())].mean()
    data[TARGET]=data.org*data.m
    data["year_c"]=data.year-data.year.min()
    data["org_trend"]=data.org*data.year_c
    data["org_trend2"]=data.org*data.year_c**2
    for year in [2020,2021,2022]:
        data[f"org_{year}"]=data.org*data.year.eq(year)
    data["china_lead_x_organic"]=data.org*data.year.map(lambda year:imports.loc[year+1])
    data["china_lag_x_organic"]=data.org*data.year.map(lambda year:imports.loc[year-1])
    # Explicitly defined geographic blocks; this is a sensitivity partition, not new data.
    def block(region):
        code=int(region.split("-")[1])
        for limit,label in [(1,"Hokkaido"),(7,"Tohoku"),(14,"Kanto"),(23,"Chubu"),
                            (30,"Kinki"),(35,"Chugoku"),(39,"Shikoku"),(47,"Kyushu_Okinawa")]:
            if code<=limit:
                return label
        raise ValueError(region)
    data["block"]=data.region_code.map(block)
    block_terms=[]
    new_columns={}
    years=sorted(data.year.unique())
    for label in sorted(data.block.unique())[1:]:
        for year in years[1:]:
            name=f"block_{label}_{year}"
            new_columns[name]=data.block.eq(label).astype(int)*data.year.eq(year).astype(int)
            block_terms.append(name)
    trend_terms=[]
    for region in sorted(data.region_code.unique())[1:]:
        name="trend_"+region.replace("-","_")
        new_columns[name]=data.region_code.eq(region).astype(int)*data.year_c
        trend_terms.append(name)
    data=pd.concat([data,pd.DataFrame(new_columns,index=data.index)],axis=1)
    specifications={
        "annual_FE":BASE+" + "+TARGET,
        "organic_linear_trend":BASE+" + "+TARGET+" + org_trend",
        "organic_quadratic_trend":BASE+" + "+TARGET+" + org_trend + org_trend2",
        "organic_pandemic_year_shocks":BASE+" + "+TARGET+" + org_2020 + org_2021 + org_2022",
        "organic_trend_and_pandemic_shocks":BASE+" + "+TARGET+" + org_trend + org_2020 + org_2021 + org_2022",
        "prefecture_specific_linear_trends":BASE+" + "+TARGET+" + "+" + ".join(trend_terms),
        "geographic_block_by_year_effects":BASE+" + "+TARGET+" + "+" + ".join(block_terms),
        "current_and_next_year_imports":BASE+" + "+TARGET+" + china_lead_x_organic",
        "current_and_previous_year_imports":BASE+" + "+TARGET+" + china_lag_x_organic",
        "no_contemporaneous_income_or_eating_out":"tfr ~ C(region_code) + C(year) + "+TARGET,
    }
    fitted={name:model(formula,data) for name,formula in specifications.items()}
    baseline=fitted["annual_FE"]
    # Residual variation retained: comparison of treatment information after nuisance controls.
    def treatment_residual(result):
        j=result.model.exog_names.index(TARGET)
        return residualise(result.model.exog[:,j],np.delete(result.model.exog,j,axis=1))
    baseline_r=treatment_residual(baseline)
    spec_rows=[]
    for name,result in fitted.items():
        row=estimate(name,result,data)
        row["treatment_information_fraction_vs_baseline"]=float(np.sum(treatment_residual(result)**2)/np.sum(baseline_r**2))
        spec_rows.append(row)
    specs=pd.DataFrame(spec_rows)
    specs.to_csv(DEST/"shared_shock_sensitivity.csv",index=False)
    lead_rows=[]
    for name,var in [("current_and_next_year_imports","china_lead_x_organic"),
                     ("current_and_previous_year_imports","china_lag_x_organic")]:
        lead_rows.append(estimate(name,fitted[name],data,var))
    pd.DataFrame(lead_rows).to_csv(DEST/"lead_lag_coefficients.csv",index=False)

    # Covariance sensitivity for precisely the same fitted regression.
    year_codes=pd.factorize(data.year)[0]
    pref_codes=pd.factorize(data.region_code)[0]
    j=baseline.model.exog_names.index(TARGET)
    two_way,_,_=cov_cluster_2groups(baseline,pref_codes,year_codes,use_correction=True)
    covariance_rows=[]
    for label,cov,df in [
        ("prefecture_clusters_47",cov_cluster(baseline,pref_codes),46),
        ("year_clusters_7",cov_cluster(baseline,year_codes),6),
        ("two_way_prefecture_and_year",two_way,6),
    ]:
        variance=cov[j,j]
        se=np.sqrt(variance) if variance>=0 else np.nan
        coefficient=baseline.params[TARGET]
        cutoff=stats.t.ppf(.975,df)
        covariance_rows.append(dict(method=label,coefficient=coefficient,se=se,reference_df=df,
                                    p=2*stats.t.sf(abs(coefficient/se),df),
                                    ci_low=coefficient-cutoff*se,ci_high=coefficient+cutoff*se,
                                    min_covariance_eigenvalue=float(np.linalg.eigvalsh(cov).min()),
                                    warning="Few-year sensitivity only; year clustering does not allow serial correlation across years"))
    covariances=pd.DataFrame(covariance_rows)
    covariances.to_csv(DEST/"covariance_sensitivity.csv",index=False)
    boot=pd.DataFrame([bootstrap_year(baseline,data,"webb_six_point"),
                       bootstrap_year(baseline,data,"rademacher_enumerated")])
    boot.to_csv(DEST/"wild_year_bootstrap.csv",index=False)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(14,7),gridspec_kw={"width_ratios":[1.5,1]})
    positions=np.arange(len(specs))[::-1]
    axes[0].errorbar(specs.coefficient,positions,
                    xerr=np.vstack([specs.coefficient-specs.ci_low,specs.ci_high-specs.coefficient]),
                    fmt="o",color="#176475",capsize=3)
    axes[0].set_yticks(positions,specs.spec.str.replace("_"," "),fontsize=8)
    axes[0].axvline(0,color="grey",linestyle="--",linewidth=1)
    axes[0].set_xlabel("China import × organic-context coefficient")
    axes[0].set_title("Specification sensitivity\n95% prefecture-clustered t intervals",fontsize=11)
    draws=pd.read_csv(DEST/"bootstrap_webb_six_point_draws.csv").bootstrap_t
    axes[1].hist(draws,bins=65,density=True,color="#bed7dc",edgecolor="white")
    obs=boot.iloc[0].observed_t
    for threshold in [-obs,obs]:
        axes[1].axvline(threshold,color="#b43e33",linestyle="--",linewidth=1.5)
    axes[1].set_xlabel("Null-imposed bootstrap t statistic")
    axes[1].set_ylabel("Density")
    axes[1].set_title(f"Seven year clusters; Webb weights\n9,999 draws; bootstrap p = {boot.iloc[0].bootstrap_p:.3f}",fontsize=11)
    fig.suptitle("Import interaction: shared-shock diagnostics",fontsize=15)
    fig.text(.5,.02,"Sensitivity checks do not establish causal identification. Bootstrap assumes independent year clusters.",ha="center",fontsize=9)
    fig.tight_layout(rect=(0,.05,1,.94))
    fig.savefig(DEST/"import_identification_diagnostics.png",dpi=170)
    plt.close(fig)

    # Influence checks: report all, without excluding observations in the main model.
    leave_rows=[]
    for region in sorted(data.region_code.unique()):
        sample=data[data.region_code.ne(region)].copy()
        leave_rows.append(estimate(region,model(specifications["annual_FE"],sample),sample))
    leave=pd.DataFrame(leave_rows)
    leave.to_csv(DEST/"interaction_leave_one_prefecture_out.csv",index=False)
    annual_information=data[["year","cn_import"]].drop_duplicates().sort_values("year")
    annual_information["partial_treatment_sum_squares"]=data.assign(info=baseline_r**2).groupby("year").info.sum().reindex(annual_information.year).to_numpy()
    annual_information["information_share"]=annual_information.partial_treatment_sum_squares/annual_information.partial_treatment_sum_squares.sum()
    annual_information.to_csv(DEST/"annual_treatment_information.csv",index=False)

    # Non-identification proof: arbitrary organic-context × year shocks span the import interaction.
    saturated=data.copy()
    shock_terms=[]
    for year in years[1:]:
        name=f"org_year_{year}"
        saturated[name]=saturated.org*saturated.year.eq(year)
        shock_terms.append(name)
    unrestricted=model(BASE+" + "+" + ".join(shock_terms),saturated)
    z=unrestricted.model.exog
    y=unrestricted.model.endog
    treatment=data[TARGET].to_numpy()
    unspanned=residualise(treatment,z)
    ratio=np.linalg.norm(unspanned)/np.linalg.norm(treatment)
    assert ratio<1e-10
    proof=[]
    for theta in [-baseline.params[TARGET],0.,baseline.params[TARGET]]:
        nuisance=np.linalg.lstsq(z,y-theta*treatment,rcond=None)[0]
        predicted=theta*treatment+z@nuisance
        proof.append(dict(imposed_import_interaction=theta,ssr=float(np.sum((y-predicted)**2)),
                          max_prediction_difference_vs_unrestricted=float(np.max(abs(predicted-unrestricted.fittedvalues)))))
    pd.DataFrame(proof).to_csv(DEST/"nonidentification_demonstration.csv",index=False)
    assert np.ptp([v["ssr"] for v in proof])<1e-10

    # Contemporaneous regional residual dependence, descriptive only.
    residual_matrix=data.assign(residual=baseline.resid).pivot(index="year",columns="region_code",values="residual")
    corr=residual_matrix.corr(min_periods=5).to_numpy()
    offdiag=corr[np.triu_indices_from(corr,k=1)]
    diagnostics=dict(source_sample="47 prefectures; observed-income period-file rows, 2017–2023",
                     n=len(data),years=list(map(int,years)),organic_snapshot_year=2020,
                     organic_context_definition="z-score (ddof=0) of organic-reporting operations / all farm operations across 47 prefectures",
                     snapshot_z_max_reconstruction_error=float(np.max(abs(reconstructed-snapshot_check.organic_farming_context_z))),
                     saturated_context_year_residual_treatment_norm_fraction=float(ratio),
                     median_abs_pairwise_residual_correlation=float(np.nanmedian(abs(offdiag))),
                     correlation_caveat="Only 6–7 annual observations per pair; descriptive, not a calibrated dependence test",
                     bootstrap_seed=SEED,geographic_blocks={k:sorted(v.region_code.unique().tolist()) for k,v in data.groupby("block")})
    (DEST/"identification_checks.json").write_text(json.dumps(diagnostics,indent=2)+"\n")
    sources=[
        "Borusyak, Hull and Jaravel, A Practical Guide to Shift-Share Instruments: https://www.nber.org/papers/w33236",
        "Adão, Kolesár and Morales, Shift-Share Designs: Theory and Inference: https://www.nber.org/papers/w24944",
        "MacKinnon, Nielsen and Webb, Cluster-robust inference: A guide to empirical practice: https://doi.org/10.1016/j.jeconom.2022.04.001",
        "Statsmodels two-way covariance implementation: https://www.statsmodels.org/stable/generated/statsmodels.stats.sandwich_covariance.cov_cluster_2groups.html",
    ]
    report=["# National imports: identification and shared-shock audit", "", "28 October 2026. All results use the supplied data. No new exposure data were invented or imputed.",
            "", "## Finding", "",
            "The national import series multiplied by organic context identifies a differential temporal association under restrictions on context-specific national shocks. It does not identify prefecture-specific import exposure, a national average import effect, or an organic-farming protection mechanism.",
            "", f"In this run, the baseline interaction is {baseline.params[TARGET]:+.4f} (prefecture-clustered p = {specs.iloc[0].p_prefecture_t:.4f}). Adding organic-context trends and separate pandemic-year responses gives {specs.loc[specs.spec.eq('organic_trend_and_pandemic_shocks'),'coefficient'].iloc[0]:+.4f} (p = {specs.loc[specs.spec.eq('organic_trend_and_pandemic_shocks'),'p_prefecture_t'].iloc[0]:.3f}). The year-clustered Webb bootstrap p-value is {boot.iloc[0].bootstrap_p:.3f}. These are evidence of sensitivity, not proof of a zero effect.",
            "", "![Specification and bootstrap diagnostics](import_identification_diagnostics.png)",
            "", "The core identifying restriction is substantive: after controls and fixed effects, omitted national shocks must not differentially move fertility along the organic-context gradient in a way correlated with imports. Year effects remove equal-loading common shocks, not heterogeneous responses to those shocks. Baseline imports, COVID, food prices, urbanisation, marriage and migration can share time patterns; adding annual FE alone does not resolve this.",
            "", "## Data and timing", "",
            "- Primary comparison: the same 324 eligible rows, 47 prefectures, 2017–2023. There are seven national import values, not 324 independent import shocks. The precision of inference also depends on the maintained cross-prefecture error assumptions; counting shocks alone does not determine all possible inferential validity.",
            "- Organic context is exactly the standardised share of farms reporting organic activity in the 2020 census. It is not a local imported-food consumption share, pesticide measurement or pre-2017 exposure measure. It includes uncertified operations. Its timing raises the possibility of post-treatment measurement; it cannot simply be assumed exogenous.",
            "- Country-of-origin kilograms of a crop basket are not chemical residues, individual consumption, or biologically relevant dose. No health mechanism can be inferred from this interaction.",
            "- Centring imports and organic context changes only terms absorbed by FE; the interaction coefficient remains comparable to the previous annual-FE audit. No observation exclusions are chosen by statistical significance.",
            "", "## Explicit non-identification demonstration", "",
            "Write TFR_it = prefecture_FE_i + year_FE_t + controls_it + theta × organic_i × imports_t + organic_i × h_t + error_it. With unrestricted h_t, any candidate theta can be offset by h_t. The original data cannot distinguish these explanations.",
            "", f"After including unrestricted organic-context × year effects, the residual treatment norm is {ratio:.2e} of its raw norm. The interaction is fully absorbed. This is an identification result, not a numerical failure.", "",
            markdown_table(pd.DataFrame(proof),["imposed_import_interaction","ssr","max_prediction_difference_vs_unrestricted"]),
            "", "Positive, zero and negative imposed import coefficients fit equally well when the allowed organic-context-specific national shocks adjust. This does not prove a particular confounder exists; it proves the data cannot rule it out without extra restrictions.",
            "", "## Shared-shock specification sensitivity", "",
            "All rows below use the same sample. p-values use prefecture-clustered CR1 SE and t(46); they are specification diagnostics, not independent confirmations. More flexible trends use scarce time variation and can reduce both bias and precision. Income and eating out may themselves be outcomes of trade; the no-controls row is included because controlling mediators can change the estimand.", "",
            markdown_table(specs,["spec","coefficient","prefecture_cluster_se","p_prefecture_t","treatment_information_fraction_vs_baseline"]),
            "", "Pandemic controls are organic context interacted with separate 2020, 2021 and 2022 indicators; they allow differential rather than merely average shocks. Geographic controls allow each of eight explicitly listed blocks a separate annual shock. See identification_checks.json for the block mapping. Prefecture trends use one omitted reference trend alongside year effects to keep full rank.",
            "", "## Covariance and few-year sensitivity", "",
            markdown_table(covariances,["method","coefficient","se","reference_df","p","ci_low","ci_high"]),
            "", "Prefecture clustering permits serial dependence within a prefecture but assumes independence between prefectures. Year clustering permits arbitrary same-year cross-prefecture dependence but assumes independence across years. Two-way clustering combines those dimensions but does not generally allow serially correlated common factors across different prefectures and years. Seven year clusters make the latter two estimates fragile. The two-way covariance matrix has a materially negative eigenvalue in this run; its target variance is positive, but the indefinite full matrix is a further warning against treating its borderline p-value as reliable. No eigenvalues or negative target variances were silently clipped; full diagnostics are exported.",
            "", "### Restricted wild cluster bootstrap-t by year", "",
            markdown_table(boot,["method","year_clusters","replications","observed_t","bootstrap_p","monte_carlo_se"]),
            "", "Webb six-point weights use 9,999 draws with a fixed seed. The Rademacher diagnostic enumerates all 128 sign patterns. Each imposes theta=0, generates restricted-residual bootstrap outcomes with a common weight per year, refits the full model, and studentises using year-clustered CR1 SE. Exhaustive sign enumeration does not make this an exact randomisation test. Independent year clusters, valid residual approximations and regressor exogeneity are maintained assumptions; serial national shocks and endogenous imports remain unresolved.",
            "", "## Lead/lag diagnostic", "",
            markdown_table(pd.DataFrame(lead_rows),["spec","variable","coefficient","prefecture_cluster_se","p_prefecture_t"]),
            "", "These rows jointly include current imports and one adjacent-year series on the same 324 observations. A future-import association would weaken a contemporaneous mechanism, but a null lead would not establish exogeneity. Highly correlated annual imports, anticipatory behaviour and persistent unobservables prevent treating this as a definitive falsification test. Adjacent-year import values come from supplied annual data; lead values include 2024.",
            "", "## Influence and information", "",
            f"Omitting each prefecture in turn gives interaction coefficients from {leave.coefficient.min():.4f} to {leave.coefficient.max():.4f}. All 47 fits are exported. These are influence diagnostics, not independent replications.", "",
            markdown_table(annual_information,["year","cn_import","information_share"]),
            "", "Information shares are sums of squared treatment residuals after projecting out baseline nuisance controls. They measure design concentration, not exogenous-shock probabilities or causal weights. Pairwise residual correlations are noisy with seven years and are exported only as descriptive diagnostics.",
            "", "## What would address the problem", "",
            "1. Specify the mechanism and target first: imported food consumption, agricultural competition, or another pathway imply different exposure measures and confounders. Do not label the current context interaction as exposure.",
            "2. Obtain pre-2016 prefecture-by-crop exposure weights, with a defensible link to the chosen mechanism. Food purchases, supply-chain deliveries or interregional commodity flows are candidates requiring verification. Port-of-entry trade is not automatically local consumption; local organic production is not automatically a substitute for imported consumption.",
            "3. Construct E_it = sum_k s_ik,pre × M_kt only after validating s. Prefer multiple crop/source shocks rather than one national series. Frozen pre-period weights avoid mechanically using contemporaneous outcomes to define exposure, but do not establish exogeneity.",
            "4. Imports respond to Japanese demand. Consider external supply variation such as origin-country harvest or policy shocks, or exports to destinations excluding Japan, only with a defensible exclusion restriction and documented pre-period shares. Weather, prices and global food shocks can also affect fertility through other channels. Neither an instrument nor shift-share construction is automatically valid.",
            "5. Obtain a longer pre-period and audit pre-trends, regional price/demographic changes, spillovers, share concentration and influential shocks. Test validity at the shock/exposure level as appropriate; conventional prefecture clustering alone may be inadequate.",
            "6. Decide in advance whether identification is justified by the shares, by external shocks, or a specified conditional parallel-trends assumption. Choose inference for that design. Do not manufacture regional exposure by simply allocating national imports by population; per-capita allocation leaves all prefectures with the same exposure.",
            "7. Until those inputs exist, report the interaction as an exploratory national-time-pattern association by organic context. Keep the inability to distinguish heterogeneous common shocks in the main conclusion.",
            "", "## References", ""]+['- '+s for s in sources]+[""]
    (DEST/"IMPORT_IDENTIFICATION_AUDIT.md").write_text("\n".join(report))
    print(specs[["spec","coefficient","p_prefecture_t","treatment_information_fraction_vs_baseline"]].to_string(index=False))
    print(covariances[["method","se","p"]].to_string(index=False))
    print(boot[["method","bootstrap_p"]].to_string(index=False))
    print(pd.DataFrame(lead_rows)[["variable","coefficient","p_prefecture_t"]].to_string(index=False))
    print(f"Identification audit written to {DEST}")


if __name__=="__main__":
    main()
