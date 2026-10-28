"""Fetch broad food/beverage imports into Japan, separately for China and USA.

BEC Rev.4 category 1, split into primary (11) and processed (12).
No organic interaction. Collection only: no new causal effect is estimated.
python scripts/_09_food_imports.py [--refresh]
"""
import argparse
from datetime import datetime, timezone
import json
import time
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/"data"/"food_import_sources"
YEARS=range(2016,2026)
PARTNERS={156:"China",842:"USA"}


def fetch(year,refresh=False):
    path=CACHE/f"bec4_food_{year}.json"
    if path.exists() and not refresh:
        saved=json.loads(path.read_text())
    else:
        parameters={"period":str(year),"reporterCode":392,"cmdCode":"1,11,12",
                    "flowCode":"M","partnerCode":"156,842","partner2Code":0,
                    "customsCode":"C00","motCode":0,"maxRecords":500}
        url="https://comtradeapi.un.org/public/v1/preview/C/A/B4?"+urllib.parse.urlencode(parameters)
        for attempt in range(5):
            try:
                with urllib.request.urlopen(url,timeout=30) as response:
                    payload=json.load(response)
                break
            except urllib.error.HTTPError as error:
                if error.code==429 and attempt<4:
                    time.sleep(max(3,int(error.headers.get("Retry-After",3))))
                    continue
                raise RuntimeError(f"Comtrade {year}: HTTP {error.code}: {error.read().decode()[:300]}") from error
        saved={"source_url":url,"retrieved_utc":datetime.now(timezone.utc).isoformat(),"response":payload}
    payload=saved["response"]
    records=payload.get("data",[])
    if payload.get("error") or len(records)!=6 or payload.get("count")!=6:
        raise ValueError(f"Expected six unique records for {year}, got {len(records)}: {payload.get('error')}")
    expected={(partner,code) for partner in PARTNERS for code in ["1","11","12"]}
    actual={(row["partnerCode"],row["cmdCode"]) for row in records}
    assert actual==expected
    for row in records:
        assert row["refYear"]==year and row["reporterCode"]==392 and row["flowCode"]=="M"
        assert row["classificationCode"]=="B4" and row["partner2Code"]==0
        assert row["customsCode"]=="C00" and row["motCode"]==0
        assert row["primaryValue"] is not None and row["primaryValue"]>0
    if not path.exists() or refresh:
        path.write_text(json.dumps(saved,ensure_ascii=False,indent=2)+"\n")
    return saved


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh",action="store_true")
    args=parser.parse_args()
    CACHE.mkdir(parents=True,exist_ok=True)
    # Sequential requests respect the public preview service's low rate limit.
    snapshots=[]
    for year in YEARS:
        snapshots.append(fetch(year,args.refresh))
        print(f"Validated {year}",flush=True)
    rows=[]
    for year,saved in zip(YEARS,snapshots):
        lookup={(r["partnerCode"],r["cmdCode"]):r for r in saved["response"]["data"]}
        for partner,name in PARTNERS.items():
            total=lookup[(partner,"1")]
            primary=lookup[(partner,"11")]["primaryValue"]
            processed=lookup[(partner,"12")]["primaryValue"]
            assert np.isclose(total["primaryValue"],primary+processed,rtol=1e-8,atol=.1)
            rows.append(dict(year=year,importer="Japan",origin=name,partner_code=partner,
                             classification="BEC Rev.4",food_category="1 Food and beverages",
                             food_import_value_current_usd=total["primaryValue"],
                             primary_food_beverages_current_usd=primary,
                             processed_food_beverages_current_usd=processed,
                             organic_status="Not distinguished",net_weight_kg=np.nan,
                             weight_status="Aggregate weight not used; zero/unavailable is not interpreted as zero imports",
                             is_original_classification=total["isOriginalClassification"],
                             is_reported_bec_row=total["isReported"],
                             source_url=saved["source_url"],retrieved_utc=saved["retrieved_utc"]))
    output=pd.DataFrame(rows).sort_values(["year","origin"])
    assert len(output)==20 and not output.duplicated(["year","origin"]).any()
    target=ROOT/"data"/"food_imports_china_usa_2016_2025.csv"
    output.to_csv(target,index=False)
    # Wide table retains two separate country variables, without summing origins.
    wide=output.pivot(index="year",columns="origin",values="food_import_value_current_usd").rename(
        columns={"China":"china_food_import_value_current_usd","USA":"usa_food_import_value_current_usd"})
    wide.to_csv(ROOT/"data"/"food_imports_china_usa_wide.csv")
    print(output[["year","origin","food_import_value_current_usd"]].to_string(index=False))
    print(f"Saved {target}; primary + processed validated against total for all 20 country-years.")


if __name__=="__main__":
    main()
