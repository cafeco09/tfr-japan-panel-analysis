"""Index retained observation/batch URLs without inventing missing provenance."""
import json
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]


def main():
    entries=[]

    def add(role,variable,year,provider,url,path,locator="",retrieved="",publication="",note=""):
        if pd.isna(url) or not str(url).strip():
            return
        entries.append(dict(role=role,variable=variable,observation_year=year,provider=provider,
                            source_url=url,source_file=path,locator=locator,retrieved_utc=retrieved,
                            publication_date=publication,note=note))

    path="data/prefectural_tfr_2016_2025.csv";frame=pd.read_csv(ROOT/path)
    for (year,url),g in frame.groupby(["year","tfr_source"]):
        add("current","prefectural_tfr",year,"MHLW / e-Stat",url,path,
            "; ".join(sorted(g.tfr_source_cell.dropna().unique())),
            publication="2025-09-16" if year<=2024 else "",
            note="Final-data historical table" if year<=2024 else "Provisional source")

    path="data/national_tfr_2016_2025.csv"
    for row in pd.read_csv(ROOT/path).itertuples():
        add("current","national_tfr",row.year,"MHLW",row.source_url,path,
            row.source_sheet+"!"+row.source_cell,note=row.release_status)

    path="data/dated_source_panel_2016_2025.csv";panel=pd.read_csv(ROOT/path)
    mappings=[("current","prefectural_income","ESRI / Cabinet Office","income_source","income_source_cell"),
              ("current","capital_city_eating_out","Statistics Bureau / e-Stat","eating_out_source","eating_out_source_cell"),
              ("historical_snapshot","organic_activity","MAFF / e-Stat","organic_source_url","organic_source_cells"),
              ("historical_snapshot","gardening_participation","Statistics Bureau / e-Stat","gardening_source_url","gardening_source_cells"),
              ("historical_crop","population_denominator","World Bank WDI","population_source",None),
              ("historical_crop","three_crop_mass_imports","UN Comtrade","import_source",None),
              ("coverage_metadata","income_availability","ESRI / Cabinet Office","income_availability_source",None)]
    for role,variable,provider,url_col,cell_col in mappings:
        for (year,url),g in panel.dropna(subset=[url_col]).groupby(["year",url_col]):
            locator="; ".join(sorted(g[cell_col].dropna().unique())) if cell_col else ""
            publication="2026-08-07" if variable=="prefectural_income" and "/tables/2023/" in url else ""
            add(role,variable,year,provider,url,path,locator,publication=publication,
                note="Retained source field; not a claim that missing historical fields were verified")

    for role,path,variable in [
        ("current","data/external_food_imports_world_2016_2025.csv","world_BEC4_food_value"),
        ("historical_broad_food","data/food_imports_china_usa_2016_2025.csv","china_usa_BEC4_food_value")]:
        frame=pd.read_csv(ROOT/path)
        for (year,url),g in frame.groupby(["year","source_url"]):
            add(role,variable,year,"UN Comtrade",url,path,
                retrieved=str(g.retrieved_utc.iloc[0]) if "retrieved_utc" in g else "")

    path="output/food_names/source_batches.csv"
    for row in pd.read_csv(ROOT/path).itertuples():
        add("current","world_named_HS6_food",row.year,"UN Comtrade",row.source_url,path,
            row.batch_id+"; "+row.revision,row.retrieved_utc)

    path="data/food_names_references/reference_sources.json"
    for filename,url in json.loads((ROOT/path).read_text()).items():
        add("classification","HS_to_BEC4_conversion","","UNSD",url,
            "data/food_names_references/"+filename,note="Use conversion sheets, not ambiguous correlation expansion")
    for revision,label in [("H4","HS2012"),("H5","HS2017"),("H6","HS2022")]:
        add("classification","HS_product_names","","UN Comtrade",
            f"https://comtradeapi.un.org/files/v1/app/reference/{revision}.json",
            f"data/food_names_references/{revision}_names.json",label)
    add("classification","BEC_Rev4_manual","","UNSD",
        "https://unstats.un.org/unsd/publication/SeriesM/SeriesM_53rev4e.pdf","FOOD_IMPORT_SCOPE.md")

    result=pd.DataFrame(entries).drop_duplicates().sort_values(["role","variable","observation_year","source_url"],key=lambda s:s.astype(str))
    assert result.source_url.str.startswith("https://").all()
    result.to_csv(ROOT/"data/source_catalogue.csv",index=False)
    print(f"Indexed {len(result)} source/year/batch entries and {result.source_url.nunique()} distinct retained URLs.")


if __name__=="__main__":
    main()
