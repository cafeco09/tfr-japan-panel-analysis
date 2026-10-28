"""Named HS products inside BEC food imports, plus a separately flagged soy-meal reference.

python scripts/_16_named_food_imports.py
Retains source definitions and reports discrepancies instead of forcing reconciliation.
"""
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
REF=ROOT/"data"/"food_names_references"
CACHE=ROOT/"data"/"food_names_sources"
DEST=ROOT/"output"/"food_names"
SOY={"120110":"Soyabeans for sowing","120190":"Other soyabeans",
     "120810":"Soyabean flour and meal","150710":"Crude soyabean oil",
     "150790":"Other soyabean oil","210310":"Soy sauce",
     "230400":"Soyabean oilcake and extraction residues"}
GROUP_NAMES={"01":"Live animals","02":"Meat and edible offal","03":"Fish and seafood",
             "04":"Dairy, eggs and honey","07":"Vegetables and roots","08":"Fruit and nuts",
             "09":"Coffee, tea and spices","10":"Cereals","11":"Milling products and starches",
             "12":"Oilseeds and related products","15":"Fats and oils","16":"Prepared meat and seafood",
             "17":"Sugar and confectionery","18":"Cocoa and cocoa products",
             "19":"Cereal, flour and bakery preparations","20":"Prepared vegetables and fruit",
             "21":"Miscellaneous food preparations","22":"Beverages and vinegar",
             "23":"Food-industry residues","24":"Oral nicotine products (classification flag)",
             "35":"Albumins and enzymes"}
REFERENCE_SOURCES={
    "HS2012_to_BEC.xls":"https://unstats.un.org/unsd/classifications/Econ/tables/HS%202012%20to%20BEC%20Correlation%20and%20conversion%20tables.xls",
    "HS2017toBECConversionAndCorrelationTables.xlsx":"https://unstats.un.org/unsd/classifications/Econ/tables/HS2017toBECConversionAndCorrelationTables.xlsx",
    "HS2022toBEC4ConversionAndCorrelationTables.xlsx":"https://unstats.un.org/unsd/classifications/Econ/tables/HS2022toBEC4ConversionAndCorrelationTables.xlsx"}


def get_json(url):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url,timeout=30) as response:return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code in [429,500,502,503,504] and attempt<4:
                time.sleep(max(3,int(error.headers.get("Retry-After",3))));continue
            raise RuntimeError(f"HTTP {error.code}: {error.read().decode()[:250]}") from error


def references():
    REF.mkdir(parents=True,exist_ok=True)
    for name,url in REFERENCE_SOURCES.items():
        if not (REF/name).exists():
            with urllib.request.urlopen(url,timeout=30) as response:(REF/name).write_bytes(response.read())
    mapping={}
    for revision,name,sheet,columns in [
        ("H4","HS2012_to_BEC.xls","Conversion HS 2012-BEC",[2,3]),
        ("H5","HS2017toBECConversionAndCorrelationTables.xlsx",0,[0,1]),
        ("H6","HS2022toBEC4ConversionAndCorrelationTables.xlsx",0,[0,1])]:
        raw=pd.read_excel(REF/name,sheet_name=sheet,header=None,dtype=str)
        pairs=[]
        for row in raw.itertuples(index=False,name=None):
            code=str(row[columns[0]]).strip();bec=str(row[columns[1]]).strip()
            if re.fullmatch(r"\d{6}",code) and re.fullmatch(r"\d{2,3}",bec):pairs.append((code,bec))
        assert len(pairs)>5000 and len(dict(pairs))==len(pairs)
        mapping[revision]=dict(pairs)
    dictionaries={}
    for revision in mapping:
        path=REF/f"{revision}_names.json";url=f"https://comtradeapi.un.org/files/v1/app/reference/{revision}.json"
        if not path.exists():path.write_text(json.dumps(get_json(url),ensure_ascii=False,indent=2)+"\n")
        obj=json.loads(path.read_text())
        dictionaries[revision]={r["id"]:re.sub(r"^[A-Za-z0-9]+\s*-\s*","",r["text"]) for r in obj["results"]}
    pd.DataFrame([dict(revision=rev,hs6=code,bec4=bec,in_food_category=bec.startswith("1"))
                  for rev,items in mapping.items() for code,bec in items.items()]).to_csv(REF/"HS_to_BEC4_conversion.csv",index=False)
    (REF/"reference_sources.json").write_text(json.dumps(REFERENCE_SOURCES,indent=2)+"\n")
    return mapping,dictionaries


def fetch(year,revision,codes,batch):
    batch_id=f"{year}_{revision}_{batch:02d}"
    path=CACHE/f"{batch_id}.json"
    if path.exists():
        saved=json.loads(path.read_text());assert saved["requested_codes"]==codes
    else:
        params={"period":year,"reporterCode":392,"cmdCode":','.join(codes),"flowCode":"M",
                "partnerCode":0,"partner2Code":0,"customsCode":"C00","motCode":0,"maxRecords":500}
        url="https://comtradeapi.un.org/public/v1/preview/C/A/HS?"+urllib.parse.urlencode(params)
        saved=dict(batch_id=batch_id,year=year,revision=revision,requested_codes=codes,source_url=url,
                   retrieved_utc=datetime.now(timezone.utc).isoformat(),response=get_json(url))
    records=saved["response"].get("data",[])
    assert not saved["response"].get("error") and len(records)<500
    assert len({r['cmdCode'] for r in records})==len(records)
    for row in records:
        assert row["cmdCode"] in codes and row["classificationCode"]==revision
        assert row["reporterCode"]==392 and row["partnerCode"]==0 and row["partner2Code"]==0
        assert row["refYear"]==year and row["flowCode"]=="M" and row["motCode"]==0 and row["customsCode"]=="C00"
        assert row["primaryValue"] is not None and row["primaryValue"]>=0
    if not path.exists():path.write_text(json.dumps(saved,ensure_ascii=False,indent=2)+"\n")
    return saved


def scope_flag(code,name):
    if code=="240491":return "Oral nicotine product: not conventional food; source maps to BEC food"
    if code=="230400":return "Soy oilcake/residues: outside BEC food; supplementary reference only"
    if "sowing" in name.lower():return "Seed for sowing: not measured dietary consumption"
    if code.startswith("23"):return "Milling/food-industry residue: possible feed or industrial use"
    if code.startswith("01"):return "Live animal: use is not established by this commodity category"
    if code.startswith("35"):return "Albumins or enzymes: includes industrial ingredients"
    return "BEC-classified food/beverage; final use not observed"


def main():
    CACHE.mkdir(parents=True,exist_ok=True);DEST.mkdir(parents=True,exist_ok=True)
    mapping,names=references()
    products=[];batch_sources=[];missing=[]
    for year in range(2016,2026):
        revision="H4" if year==2016 else "H5" if year<=2021 else "H6"
        codes=sorted({code for code,bec in mapping[revision].items() if bec.startswith("1")}|set(SOY))
        returned=set()
        for offset in range(0,len(codes),100):
            saved=fetch(year,revision,codes[offset:offset+100],offset//100+1)
            batch_sources.append({k:saved[k] for k in ["batch_id","year","revision","source_url","retrieved_utc"]})
            for r in saved["response"]["data"]:
                code=r["cmdCode"];returned.add(code);description=names[revision].get(code,"")
                assert description
                products.append(dict(year=year,hs_revision=revision,hs2=code[:2],food_group=GROUP_NAMES.get(code[:2],names[revision].get(code[:2],code[:2])),
                                     official_food_group_description=names[revision].get(code[:2],code[:2]),
                                     hs4=code[:4],food_name="Soyabeans" if code.startswith("1201") else names[revision].get(code[:4],code[:4]),
                                     hs6=code,product_name=SOY.get(code,description),official_product_description=description,
                                     bec4=mapping[revision][code],included_in_bec_food=mapping[revision][code].startswith("1"),
                                     import_value_current_usd=r["primaryValue"],reported_net_weight_kg=r.get("netWgt"),
                                     net_weight_is_estimated=r.get("isNetWgtEstimated"),
                                     scope_flag=scope_flag(code,description),source_batch_id=saved["batch_id"]))
            print(f"{year}: validated batch {offset//100+1}/{(len(codes)+99)//100}",flush=True)
        missing.extend(dict(year=year,hs_revision=revision,hs6=code,product_name=names[revision].get(code,code),
                            status="No record returned; not replaced with an assumed zero") for code in codes if code not in returned)
    detail=pd.DataFrame(products).sort_values(["year","hs6"])
    assert not detail.duplicated(["year","hs6"]).any()
    detail.to_csv(DEST/"named_food_products_2016_2025.csv",index=False)
    pd.DataFrame(batch_sources).to_csv(DEST/"source_batches.csv",index=False)
    pd.DataFrame(missing).to_csv(DEST/"requested_products_not_returned.csv",index=False)
    included=detail[detail.included_in_bec_food].copy()
    headings=included.groupby(["year","hs4","food_name"],as_index=False).agg(import_value_current_usd=("import_value_current_usd","sum"),
                  returned_product_codes=("hs6","size"))
    groups=included.groupby(["year","hs2","food_group"],as_index=False).import_value_current_usd.sum()
    headings.to_csv(DEST/"named_food_headings_2016_2025.csv",index=False)
    groups.to_csv(DEST/"food_groups_2016_2025.csv",index=False)
    soy=detail[detail.hs6.isin(SOY)].copy();soy.to_csv(DEST/"soyabean_products_2016_2025.csv",index=False)
    control=pd.read_csv(ROOT/"data"/"external_food_imports_world_2016_2025.csv")
    check=control[["year","external_food_import_value_current_usd"]].merge(
        included.groupby("year",as_index=False).import_value_current_usd.sum(),on="year",validate="one_to_one")
    check=check.rename(columns={"import_value_current_usd":"mapped_named_product_total_usd"})
    check["difference_usd"]=check.mapped_named_product_total_usd-check.external_food_import_value_current_usd
    check["difference_fraction"]=check.difference_usd/check.external_food_import_value_current_usd
    check.to_csv(DEST/"reconciliation_to_world_food_total.csv",index=False)
    latest=headings[headings.year.eq(2025)].sort_values("import_value_current_usd",ascending=False)
    latest.to_csv(DEST/"food_names_2025.csv",index=False)
    record=dict(importer="Japan",origin="World",years=list(range(2016,2026)),units="Current USD",
                definition="HS6 products selected by official version-specific BEC4 conversion tables, categories starting with 1",
                revisions={"2016":"HS2012 H4","2017–2021":"HS2017 H5","2022–2025":"HS2022 H6"},
                supplemental="HS230400 soy oilcake/residues outside BEC food, shown separately and excluded from food totals",
                flags="Sowing seeds, possible feed/industrial residues, oral nicotine products and live animals are identified, not silently called consumed food",
                missing="Codes not returned are listed, not replaced by invented zero values",
                coverage="HS conversion and reported BEC aggregate may differ; actual reconciliation is exported without rescaling",
                products_returned=len(detail),latest_heading_count=len(latest))
    (DEST/"methodology.json").write_text(json.dumps(record,indent=2,ensure_ascii=False)+"\n")
    # Compact typed intermediate for the workbook builder.
    payload=dict(latest=latest.to_dict("records"),products=detail.replace({np.nan:None}).to_dict("records"),
                 headings=headings.to_dict("records"),groups=groups.to_dict("records"),
                 soy=soy.replace({np.nan:None}).to_dict("records"),sources=batch_sources,
                 soy_definitions=[dict(hs6=code,name=name,bec4=mapping['H6'][code],included=mapping['H6'][code].startswith('1')) for code,name in SOY.items()],
                 reconciliation=check.to_dict("records"),methodology=record)
    (DEST/"workbook_data.json").write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False))
    print('Reconciliation:',check.to_string(index=False))
    print('Latest named foods:',latest.head(15).to_string(index=False))


if __name__=="__main__":
    main()
