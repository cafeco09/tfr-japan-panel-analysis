"""Shared loading & feature engineering."""
import pandas as pd, numpy as np, os

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
OUT  = os.path.join(os.path.dirname(__file__), "..", "output")
os.makedirs(os.path.join(OUT, "tables"), exist_ok=True)
os.makedirs(os.path.join(OUT, "figures"), exist_ok=True)

def load_2016_2023():
    df = pd.read_csv(os.path.join(DATA, "input_2016_2023.csv"))
    eating = pd.read_csv(os.path.join(DATA, "dated_source_panel_2016_2025.csv"))[
        ["region_code", "year", "eating_out_jpy_per_household"]]
    df = df.merge(eating, on=["region_code", "year"], how="left", validate="one_to_one")
    df = df.rename(columns={
        "tfr_children_per_woman":"tfr",
        "observed_income_jpy_per_resident":"income",
        "eating_out_jpy_per_household":"eating_out",
        "china_national_crop_import_kg_per_resident":"cn_import",
        "usa_national_crop_import_kg_per_resident":"us_import",
    })
    for c in ["tfr","income","eating_out","cn_import","us_import"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["income_obs"]    = df["income_observed"].astype(bool)
    df["log_income"]    = np.log(df["income"])
    df["log_eating_out"]= np.log(df["eating_out"])
    df["year_c"]        = df["year"] - 2016
    df["year_c2"]       = df["year_c"]**2
    return df

def load_full_panel():
    df = pd.read_csv(os.path.join(DATA, "dated_source_panel_2016_2025.csv")).rename(columns={
        "tfr_children_per_woman":"tfr",
        "eating_out_jpy_per_household":"eating_out",
        "capital_meals_out_jpy_per_household":"cap_meals",
        "observed_income_jpy_per_resident":"income",
    })
    for c in ["tfr","eating_out","cap_meals","income"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["log_eating_out"] = np.log(df["eating_out"])
    df["log_cap_meals"]  = np.log(df["cap_meals"])
    return df

def load_period_panel():
    dp = pd.read_csv(os.path.join(DATA, "model_panel_periods_no_year.csv"))
    for c in ["tfr_children_per_woman","observed_income_jpy_per_resident",
              "eating_out_jpy_per_household","china_national_crop_import_kg_per_resident",
              "usa_national_crop_import_kg_per_resident","organic_farming_context_z",
              "female_gardening_context_z"]:
        dp[c] = pd.to_numeric(dp[c], errors="coerce")
    dp = dp.rename(columns={
        "tfr_children_per_woman":"tfr",
        "observed_income_jpy_per_resident":"income",
        "eating_out_jpy_per_household":"eating_out",
        "china_national_crop_import_kg_per_resident":"cn_import",
        "usa_national_crop_import_kg_per_resident":"us_import",
    })
    dp["log_income"]     = np.log(dp["income"])
    dp["log_eating_out"] = np.log(dp["eating_out"])
    dp["period_code"]    = dp["period_code"].astype(str)
    return dp
