"""Collect actual mass and matched values for maize, rice and soybean imports.

python scripts/_32_crop_mass_data.py [--refresh]
No monetary-to-mass conversion, missing-weight zero-fill, or organic inference.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import time
import urllib.request
import urllib.parse
import urllib.error
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'data/crop_mass_sources'
PRODUCTS={'1005':'maize','1006':'rice','1201':'soybeans'}
PARTNERS={0:'World',156:'China',842:'USA'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--refresh',action='store_true')
    args=parser.parse_args();CACHE.mkdir(parents=True,exist_ok=True)
    original=pd.read_csv(ROOT/'data/dated_source_panel_2016_2025.csv').drop_duplicates('year').set_index('year')
    records=[]
    for year in range(2016,2026):
        p=CACHE/f'crop_mass_{year}.json'
        if p.exists() and not args.refresh:
            saved=json.loads(p.read_text())
        else:
            params=dict(period=year,reporterCode=392,cmdCode='1005,1006,1201',flowCode='M',partnerCode='0,156,842',partner2Code=0,customsCode='C00',motCode=0,maxRecords=500)
            url='https://comtradeapi.un.org/public/v1/preview/C/A/HS?'+urllib.parse.urlencode(params)
            for attempt in range(4):
                try:
                    with urllib.request.urlopen(url,timeout=25) as response: payload=json.load(response)
                    break
                except urllib.error.HTTPError as e:
                    if e.code in [429,500,502,503,504] and attempt<3:
                        time.sleep(5*(attempt+1));continue
                    raise
            saved=dict(source_url=url,retrieved_utc=datetime.now(timezone.utc).isoformat(),response=payload)
            p.write_text(json.dumps(saved,indent=2)+'\n')
        rows=saved['response'].get('data',[])
        assert not saved['response'].get('error')
        assert {(r['partnerCode'],r['cmdCode']) for r in rows}=={(p,c) for p in PARTNERS for c in PRODUCTS}
        assert len(rows)==9
        # Preserve the existing denominator vintage when changing units/specifications.
        old=original.loc[year]
        pop=old.china_national_crop_import_total_kg/old.china_national_crop_import_kg_per_resident
        other_pop=old.usa_national_crop_import_total_kg/old.usa_national_crop_import_kg_per_resident
        assert np.isclose(pop,other_pop,atol=.1) and pop>0
        pop=float(round(pop))
        for row in rows:
            assert row['refYear']==year and row['reporterCode']==392 and row['flowCode']=='M'
            assert row['partner2Code']==0 and row['customsCode']=='C00' and row['motCode']==0
            kg=row.get('netWgt');value=row.get('primaryValue')
            assert kg is None or kg>=0
            records.append(dict(year=year,origin=PARTNERS[row['partnerCode']],partner_code=row['partnerCode'],
                product=PRODUCTS[row['cmdCode']],hs_code=row['cmdCode'],classification=row['classificationCode'],
                net_weight_kg=kg,current_usd=value,population_denominator=pop,
                kg_per_resident=kg/pop if kg is not None else np.nan,
                current_usd_per_resident=value/pop if value is not None else np.nan,
                mass_source_estimated=row.get('isNetWgtEstimated',False),is_reported=row.get('isReported'),
                organic_status='Not distinguished; historical imports are not assumed organic',
                use_status='Trade mass, potentially including feed/processing; not measured diet or local exposure',
                denominator_provenance='Retained dated_source_panel_2016_2025.csv vintage; verified total/per-resident identity for both origins',
                source_url=saved['source_url'],retrieved_utc=saved['retrieved_utc']))
        print(f'Validated {year}: 9 origin-product records',flush=True)
    long=pd.DataFrame(records).sort_values(['year','origin','product'])
    assert len(long)==90 and not long.duplicated(['year','origin','product']).any()
    long.to_csv(ROOT/'data/crop_mass_components_2016_2025.csv',index=False)
    annual=[]
    for year,group in long.groupby('year'):
        for origin in ['China','USA','China_USA','World']:
            selected=group[group.origin.isin(['China','USA'])] if origin=='China_USA' else group[group.origin==origin]
            row=dict(year=year,origin=origin,population_denominator=selected.population_denominator.iloc[0],
                     any_mass_source_estimated=bool(selected.mass_source_estimated.any()),
                     missing_mass_components=int(selected.net_weight_kg.isna().sum()),
                     scope='China and USA combined' if origin=='China_USA' else origin)
            for product in [*PRODUCTS.values(),'basket']:
                cell=selected if product=='basket' else selected[selected['product']==product]
                for unit,col in [('kg','net_weight_kg'),('usd','current_usd')]:
                    total=cell[col].sum(min_count=len(cell))
                    row[f'{product}_{unit}']=total
                    row[f'{product}_{unit}_per_resident']=total/row['population_denominator']
                row[f'{product}_mass_estimated']=bool(cell.mass_source_estimated.any())
            annual.append(row)
    wide=pd.DataFrame(annual)
    # World is retained separately, never added to its country components.
    for product in [*PRODUCTS.values(),'basket']:
        check=wide.pivot(index='year',columns='origin',values=f'{product}_kg')
        assert (check.World>=check.China_USA-.1).all()
    wide.to_csv(ROOT/'data/crop_mass_annual_2016_2025.csv',index=False)
    legacy=[]
    for year,row in original.iterrows():
        for origin,prefix in [('China','china'),('USA','usa')]:
            fresh=wide[(wide.year==year)&(wide.origin==origin)].iloc[0]
            old=row[f'{prefix}_national_crop_import_total_kg']
            legacy.append(dict(year=year,origin=origin,retained_legacy_kg=old,fresh_source_kg=fresh.basket_kg,difference_kg=fresh.basket_kg-old,
                matches=np.isclose(old,fresh.basket_kg,rtol=1e-8,atol=.1)))
    pd.DataFrame(legacy).to_csv(ROOT/'data/crop_mass_legacy_reconciliation.csv',index=False)
    print('Saved 90 components and 40 annual origin baskets; complete mass available:',long.net_weight_kg.notna().all())


if __name__=='__main__': main()
