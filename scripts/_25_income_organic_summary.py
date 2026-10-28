"""Visible, audited summary of the historical income and organic analyses."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from _00_load import load_2016_2023
from _13_ml_sensitivity_projections import table

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"output/income_organic_summary"


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    data=load_2016_2023()
    data=data[data.income_obs&data.income.notna()].copy()
    assert len(data)==371 and data.region_code.nunique()==47
    specifications={
        "OLS_with_year_effects":"tfr ~ log_income + log_eating_out + C(year)",
        "prefecture_effects_only":"tfr ~ log_income + log_eating_out + C(region_code)",
        "prefecture_and_year_effects":"tfr ~ log_income + log_eating_out + C(region_code) + C(year)",
    }
    rows=[]
    for spec,formula in specifications.items():
        fit=smf.ols(formula,data,missing="raise").fit(cov_type="cluster",cov_kwds={"groups":data.region_code},use_t=True)
        assert np.linalg.matrix_rank(fit.model.exog)==fit.model.exog.shape[1]
        for term in ["log_income","log_eating_out"]:
            ci=fit.conf_int().loc[term]
            rows.append(dict(spec=spec,term=term,coefficient=fit.params[term],prefecture_cluster_se=fit.bse[term],
                             p_t46=fit.pvalues[term],ci_low=ci.iloc[0],ci_high=ci.iloc[1],n=int(fit.nobs),
                             prefectures=47,years=data.year.nunique(),df_reference=fit.df_resid_inference))
    core=pd.DataFrame(rows);core.to_csv(DEST/"core_income_eating_out.csv",index=False)
    audited=pd.read_csv(ROOT/"output/audit/core_sensitivity.csv")
    for term in ["log_income","log_eating_out"]:
        original=audited[audited.spec.eq("annual_two_way_FE")&audited.variable.eq(term)].iloc[0]
        current=core[core.spec.eq("prefecture_and_year_effects")&core.term.eq(term)].iloc[0]
        assert np.isclose(original.coefficient,current.coefficient,atol=1e-10)
        assert np.isclose(original.p,current.p_t46,atol=1e-10)
    trend=audited[audited.spec.eq("prefecture_specific_linear_trends")].copy()
    plot=core.copy()
    extra=pd.DataFrame([dict(spec="prefecture_specific_trends",term=r.variable,coefficient=r.coefficient,
                             ci_low=r.ci_low,ci_high=r.ci_high,p_t46=r.p) for r in trend.itertuples()])
    plot=pd.concat([plot,extra],ignore_index=True)
    labels=["OLS + year effects","Prefecture effects only","Prefecture + year effects","Plus prefecture-specific trends"]
    order=list(specifications)+["prefecture_specific_trends"]
    fig,axes=plt.subplots(1,2,figsize=(14.2,5.3),sharey=True)
    for ax,term,title in zip(axes,["log_income","log_eating_out"],["Income per resident","Capital-city eating-out proxy"]):
        g=plot[plot.term.eq(term)].set_index("spec").loc[order]
        for i,r in enumerate(g.itertuples()):
            ax.plot([r.ci_low,r.ci_high],[i,i],color="#25638B",linewidth=1.7)
            ax.scatter(r.coefficient,i,color="#25638B",s=32,zorder=3)
            ax.text(1.025,i,f"p = {r.p_t46:.3g}",transform=ax.get_yaxis_transform(),va="center",ha="left",fontsize=9)
        ax.axvline(0,color="#647482",linestyle="--",linewidth=1)
        ax.set_title(title,fontsize=12);ax.set_xlabel("TFR units per log-point higher nominal value")
        ax.grid(axis="x",color="#E4E9ED");ax.set_axisbelow(True)
        ax.spines[['top','right']].set_visible(False)
    axes[0].set_yticks(range(4),labels=labels);axes[0].invert_yaxis()
    fig.suptitle("Income and eating-out associations depend on the specification",fontsize=15,y=.97)
    fig.text(.29,.035,"371 observed-income rows · 47 prefectures · 2016–2023\nPointwise 95% intervals: prefecture-clustered SEs, t(46). Descriptive associations, not causal effects.",fontsize=9)
    fig.subplots_adjust(left=.25,right=.88,top=.84,bottom=.22,wspace=.65)
    fig.savefig(DEST/"income_eating_out_specification_sensitivity.png",dpi=180,bbox_inches="tight")
    fig.savefig(DEST/"income_eating_out_specification_sensitivity.svg",bbox_inches="tight")
    plt.close(fig)

    organic=pd.read_csv(ROOT/"output/import_identification/shared_shock_sensitivity.csv")
    selected=organic[organic.spec.isin(["annual_FE","organic_linear_trend","organic_trend_and_pandemic_shocks"])].copy()
    selected.to_csv(DEST/"organic_interaction_selected_checks.csv",index=False)
    bootstrap=pd.read_csv(ROOT/"output/import_identification/wild_year_bootstrap.csv")
    later=pd.read_csv(ROOT/"output/audit/eating_out_sensitivity.csv")
    caveats=[
        "Organic context is the standardised share of farms reporting organic activity in the 2020 census, not individual organic-food consumption, certified-only production, chemical residues or local imported-food exposure.",
        "Its standalone main effect, and the gardening-context main effect, are constant within prefecture and absorbed by prefecture effects. Legacy pseudoinverse coefficients for those main effects are not uniquely identified and must not be reported as substantive estimates.",
        "The China interaction is positive. Under its model, higher organic context is associated with a more positive import-related TFR slope. This does not identify an absolute import effect or establish that organic farming protects fertility.",
        "The interaction uses historical China/USA maize-rice-soyabean mass proxies, not the current all-origin BEC food-value measure. Only seven annual exposure observations enter the 324-row 2017–2023 sample.",
        "Original period labels aggregate year indicators, not observations: the period input contains annual records with year labels removed. The audit recovers years explicitly and fits full-rank annual-FE models.",
        "Five synthetic 2023 incomes are separate from the observed-income samples. Organic and gardening snapshots are not copied into the current World-food controlled model as annual measurements.",
    ]
    report=["# Income, eating-out and organic-context results", "",
        "These analyses already existed in the legacy tables and model audits. This page makes their reproduced results visible without carrying forward the earlier unsupported headline that income and eating-out are robustly negative across fixed-effects models.", "",
        "## Income and eating out", "",
        "Same observed-income sample for the three core specifications: 371 prefecture-year rows, 47 prefectures, 2016–2023. Standard errors are clustered by prefecture and use a t(46) reference. No synthetic incomes are included. This differs from the 329-row balanced 2016–2022 sample used for the recent import/control ANOVA.", "",
        table(core,["spec","term","coefficient","p_t46","ci_low","ci_high","n"]), "",
        "Income changes from negative in the pooled/year-effect and prefecture-only models to positive after both prefecture and year effects are included (+0.2058, p = 0.0190). Eating-out is essentially zero in the two-way model (−0.00195, p = 0.9321). These are different conditional associations; the pasted negative ranges do not reproduce the current tables.", "",
        "Adding prefecture-specific trends reduces the income coefficient to +0.0603 (p = 0.2470). This sensitivity prevents describing the positive two-way result as invariant to regional trends. Eating-out in that specification remains non-significant (−0.0152, p = 0.4574).", "",
        "![Income and eating-out specification sensitivity](income_eating_out_specification_sensitivity.png)", "",
        "### Eating-out-only checks in later years", "",
        table(later,["spec","coefficient","p","n"]), "",
        "The 2024–2025 two-way model gives +0.00734, p = 0.8402, and includes provisional 2025 TFR. It does not reproduce a persistent negative eating-out result. The city-level household spending measure is a proxy; neither the sign nor the direction of measurement-error bias can be assumed.", "",
        "## Organic context and historical crop imports", "",
        table(selected,["spec","coefficient","p_prefecture_t","ci_low","ci_high","n"]), "",
        "The full-rank annual-FE China × organic-context interaction is +0.0386 (prefecture-clustered p = 0.0081). Allowing an organic-context trend and differential pandemic-year shocks reduces it to +0.0117 (p = 0.3893). Restricted year-cluster bootstrap p-values are shown below; neither bootstrap confirms the baseline at 5%.", "",
        table(bootstrap,["method","year_clusters","replications","bootstrap_p","monte_carlo_se"]), "",
        "![Organic-context specification and bootstrap diagnostics](../import_identification/import_identification_diagnostics.png)", "",
        "### Interpretation", "",
        *["- "+c for c in caveats], "",
        "The annual-FE gardening interaction is non-significant (p = 0.7913), but that is not a standalone test of whether gardening affects fertility. When unrestricted organic-context × year effects are allowed, the import × organic interaction is absorbed; distinguishing an import mechanism requires additional identifying assumptions or exposure data.", "",
        "## Reproduce and inspect", "", "```bash", "python scripts/_07_diagnostics.py", "python scripts/_25_income_organic_summary.py", "```", "",
        "The summary reads the retained shared-shock/bootstrap audit; regenerate that audit separately with `python scripts/_08_import_identification.py` when deliberately rerunning those checks. `python run_all.py --legacy` reproduces the original six-stage pipeline, but its organic main-effect exports retain rank deficiencies and are historical outputs, not the audited headline evidence.", "",
        "Full checks: [model audit](../audit/MODEL_AUDIT.md), [shared-shock identification audit](../import_identification/IMPORT_IDENTIFICATION_AUDIT.md), [all original core table entries](../tables/table1_core.csv), and [historical interaction table](../tables/table2_imports_interactions.csv). Sources and scope are in [Data_Sources.md](../../Data_Sources.md).", ""]
    (DEST/"INCOME_ORGANIC_RESULTS.md").write_text("\n".join(report))
    print(core.to_string(index=False))


if __name__=="__main__":
    main()
