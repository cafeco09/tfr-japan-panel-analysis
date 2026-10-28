"""Annual 2026–2050 scenarios: imports assumed organic, with no TFR target.

Historical volume associations are held fixed. Organic uplifts are explicit,
unestimated contrasts with continuation of the unknown historical food mix.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'
EFFECTS={'negative_assumption':-.001,'zero_assumption':0.,'positive_0p001':.001,'positive_0p004':.004}


def smooth(values):
    result=[];previous=0.
    for value in values:
        previous+=(value-previous)/3.
        result.append(previous)
    return np.asarray(result)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    forecasts=pd.read_csv(ROOT/'background/calculated_tfr_2026_2050.csv')
    age_forecasts=pd.read_csv(ROOT/'background/projected_age_contributions_2026_2050.csv')
    history=pd.read_csv(ROOT/'inputs/national_tfr_2006_2025.csv')
    historical_age=pd.read_csv(ROOT/'inputs/national_age_fertility_contributions_2006_2025.csv')
    anchor=float(historical_age.loc[historical_age.year==2025,'age_group_tfr_contribution'].sum())
    # Domestic food quantities are unmeasured scenario assumptions; no historical imputation.
    output=[];support=[];summaries=[]
    for scenario in ['volume_down_1pct','volume_constant','volume_up_1pct']:
        baseline=forecasts[(forecasts['sample']=='primary_2016_2024')&(forecasts.model=='age_trends_and_crop_mass')&(forecasts.scenario==scenario)].sort_values('year')
        years=baseline.year.to_numpy();assert np.array_equal(years,np.arange(2026,2051))
        imported=baseline.assumed_crop_kg_per_person.to_numpy()
        domestic=5.+95.*(years-2025)/25.
        # All modelled imports become organic in the scenario from 2026.
        # The effect is a contrast with historical mix, NOT an assertion that past imports were non-organic.
        effective_import=smooth(imported)
        effective_domestic=smooth(domestic-5.)
        b=baseline.calculated_tfr.to_numpy()
        for label,beta in EFFECTS.items():
            import_gain=beta*effective_import
            domestic_gain=beta*effective_domestic
            tfr=b+import_gain+domestic_gain
            assert (tfr>0).all()
            changes=np.diff(np.r_[anchor,tfr])
            sustained=[int(years[j]) for j in range(len(years)) if np.all(changes[j:]>0)]
            for j,year in enumerate(years):
                output.append(dict(year=int(year),volume_scenario=scenario,organic_effect_assumption=label,
                    control_import_volume_kg_per_person_year=imported[j],assumed_organic_import_fraction=1.,
                    assumed_organic_import_kg_per_person_year=imported[j],assumed_domestic_organic_kg_per_person_year=domestic[j],
                    assumed_organic_uplift_tfr_per_kg=beta,estimated_background_tfr=b[j],
                    assumed_import_tfr_contribution=import_gain[j],assumed_domestic_tfr_contribution=domestic_gain[j],
                    simulated_tfr=tfr[j],status='SYNTHETIC_ASSUMPTION_SCENARIO_NOT_ESTIMATED_ORGANIC_EFFECT'))
                # Preserve the age-rate aggregation calculation internally; annual output is primary.
                ag=age_forecasts[(age_forecasts['sample']=='primary_2016_2024')&(age_forecasts.model=='age_trends_and_crop_mass')&(age_forecasts.scenario==scenario)&(age_forecasts.year==year)]
                for r in ag.itertuples():
                    support.append(dict(year=int(year),volume_scenario=scenario,organic_effect_assumption=label,
                        age_group=r.age_group,scenario_age_contribution=r.projected_age_tfr_contribution*tfr[j]/b[j]))
            summaries.append(dict(volume_scenario=scenario,organic_effect_assumption=label,assumed_uplift_per_kg=beta,
                simulated_tfr_2026=tfr[0],simulated_tfr_2050=tfr[-1],change_from_2025_age_sum=tfr[-1]-anchor,
                first_sustained_annual_rise=sustained[0] if sustained else np.nan,
                fertility_target_used=False))
    annual=pd.DataFrame(output);internal=pd.DataFrame(support);summary=pd.DataFrame(summaries)
    annual.to_csv(OUT/'annual_food_volumes_and_tfr_2026_2050.csv',index=False)
    internal.to_csv(OUT/'supporting_age_contribution_reconciliation.csv',index=False)
    summary.to_csv(OUT/'emergent_2050_results.csv',index=False)
    constant=annual[annual.volume_scenario=='volume_constant']
    display=constant.pivot(index='year',columns='organic_effect_assumption',values='simulated_tfr')
    volumes=constant.drop_duplicates('year').set_index('year')[['assumed_organic_import_kg_per_person_year','assumed_domestic_organic_kg_per_person_year']]
    volumes.join(display).to_csv(OUT/'year_by_year_constant_volume_comparison.csv')
    check=internal.groupby(['year','volume_scenario','organic_effect_assumption']).scenario_age_contribution.sum()
    direct=annual.set_index(['year','volume_scenario','organic_effect_assumption']).simulated_tfr
    assert np.allclose(check.sort_index(),direct.sort_index())
    assert len(annual)==300 and len(internal)==2100
    assert np.allclose(annual[annual.organic_effect_assumption=='zero_assumption'].simulated_tfr,
                       annual[annual.organic_effect_assumption=='zero_assumption'].estimated_background_tfr)
    fig,axes=plt.subplots(1,2,figsize=(12,5))
    colours=['#b86a5a','#687581','#2e8a86','#6755a5']
    axes[0].plot(history.year,history.national_tfr,color='#263649',lw=2,label='Observed TFR (2025 provisional)')
    for (label,beta),colour in zip(EFFECTS.items(),colours):
        g=constant[constant.organic_effect_assumption==label]
        axes[0].plot(np.r_[2025,g.year],np.r_[anchor,g.simulated_tfr],lw=2,color=colour,label=f'Assumed uplift {beta:+.3f} per kg')
    axes[0].axvline(2025.5,color='#888',ls=':',lw=1)
    axes[0].set(xlabel='Year',ylabel='Annual TFR (children per woman)',title='Emergent TFR; constant import-volume control')
    axes[0].legend(frameon=False,fontsize=7.5)
    one=constant.drop_duplicates('year')
    axes[1].plot(one.year,one.assumed_organic_import_kg_per_person_year,lw=2,label='Imports: 100% assumed organic')
    axes[1].plot(one.year,one.assumed_domestic_organic_kg_per_person_year,lw=2,label='Assumed domestic organic production')
    axes[1].set(xlabel='Year',ylabel='Assumed kg per person per year',title='Physical food supply assumptions')
    axes[1].legend(frameon=False,fontsize=8)
    for ax in axes: ax.spines[['top','right']].set_visible(False);ax.grid(alpha=.15)
    fig.suptitle('Year-by-year scenarios, 2026–2050: no fixed fertility outcome',fontsize=14)
    fig.text(.5,.02,'Future imports assumed organic · Historical physical basket: China/USA maize, rice, soybeans · Organic effects unestimated',ha='center',fontsize=8.5)
    fig.tight_layout(rect=(0,.06,1,.93));fig.savefig(OUT/'annual_organic_scenarios.png',dpi=170);fig.savefig(OUT/'annual_organic_scenarios.svg');plt.close(fig)
    (OUT/'assumptions.json').write_text(json.dumps(dict(future_years=[2026,2050],target_tfr=None,
        imports_organic_from_2026=True,historical_organic_classification='Unknown; never relabelled',
        volume_control='Estimated historical trend+mass model, primary 2016–2024; projected general crop import volume paths held fixed for each organic-benefit comparison',
        scope='China and USA maize/rice/soybeans only; not world/all-food imports; potential feed uses',
        organic_import_kg='Equal to entire modelled import mass after 2025, by assumption',
        domestic_organic_kg='Assumed reference 5 kg/person/year in 2025; linearly increases to 100 in 2050; not measured',
        effect_assumptions=EFFECTS,effect_interpretation='Additional TFR per organic kg/person/year versus continuation of historical mix; not estimated from historical mass coefficient',
        lag='3-year smoothing: E[t]=E[t-1]+(quantity[t]-E[t-1])/3, with E[2025]=0. Quantity is all future organic imports for import uplift and additional domestic organic output above assumed 5 kg reference for domestic uplift',
        same_origin_beta='Same assumed response per kg for domestic and imported organic food',
        internal_age_rule='Apply total uplift proportionally to each estimated annual age contribution; sum remains the annual TFR',
        identification='Organic imports equal total modelled imports post-2026 and cannot be separately estimated alongside the volume control; historical volume coefficient fixed, extra organic uplift assumed',
        uncertainty='No calibrated forecast intervals; effect cases are assumptions, not probabilities or confidence bounds',
        no_target_calibration=True),indent=2)+'\n')
    (OUT/'validation.txt').write_text('PASS: 300 annual scenario rows, 2100 supporting age rows, full 2026–2050 coverage; every organic import mass equals controlled import mass; zero-effect reproduces estimated background; all TFR totals reconcile; no fixed fertility target.\n')
    print(summary.to_string(index=False))


if __name__=='__main__':
    main()
