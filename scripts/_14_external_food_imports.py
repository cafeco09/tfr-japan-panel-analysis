"""Japan's aggregate external food imports: World partner total, no origin split.

python scripts/_14_external_food_imports.py [--refresh]
BEC Rev.4 category 1 = primary (11) + processed (12) food and beverages.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/"data"/"external_food_sources"


def fetch(year,refresh=False):
    path=CACHE/f"world_food_{year}.json"
    if path.exists() and not refresh:
        saved=json.loads(path.read_text())
    else:
        params={"period":year,"reporterCode":392,"cmdCode":"1,11,12","flowCode":"M",
                "partnerCode":0,"partner2Code":0,"customsCode":"C00","motCode":0,"maxRecords":500}
        url="https://comtradeapi.un.org/public/v1/preview/C/A/B4?"+urllib.parse.urlencode(params)
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
    rows=saved["response"].get("data",[])
    assert not saved["response"].get("error")
    assert len(rows)==3 and saved["response"].get("count")==3
    assert {r["cmdCode"] for r in rows}=={"1","11","12"}
    for row in rows:
        assert row["refYear"]==year and row["reporterCode"]==392 and row["partnerCode"]==0
        assert row["partner2Code"]==0 and row["classificationCode"]=="B4" and row["flowCode"]=="M"
        assert row["customsCode"]=="C00" and row["motCode"]==0
        assert row["primaryValue"] is not None and row["primaryValue"]>0
    if not path.exists() or refresh:
        path.write_text(json.dumps(saved,indent=2,ensure_ascii=False)+"\n")
    return saved


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--refresh",action="store_true")
    args=parser.parse_args();CACHE.mkdir(parents=True,exist_ok=True)
    output=[]
    for year in range(2016,2026):
        saved=fetch(year,args.refresh);records={r["cmdCode"]:r for r in saved["response"]["data"]}
        total=records["1"]["primaryValue"];primary=records["11"]["primaryValue"];processed=records["12"]["primaryValue"]
        reconciles=bool(np.isclose(total,primary+processed,rtol=1e-8,atol=.1))
        gap=total-primary-processed
        if not reconciles:
            print(f"Source aggregation discrepancy {year}: ${gap:,.3f} ({100*gap/total:.6f}%); retain published category 1 and flag",flush=True)
        output.append(dict(year=year,importer="Japan",origin_scope="World: all partners",partner_code=0,
                           external_food_import_value_current_usd=total,
                           primary_food_beverages_current_usd=primary,processed_food_beverages_current_usd=processed,
                           category_sum_current_usd=primary+processed,aggregation_gap_usd=gap,
                           aggregation_gap_fraction=gap/total,components_reconcile=reconciles,
                           classification="BEC Rev.4 category 1 Food and beverages",
                           net_weight_kg=np.nan,weight_status="Aggregate weight unavailable; not interpreted as zero",
                           is_reported_bec_row=records["1"]["isReported"],
                           is_original_classification=records["1"]["isOriginalClassification"],
                           source_url=saved["source_url"],retrieved_utc=saved["retrieved_utc"]))
        print(f"Validated World food imports {year}: ${total:,.0f}",flush=True)
    data=pd.DataFrame(output)
    assert len(data)==10 and data.year.is_unique
    # The World aggregate is used directly; country and World totals must never be added together.
    country_path=ROOT/"data"/"food_imports_china_usa_wide.csv"
    if country_path.exists():
        check=data.merge(pd.read_csv(country_path),on="year",validate="one_to_one")
        assert (check.external_food_import_value_current_usd>=check.china_food_import_value_current_usd+check.usa_food_import_value_current_usd).all()
    target=ROOT/"data"/"external_food_imports_world_2016_2025.csv"
    data.to_csv(target,index=False)
    print(f"Saved {target}; no country/World double counting.")


if __name__=="__main__":
    main()
