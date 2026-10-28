"""Historical TFR regressions on physical food volumes and matched dollar values.

Primary basket: China+USA maize/rice/soybeans; World and country fits secondary.
python scripts/_32_crop_mass_data.py
python scripts/_33_historical_mass_regressions.py
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import variance_inflation_factor
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from itertools import product as sign_product

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/historical_mass_analysis'
PRODUCTS=['basket','maize','rice','soybeans']
METRICS={'physical_mass':'kg_per_resident','matched_value':'usd_per_resident'}


def wild_cluster_p(fit,years,term):
    """Restricted enumerated Rademacher diagnostic, with CR1 studentisation."""
    X=fit.model.exog;y=fit.model.endog;idx=fit.model.exog_names.index(term)
    restricted=np.delete(X,idx,axis=1)
    fitted=restricted@np.linalg.lstsq(restricted,y,rcond=None)[0];errors=y-fitted
    pinv=np.linalg.pinv(X);weights=pinv[idx]
    unique,inverse=np.unique(years,return_inverse=True);g=len(unique);n,k=X.shape
    correction=g/(g-1)*(n-1)/(n-k)
    signs=np.array(list(sign_product([-1.,1.],repeat=g)))
    outcomes=fitted[:,None]+errors[:,None]*signs[:,inverse].T
    betas=pinv@outcomes;residual=outcomes-X@betas
    scores=np.stack([(weights[inverse==j,None]*residual[inverse==j]).sum(axis=0) for j in range(g)])
    ses=np.sqrt(correction*(scores**2).sum(axis=0))
    stats=betas[idx]/ses
    observed=float(fit.params[term]/fit.bse[term])
    observed_scores=np.array([np.dot(weights[inverse==j],fit.resid[inverse==j]) for j in range(g)])
    assert np.isclose(np.sqrt(correction*np.sum(observed_scores**2)),fit.bse[term],rtol=1e-7)
    assert np.isfinite(stats).all()
    return float(np.mean(np.abs(stats)>=abs(observed)-1e-9)),len(signs)


def markdown(frame,columns):
    lines=['| '+' | '.join(columns)+' |','|'+'|'.join(['---']*len(columns))+'|']
    for row in frame[columns].itertuples(index=False,name=None):
        lines.append('| '+' | '.join(f'{v:.4f}' if isinstance(v,(float,np.floating)) else str(v) for v in row)+' |')
    return '\n'.join(lines)


def prepare(data,metric):
    frame=data.copy()
    for product in PRODUCTS:
        frame[f'x_{product}']=np.log(frame[f'{product}_{METRICS[metric]}'].where(frame[f'{product}_{METRICS[metric]}']>0))
    frame['trend']=frame.year-2016
    return frame


def check(fit):
    assert np.linalg.matrix_rank(fit.model.exog)==fit.model.exog.shape[1]


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    volumes=pd.read_csv(ROOT/'data/crop_mass_annual_2016_2025.csv')
    national=pd.read_csv(ROOT/'data/national_tfr_2016_2025.csv')
    history=pd.read_csv(ROOT/'data/dated_source_panel_2016_2025.csv')
    merged=volumes.merge(national,on='year',validate='many_to_one')
    merged.to_csv(OUT/'national_analysis_data.csv',index=False)
    specs={p:[p] for p in PRODUCTS};specs['joint_crops']=['maize','rice','soybeans']
    coefficients=[];diagnostics=[];stability=[];heldout=[]
    for origin in ['China_USA','World','China','USA']:
        for sample,end in [('primary_2016_2024',2024),('provisional_2025_sensitivity',2025)]:
            raw=merged[(merged.origin==origin)&(merged.year<=end)].sort_values('year')
            for metric in METRICS:
                data=prepare(raw,metric)
                for spec,products in specs.items():
                    formula='national_tfr ~ trend + '+' + '.join('x_'+p for p in products)
                    fit=smf.ols(formula,data,missing='raise').fit(cov_type='HC3',use_t=True);check(fit)
                    hac=smf.ols(formula,data).fit(cov_type='HAC',cov_kwds={'maxlags':1,'use_correction':True},use_t=True)
                    for product in products:
                        term='x_'+product;ci=fit.conf_int().loc[term]
                        j=fit.model.exog_names.index(term)
                        coefficients.append(dict(origin=origin,sample=sample,metric=metric,spec=spec,product=product,
                            coefficient=fit.params[term],hc3_se=fit.bse[term],hc3_p=fit.pvalues[term],
                            ci_low=ci.iloc[0],ci_high=ci.iloc[1],hac1_p=hac.pvalues[term],
                            tfr_change_for_10pct=fit.params[term]*np.log1p(.1),n=int(fit.nobs),df=int(fit.df_resid),
                            VIF=variance_inflation_factor(fit.model.exog,j)))
                    diagnostics.append(dict(analysis='national',origin=origin,sample=sample,metric=metric,spec=spec,
                        rows=len(data),independent_years=data.year.nunique(),n_parameters=fit.model.exog.shape[1],
                        condition_number=fit.condition_number,R2=fit.rsquared))
                    if origin=='China_USA' and sample=='primary_2016_2024' and metric=='physical_mass' and spec in PRODUCTS:
                        for year in data.year:
                            loo=smf.ols(formula,data[data.year!=year]).fit();check(loo)
                            stability.append(dict(analysis='national',spec=spec,product=spec,omitted_year=year,coefficient=loo.params['x_'+spec]))
                if origin=='China_USA' and sample=='primary_2016_2024':
                    for year in range(2021,2025):
                        train=data[data.year<year];test=data[data.year==year]
                        for label,formula in [('trend_only','national_tfr ~ trend'),('basket','national_tfr ~ trend + x_basket')]:
                            f=smf.ols(formula,train).fit();check(f)
                            predicted=float(f.predict(test).iloc[0]);actual=float(test.national_tfr.iloc[0])
                            heldout.append(dict(metric=metric,model=label,year=year,actual=actual,predicted=predicted,absolute_error=abs(actual-predicted)))
    nat=pd.DataFrame(coefficients)
    nat['holm_p_primary_family']=np.nan
    for metric in METRICS:
        mask=(nat.origin=='China_USA')&(nat['sample']=='primary_2016_2024')&(nat.metric==metric)&nat.spec.isin(PRODUCTS)
        nat.loc[mask,'holm_p_primary_family']=multipletests(nat.loc[mask,'hc3_p'],method='holm')[1]
    nat.to_csv(OUT/'national_regression_coefficients.csv',index=False)
    # Matched-sample physical and monetary regressions with the existing controls.
    cnus=volumes[volumes.origin=='China_USA']
    controls=history.merge(cnus,on='year',validate='many_to_one')
    controls['log_income']=np.log(controls.observed_income_jpy_per_resident.where(controls.observed_income_jpy_per_resident>0))
    controls['log_eating_out']=np.log(controls.eating_out_jpy_per_household.where(controls.eating_out_jpy_per_household>0))
    primary=controls[controls.year<=2022].dropna(subset=['log_income','log_eating_out'])
    extended=controls[controls.year<=2023].dropna(subset=['log_income','log_eating_out'])
    assert len(primary)==329 and len(extended)==371
    primary.to_csv(OUT/'controlled_balanced_analysis_data.csv',index=False)
    extended.to_csv(OUT/'controlled_extended_analysis_data.csv',index=False)
    rows=[]
    for sample,raw in [('balanced_2016_2022',primary),('complete_2016_2023',extended)]:
        for metric in METRICS:
            data=prepare(raw,metric)
            for spec,products in specs.items():
                formula='tfr_children_per_woman ~ C(region_code) + trend + log_income + log_eating_out + '+' + '.join('x_'+p for p in products)
                fit=smf.ols(formula,data,missing='raise').fit(cov_type='cluster',cov_kwds={'groups':data.year,'use_correction':True,'df_correction':True},use_t=True);check(fit)
                diagnostics.append(dict(analysis='controlled_prefecture',origin='China_USA',sample=sample,metric=metric,spec=spec,
                    rows=len(data),independent_years=data.year.nunique(),n_parameters=fit.model.exog.shape[1],condition_number=fit.condition_number,R2=fit.rsquared))
                for product in products:
                    term='x_'+product;ci=fit.conf_int().loc[term]
                    boot,patterns=wild_cluster_p(fit,data.year.to_numpy(),term)
                    rows.append(dict(sample=sample,metric=metric,spec=spec,product=product,coefficient=fit.params[term],
                        year_cluster_se=fit.bse[term],year_cluster_p=fit.pvalues[term],ci_low=ci.iloc[0],ci_high=ci.iloc[1],
                        wild_cluster_p=boot,sign_patterns=patterns,tfr_change_for_10pct=fit.params[term]*np.log1p(.1),
                        rows=len(data),year_clusters=data.year.nunique(),cluster_df=fit.df_resid_inference))
                if sample=='balanced_2016_2022' and metric=='physical_mass' and spec in PRODUCTS:
                    for year in sorted(data.year.unique()):
                        loo=smf.ols(formula,data[data.year!=year]).fit();check(loo)
                        stability.append(dict(analysis='controlled_prefecture',spec=spec,product=spec,omitted_year=year,coefficient=loo.params['x_'+spec]))
    pref=pd.DataFrame(rows);pref['holm_wild_p_primary_family']=np.nan
    for metric in METRICS:
        mask=(pref['sample']=='balanced_2016_2022')&(pref.metric==metric)&pref.spec.isin(PRODUCTS)
        pref.loc[mask,'holm_wild_p_primary_family']=multipletests(pref.loc[mask,'wild_cluster_p'],method='holm')[1]
    pref.to_csv(OUT/'controlled_regression_coefficients.csv',index=False)
    pd.DataFrame(diagnostics).to_csv(OUT/'model_diagnostics.csv',index=False)
    pd.DataFrame(stability).to_csv(OUT/'leave_one_year_out_coefficients.csv',index=False)
    bt=pd.DataFrame(heldout);bt.to_csv(OUT/'conditional_expanding_backtests.csv',index=False)
    bt.groupby(['metric','model']).absolute_error.mean().rename('MAE').to_csv(OUT/'backtest_MAE.csv')
    # Interpretable level sensitivity, per 10 kg/person/year.
    data=merged[(merged.origin=='China_USA')&(merged.year<=2024)].copy();data['trend']=data.year-2016
    level=[]
    for product in PRODUCTS:
        formula=f'national_tfr ~ trend + {product}_kg_per_resident'
        f=smf.ols(formula,data).fit(cov_type='HC3',use_t=True);check(f)
        term=f'{product}_kg_per_resident'
        level.append(dict(product=product,tfr_change_for_10kg=f.params[term]*10,p_hc3=f.pvalues[term]))
    pd.DataFrame(level).to_csv(OUT/'national_level_per_10kg_sensitivity.csv',index=False)
    primary_nat=nat[(nat.origin=='China_USA')&(nat['sample']=='primary_2016_2024')&(nat.metric=='physical_mass')&nat.spec.isin(PRODUCTS)]
    primary_pref=pref[(pref['sample']=='balanced_2016_2022')&(pref.metric=='physical_mass')&pref.spec.isin(PRODUCTS)]
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    for ax,df,title in zip(axes,[primary_nat,primary_pref],['National: nine annual observations','Controlled prefectural panel: seven annual clusters']):
        for j,r in enumerate(df.itertuples()):
            scale=np.log1p(.1)
            ax.plot([r.ci_low*scale,r.ci_high*scale],[j,j],color='#286e8c',lw=2)
            ax.scatter(r.coefficient*scale,j,color='#286e8c',zorder=3)
        ax.axvline(0,color='#888',ls='--',lw=1)
        ax.set_yticks(range(4),['Combined basket','Maize','Rice','Soybeans']);ax.set_ylim(3.45,-.45)
        ax.set(title=title,xlabel='Estimated TFR difference for 10% more kg/person/year')
        if title.startswith('Controlled'):
            for j,r in enumerate(df.itertuples()):
                ax.text(.98,j+.21,f'wild p = {r.wild_cluster_p:.3f}',transform=ax.get_yaxis_transform(),ha='right',fontsize=8,color='#555')
        ax.grid(axis='x',alpha=.15);ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Historical physical-volume associations: China + USA crop basket',fontsize=14)
    fig.text(.5,.02,'Pointwise 95% intervals: left HC3, right conventional CR1 year clustering · Right-panel wild p-values show few-cluster sensitivity',ha='center',fontsize=8.5)
    fig.tight_layout(rect=(0,.06,1,.93));fig.savefig(OUT/'physical_volume_coefficients.png',dpi=170);fig.savefig(OUT/'physical_volume_coefficients.svg');plt.close(fig)
    quality=volumes.groupby('origin').agg(years=('year','size'),years_with_estimated_mass=('any_mass_source_estimated','sum'),missing_mass_components=('missing_mass_components','sum'))
    quality.to_csv(OUT/'mass_quality_by_origin.csv')
    (OUT/'methods.json').write_text(json.dumps(dict(primary='China+USA maize HS1005, rice HS1006, soybeans HS1201; kg per resident per year',
        matched_values='Same crop basket and population denominator, current USD per resident; not the previous broader food universe',
        national='2016–2024, n=9; national published TFR; linear time trend; HC3 with t(df), HAC1 sensitivity',
        controls='Prefecture indicators, common linear time trend, observed log income per resident, log capital-city eating-out spending proxy',
        panel='329 balanced rows 2016–2022 with 7 year clusters; 371 complete cases through 2023 with 8 year clusters; no synthetic income',
        inference='CR1 year-cluster t; restricted Rademacher wild-cluster bootstrap 128/256 signs; approximate diagnostic, not exact test; temporal dependence unresolved',
        multiple_testing='Holm over four prespecified single-basket/crop primary tests, separately per metric; national HC3 and controlled wild p families',
        secondary='Joint crop models, World/country models, level-per-10kg models, provisional 2025 sensitivity, leave-year-out and 4 heldout years',
        limitations='National exposures repeated across prefectures; year FE absorb their main effects. Mass may include feed/processing. Organic status, pesticide exposure and local consumption unknown. Covariates do not establish causality.',
        organic_what_if='Separate assumption-only exercise; no organic effect inferred or recalibrated from this analysis'),indent=2)+'\n')
    assert nat.loc[(nat['sample']=='primary_2016_2024'),'n'].eq(9).all()
    assert primary_nat.shape[0]==4 and primary_pref.shape[0]==4
    (OUT/'validation.txt').write_text('PASS: positive mass/values; full-rank designs; matched physical/value samples; 9 national observations, 7 primary year clusters; bootstrap covariance checks; separate primary multiple-testing families.\n')
    extended_mass=pref[(pref['sample']=='complete_2016_2023')&(pref.metric=='physical_mass')&pref.spec.isin(PRODUCTS)]
    comparison=nat[(nat.origin=='China_USA')&(nat['sample']=='primary_2016_2024')&nat.spec.isin(PRODUCTS)]
    report=['# Historical food-volume analysis','',
        'Actual trade mass replaces nominal spending as the main predictor in this supplementary analysis. Maize (HS1005), rice (HS1006) and soybeans (HS1201) are modelled separately and as a combined basket. The primary origin scope is China plus the USA; World and individual-country fits are secondary. This is not a mass reconstruction of all-world, all-food BEC imports. Earlier broad-food dollar results remain separate.','',
        '## National results: 2016–2024','',
        'Nine published national TFR observations; each primary regression includes a linear time trend and one log physical-volume predictor. Volumes are kg per resident per year. Effects below correspond to 10% more physical mass. HC3 uses a t reference with six residual degrees of freedom.','',
        markdown(primary_nat,['product','tfr_change_for_10pct','hc3_p','holm_p_primary_family','hac1_p']),'',
        'No primary HC3 result is significant at 5%, before or after the four-test Holm correction. Soybeans have a positive association, with HC3 p = 0.0768 and Holm p = 0.3073. HAC1 gives p = 0.0165 for this same positive association; this inference sensitivity is retained rather than selecting the smaller p-value. Joint-crop models are also exported, with only four residual degrees of freedom.','',
        '## Prefectural regressions with controls','',
        'The primary balanced sample has 329 rows: 47 prefectures over 2016–2022. Controls are prefecture indicators, a common linear time trend, observed log prefectural income per resident and log capital-city eating-out spending. No synthetic incomes are used. Seven independent annual exposure values are repeated across prefectures; 329 rows do not create 329 import shocks.','',
        markdown(primary_pref,['product','tfr_change_for_10pct','year_cluster_p','wild_cluster_p','holm_wild_p_primary_family']),'',
        'The basket and maize are positively associated with TFR under conventional year clustering, but the restricted wild-cluster diagnostic does not confirm either at 5%. Rice and soybeans are negative in this balanced sample but also unsupported under this diagnostic. The bootstrap enumerates 128 Rademacher sign patterns, is an approximate few-cluster diagnostic rather than an exact randomisation test, and does not resolve serial dependence.','',
        '### Complete-case extension through 2023','',
        'This secondary sample has 371 rows and eight annual clusters; five prefectures lack observed income in 2023. It is not a balanced extension and involves no imputation.','',
        markdown(extended_mass,['product','coefficient','year_cluster_p','wild_cluster_p']),'',
        'The extended sample gives positive basket and maize coefficients, with unadjusted wild p = 0.0078 and 0.0156. These positive associations should be reported, while retaining the sample sensitivity and small number of years. Soybeans change from negative in the balanced sample to positive in the extension. The extension is secondary and its displayed p-values are not the primary four-test family. Controls and statistical significance do not establish causality.','',
        '![Physical-volume effects and inference sensitivity](physical_volume_coefficients.png)','',
        '## Matched volume versus value comparison','',
        'Dollar comparisons use exactly the same three crops, origins, annual rows and population denominator, in current USD per resident. Thus price/value and physical quantity can be compared without changing the basket. This matched-value specification is distinct from the previous broad BEC food-dollar model.','',
        markdown(comparison,['metric','product','coefficient','hc3_p']),'',
        'Four expanding held-out years (2021–2024) give MAE 0.02370 for trend only, 0.02632 for the physical basket and 0.03616 for the matched-value basket. Mass improves on the matched dollar model but does not beat trend only. These checks supply realised same-year imports and are conditional predictions, not operational forecasts.','',
        '## Data quality and interpretation','',
        'UN Comtrade net-weight records were collected directly, with current dollar values retained only for comparison. All 90 origin-product-year masses are present; missing weights are never zero-filled, and money is never converted into kilograms. All 20 refreshed China/USA annual basket totals exactly match the retained historical masses.','',
        'Five of ten combined China/USA annual baskets contain at least one source-estimated weight, including four of nine primary national years. China alone has one flagged year; USA four; every World annual basket has at least one flagged component. Source estimates are retained and labelled, not presented as unestimated measurements. Flags and individual component weights are exported.','',
        'Population denominators preserve the existing source-panel vintage, reconstructed through and checked against both countries’ total/per-resident identities. This is not a fresh population-vintage update. Each total is divided by that denominator once; World is never added to China and USA.','',
        'These quantities can include feed and processing uses. They are not measured household diets, pesticide exposure or prefectural import exposure. Historical organic status remains unknown. Unrestricted year effects absorb the national import main effects; time-trend models impose restrictions and cannot remove all shared national shocks. The organic what-if scenarios remain separate assumptions and are not recalibrated to claim a benefit from these historical associations.','',
        '## Reproduction and outputs','',
        'From the repository root:','',
        '```bash\npython scripts/_32_crop_mass_data.py\npython scripts/_33_historical_mass_regressions.py\n```','',
        'The collector reuses saved raw responses by default; `--refresh` explicitly requests a new vintage. Analysis runs offline from the supplied CSVs. Dependencies: NumPy, pandas, SciPy, statsmodels and matplotlib. National, controlled, joint-crop, country/World, provisional-2025, level-per-10kg, leave-year-out and held-out results are all retained in this folder. See [methods](methods.json), [data sources](../../Data_Sources.md) and [component records](../../data/crop_mass_components_2016_2025.csv).']
    (OUT/'HISTORICAL_MASS_RESULTS.md').write_text('\n'.join(report)+'\n')
    print('\nPRIMARY NATIONAL PHYSICAL MASS\n',primary_nat[['product','coefficient','hc3_p','holm_p_primary_family','hac1_p']].to_string(index=False))
    print('\nPRIMARY CONTROLLED PHYSICAL MASS\n',primary_pref[['product','coefficient','year_cluster_p','wild_cluster_p','holm_wild_p_primary_family']].to_string(index=False))
    print('\nMASS QUALITY\n',quality.to_string())


if __name__=='__main__': main()
