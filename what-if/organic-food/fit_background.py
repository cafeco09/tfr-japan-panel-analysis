"""Estimate age-specific fertility contributions; sum them to obtain future TFR.

MHLW publishes sums of single-age rates within seven age bands. These are
already TFR contributions: sum them directly, without multiplying by five.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'background'
AGES=['15-19','20-24','25-29','30-34','35-39','40-44','45-49']
YEARS=np.arange(2026,2051)
GROWTH={'volume_down_1pct':-.01,'volume_constant':0.,'volume_up_1pct':.01}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    observed=pd.read_csv(ROOT/'inputs/national_age_fertility_contributions_2006_2025.csv')
    national=pd.read_csv(ROOT/'inputs/national_tfr_2006_2025.csv')
    panel=pd.read_csv(ROOT/'inputs/dated_source_panel_2016_2025.csv')
    mass_columns=['china_national_crop_import_kg_per_resident','usa_national_crop_import_kg_per_resident']
    for col in mass_columns:
        assert panel.groupby('year')[col].nunique(dropna=False).le(1).all()
    mass=panel[['year',*mass_columns]].drop_duplicates('year').copy()
    mass['crop_kg_per_person']=mass[mass_columns].sum(axis=1,min_count=2)
    table=observed.pivot(index='year',columns='age_group',values='age_group_tfr_contribution')[AGES]
    assert table.shape==(20,7) and table.gt(0).all().all()
    reconstruction=table.sum(axis=1).rename('sum_published_age_contributions').reset_index().merge(national,on='year')
    reconstruction['rounding_difference']=reconstruction.sum_published_age_contributions-reconstruction.national_tfr
    assert reconstruction.rounding_difference.abs().max()<.0054
    reconstruction.to_csv(OUT/'historical_tfr_reconstruction.csv',index=False)
    anchor=table.loc[2025].to_numpy()
    anchor_sum=float(anchor.sum())
    anchor_mass=float(mass.loc[mass.year==2025,'crop_kg_per_person'].iloc[0])
    coeff_rows,age_rows,total_rows,draw_rows,backtests=[],[],[],[],[]

    def fit(years,with_mass):
        m=mass.set_index('year').loc[years,'crop_kg_per_person'].to_numpy()
        X=np.column_stack([np.ones(len(years)),np.asarray(years)-2016]+([np.log(m)] if with_mass else []))
        assert np.linalg.matrix_rank(X)==X.shape[1]
        fits=[sm.OLS(np.log(table.loc[years,age].to_numpy()),X).fit(cov_type='HC3',use_t=True) for age in AGES]
        return X,fits

    for vintage,last in [('primary_2016_2024',2024),('includes_provisional_2025',2025)]:
        train_years=list(range(2016,last+1))
        for model,with_mass in [('age_trends_and_crop_mass',True),('age_trends_only',False)]:
            X,fits=fit(train_years,with_mass)
            params=np.array([f.params for f in fits])
            p=X.shape[1]
            terms=['intercept','year_trend']+(['log_crop_kg_per_person'] if with_mass else [])
            for age,f in zip(AGES,fits):
                for k,term in enumerate(terms):
                    ci=f.conf_int()[k]
                    coeff_rows.append(dict(sample=vintage,model=model,age_group=age,term=term,
                        estimate=f.params[k],hc3_se=f.bse[k],p_t=f.pvalues[k],ci_low=ci[0],ci_high=ci[1],n=len(train_years)))
            # Joint HC3 covariance preserves correlation between the seven age models.
            A=np.linalg.pinv(X);h=np.sum(X*A.T,axis=1)
            residual=np.column_stack([f.resid for f in fits])
            scores=np.array([np.outer(residual[i]/(1-h[i]),A[:,i]).ravel() for i in range(len(X))])
            cov=scores.T@scores
            for a,f in enumerate(fits):
                assert np.allclose(cov[a*p:(a+1)*p,a*p:(a+1)*p],f.cov_params())
            values,vectors=np.linalg.eigh(cov)
            assert values.min()>-1e-9
            rng=np.random.default_rng(20261028)
            noise=rng.normal(size=(1000,len(AGES)*p))@(vectors@np.diag(np.sqrt(np.maximum(values,0)))).T
            noise/=np.sqrt(rng.chisquare(len(X)-p,1000)[:,None]/(len(X)-p))
            draws=params[None,:,:]+noise.reshape(1000,len(AGES),p)
            for scenario,growth in GROWTH.items():
                volumes=anchor_mass*(1+growth)**(YEARS-2025)
                delta=np.column_stack([np.zeros(len(YEARS)),YEARS-2025]+([np.log(volumes/anchor_mass)] if with_mass else []))
                projected_age=anchor[:,None]*np.exp(params@delta.T)
                tfr=projected_age.sum(axis=0)
                simulated=(anchor[None,:,None]*np.exp(np.einsum('bap,tp->bat',draws,delta))).sum(axis=1)
                quantiles=np.quantile(simulated,[.025,.5,.975],axis=0)
                for j,year in enumerate(YEARS):
                    for a,age in enumerate(AGES):
                        age_rows.append(dict(sample=vintage,model=model,scenario=scenario,year=int(year),
                            age_group=age,projected_age_tfr_contribution=projected_age[a,j],
                            assumed_crop_kg_per_person=volumes[j],status='SYNTHETIC_PROJECTED_AGE_RATE_SUM'))
                    total_rows.append(dict(sample=vintage,model=model,scenario=scenario,year=int(year),
                        calculated_tfr=tfr[j],parameter_p025=quantiles[0,j],parameter_median=quantiles[1,j],parameter_p975=quantiles[2,j],
                        assumed_crop_kg_per_person=volumes[j],
                        status='SYNTHETIC_TFR_SUM_OF_PROJECTED_AGE_CONTRIBUTIONS'))
                draw_rows.extend(dict(sample=vintage,model=model,scenario=scenario,draw_id=k,tfr_2050=v) for k,v in enumerate(simulated[:,-1]))
    for year in range(2021,2025):
        for model,with_mass in [('age_trends_and_crop_mass',True),('age_trends_only',False)]:
            _,fits=fit(list(range(2016,year)),with_mass)
            m=float(mass.loc[mass.year==year,'crop_kg_per_person'].iloc[0])
            x=np.array([1.,year-2016]+([np.log(m)] if with_mass else []))
            predicted=float(sum(np.exp(x@f.params) for f in fits))
            actual=float(table.loc[year].sum())
            backtests.append(dict(model=model,year=year,predicted_tfr=predicted,observed_age_sum=actual,absolute_error=abs(predicted-actual)))
    ages=pd.DataFrame(age_rows);totals=pd.DataFrame(total_rows);coeff=pd.DataFrame(coeff_rows)
    bt=pd.DataFrame(backtests)
    ages.to_csv(OUT/'projected_age_contributions_2026_2050.csv',index=False)
    totals.to_csv(OUT/'calculated_tfr_2026_2050.csv',index=False)
    coeff.to_csv(OUT/'age_specific_estimated_coefficients.csv',index=False)
    pd.DataFrame(draw_rows).to_csv(OUT/'joint_parameter_draws_2050.csv',index=False)
    bt.to_csv(OUT/'expanding_year_backtests.csv',index=False)
    endpoint=totals[(totals['sample']=='primary_2016_2024')&(totals.year==2050)]
    endpoint.to_csv(OUT/'primary_2050_summary.csv',index=False)
    regroup=ages.groupby(['sample','model','scenario','year']).projected_age_tfr_contribution.sum()
    direct=totals.set_index(['sample','model','scenario','year']).calculated_tfr
    assert np.allclose(regroup.sort_index(),direct.sort_index()) and len(totals)==300
    fig,axes=plt.subplots(1,2,figsize=(12.5,5))
    for ax,vintage in zip(axes,['primary_2016_2024','includes_provisional_2025']):
        ax.plot(national.year,national.national_tfr,color='#263649',lw=2,label='Published historical TFR')
        for scenario,colour in zip(GROWTH,['#c3872b','#248882','#6654a3']):
            g=totals[(totals['sample']==vintage)&(totals.model=='age_trends_and_crop_mass')&(totals.scenario==scenario)]
            ax.plot(np.r_[2025,g.year],np.r_[anchor_sum,g.calculated_tfr],lw=2,color=colour,label=scenario.replace('_',' '))
        g=totals[(totals['sample']==vintage)&(totals.model=='age_trends_only')&(totals.scenario=='volume_constant')]
        ax.plot(np.r_[2025,g.year],np.r_[anchor_sum,g.calculated_tfr],ls='--',color='#777',label='Age-trend-only benchmark')
        ax.axvline(2025.5,color='#888',ls=':',lw=.8)
        ax.set(title=vintage.replace('_',' '),xlabel='Year',ylabel='TFR: sum of projected age-rate contributions')
        ax.grid(alpha=.15);ax.spines[['top','right']].set_visible(False)
    axes[1].legend(frameon=False,fontsize=7.5)
    fig.suptitle('Estimated annual background: no fixed fertility target',fontsize=13)
    fig.text(.5,.02,'Future TFR is calculated by summing age contributions · Food volume paths assumed · No organic effect estimated or recovery forced',ha='center',fontsize=8.5)
    fig.tight_layout(rect=(0,.06,1,.93));fig.savefig(OUT/'age_specific_tfr_paths.png',dpi=170);fig.savefig(OUT/'age_specific_tfr_paths.svg');plt.close(fig)
    metadata=dict(method='Sum seven projected age-band contributions, each already a sum of single-age ASFRs; never multiply by five',
        historical_age_years=[2006,2025],primary_estimation_years=[2016,2024],future_years=[2026,2050],
        formula='log(age_band_contribution)=intercept+year_trend*(year-2016)+beta*log(crop_kg_per_person)',
        future_rule='2025 observed age contribution * exp(estimated trend*elapsed + estimated beta*log(future_mass/2025_mass))',
        target_tfr=None,target_used_in_estimation=False,
        physical_scope='National China+USA maize/rice/soybean imports; not world food, organic certification or consumption; potential feed uses',
        organic_domestic_effect='NOT_ESTIMABLE from available annual data',
        uncertainty='1000 joint HC3 multivariate-t parameter draws, seed 20261028; preserves cross-age covariance; not predictive intervals; no future shock, origin or scenario uncertainty',
        caution='Only nine national annual training observations per age model; same years reused, not independent prefectural exposures; 25-year extrapolation',
        reconstruction='Published age contributions rounded to four decimals; sum 2025=1.1351 versus reported rounded TFR=1.14; no rescaling')
    (OUT/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    (OUT/'validation.txt').write_text('PASS: 140 historical age records; historical sums match published TFR within rounding; all age fits full rank; joint covariance blocks reproduce HC3; 2100 future age rows sum exactly to 300 TFR rows; no fertility target used.\n')
    print('2050 primary:\n',endpoint[['model','scenario','calculated_tfr']].to_string(index=False))
    print('Backtest MAE:',bt.groupby('model').absolute_error.mean().to_dict())


if __name__=='__main__':
    main()
