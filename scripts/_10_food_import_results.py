"""Descriptive national TFR / broad food-import comparisons; no organic interaction.

python scripts/_10_food_import_results.py
Nine final-labelled annual outcomes are primary; provisional 2025 is a sensitivity.
No causal identification claim is made by a time-series regression.
"""
from pathlib import Path
import hashlib
import json

import numpy as np
import openpyxl
import pandas as pd
import statsmodels.formula.api as smf

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/"output"/"food_import_results"
SOURCE=ROOT/"data"/"national_tfr_sources"/"mhlw_2025_provisional_tables.xlsx"
SOURCE_URL="https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai25/xls/R7toukeihyou.xlsx"


def table(frame,columns):
    f=frame[columns].copy()
    for col in f.select_dtypes(include="number"):
        f[col]=f[col].map(lambda x:f"{x:.4f}")
    return "| "+" | ".join(columns)+" |\n|"+"|".join(["---"]*len(columns))+"|\n"+"\n".join(
        "| "+" | ".join(map(str,r))+" |" for r in f.itertuples(index=False,name=None))


def fit(formula,data):
    result=smf.ols(formula,data,missing="raise").fit()
    assert np.linalg.matrix_rank(result.model.exog)==result.model.exog.shape[1]
    assert result.df_resid>=3
    return result


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    sheet=openpyxl.load_workbook(SOURCE,data_only=True)["第2表"]
    extracted=[]
    for row in sheet.iter_rows():
        year=row[1].value
        if isinstance(year,(int,float)) and 2016<=year<=2025:
            extracted.append(dict(year=int(year),national_tfr=row[16].value,
                                  release_status="Provisional rate" if year==2025 else "Final-labelled historical rate",
                                  source_url=SOURCE_URL,source_sheet=sheet.title,source_cell=row[16].coordinate))
    tfr=pd.DataFrame(extracted).sort_values("year")
    assert len(tfr)==10 and not tfr.year.duplicated().any()
    assert np.isfinite(tfr.national_tfr).all()
    tfr.to_csv(ROOT/"data"/"national_tfr_2016_2025.csv",index=False)
    imports=pd.read_csv(ROOT/"data"/"food_imports_china_usa_wide.csv")
    data=tfr.merge(imports,on="year",validate="one_to_one").sort_values("year")
    assert len(data)==10
    data["log_china_food"]=np.log(data.china_food_import_value_current_usd)
    data["log_usa_food"]=np.log(data.usa_food_import_value_current_usd)
    data["trend"]=data.year-2016
    for variable in ["national_tfr","log_china_food","log_usa_food"]:
        data["d_"+variable]=data[variable].diff()
    for variable in ["log_china_food","log_usa_food"]:
        data["lag_"+variable]=data[variable].shift()
    data.to_csv(DEST/"analysis_data.csv",index=False)
    formulas={
        "China_only":"national_tfr ~ log_china_food",
        "USA_only":"national_tfr ~ log_usa_food",
        "China_only_linear_trend":"national_tfr ~ log_china_food + trend",
        "USA_only_linear_trend":"national_tfr ~ log_usa_food + trend",
        "joint_no_trend":"national_tfr ~ log_china_food + log_usa_food",
        "joint_linear_trend":"national_tfr ~ log_china_food + log_usa_food + trend",
        "joint_quadratic_trend":"national_tfr ~ log_china_food + log_usa_food + trend + I(trend**2)",
        "joint_first_differences":"d_national_tfr ~ d_log_china_food + d_log_usa_food",
        "joint_one_year_lags":"national_tfr ~ lag_log_china_food + lag_log_usa_food + trend",
    }
    rows=[]
    influence=[]
    for sample_name,frame in [("2016_2024_final_labelled",data[data.year.le(2024)].copy()),
                              ("2016_2025_with_provisional_rate",data.copy())]:
        for name,formula in formulas.items():
            sample=frame.copy()
            if name=="joint_first_differences":
                sample=sample.dropna(subset=["d_national_tfr","d_log_china_food","d_log_usa_food"])
            elif name=="joint_one_year_lags":
                sample=sample.dropna(subset=["lag_log_china_food","lag_log_usa_food"])
            fitted=fit(formula,sample)
            for covariance in ["HC3","HAC_lag1"]:
                robust=(fitted.get_robustcov_results(cov_type="HC3",use_t=True) if covariance=="HC3"
                        else fitted.get_robustcov_results(cov_type="HAC",maxlags=1,use_correction=True,use_t=True))
                for j,variable in enumerate(fitted.model.exog_names):
                    if "food" not in variable:
                        continue
                    country="China" if "china" in variable else "USA"
                    ci=robust.conf_int()[j]
                    rows.append(dict(sample=sample_name,spec=name,formula=formula,covariance=covariance,
                                     country=country,variable=variable,coefficient=robust.params[j],
                                     se=robust.bse[j],p=robust.pvalues[j],ci_low=ci[0],ci_high=ci[1],
                                     change_for_10pct_higher_import_value=robust.params[j]*np.log(1.1),
                                     n=int(fitted.nobs),residual_df=int(fitted.df_resid),r2=fitted.rsquared,
                                     max_leverage=float(fitted.get_influence().hat_matrix_diag.max())))
        if sample_name=="2016_2024_final_labelled":
            for year in frame.year:
                sample=frame[frame.year.ne(year)].copy()
                fitted=fit(formulas["joint_linear_trend"],sample)
                for variable in ["log_china_food","log_usa_food"]:
                    influence.append(dict(omitted_year=int(year),variable=variable,coefficient=fitted.params[variable]))
    results=pd.DataFrame(rows)
    results.to_csv(DEST/"national_food_import_models.csv",index=False)
    pd.DataFrame(influence).to_csv(DEST/"leave_one_year_out.csv",index=False)
    primary=results[(results["sample"]=="2016_2024_final_labelled") & results.covariance.eq("HC3")]
    selected=primary[primary.spec.isin(["joint_no_trend","joint_linear_trend","joint_quadratic_trend","joint_first_differences","joint_one_year_lags"])]
    provisional=results[(results["sample"]=="2016_2025_with_provisional_rate") & results.covariance.eq("HC3") & results.spec.eq("joint_linear_trend")]
    metadata=dict(source_url=SOURCE_URL,source_sheet="第2表",source_cells="Q120:Q129",
                  source_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  tfr_source_vintage="MHLW 2025 provisional-release workbook; 2025 rate may be revised",
                  import_definition="BEC Rev.4 category 1, primary plus processed food and beverages",
                  units="Current US dollars, not deflated quantity or resident exposure",
                  organic_interaction=False,primary_years="2016–2024",primary_n=9,
                  sensitivity_years="2016–2025",sensitivity_n=10,
                  inference_caveat="HC3 and HAC with t references are small-sample diagnostics, not exact tests or causal validation")
    (DEST/"source_and_method.json").write_text(json.dumps(metadata,indent=2,ensure_ascii=False)+"\n")
    report=["# Broad food imports from China and USA: updated descriptive results", "",
            "28 October 2026. Country series are separate. No organic term is included.",
            "", "## Conclusion", "",
            "The 2016–2024 data do not establish a reliable association between national fertility and broad food-import values from either origin. Signs, magnitudes and uncertainty depend on the time specification. Non-significance is not evidence that an effect is absent. The new analysis does not support a causal claim.",
            "", "## Measurement and sample", "",
            "The outcome is official national TFR from MHLW Table 2, cells Q120–Q129 of the archived workbook, not the unweighted mean of prefectural rates. The primary sample excludes the provisional 2025 rate: nine annual observations, 2016–2024. Including 2025 gives ten observations and is a separate sensitivity. National imports are not duplicated across prefectures to inflate the information count.",
            "", "Imports use UN Comtrade BEC Rev.4 category 1 (food and beverages), covering primary and processed forms. China and USA values enter as separate log covariates. They are nominal US-dollar import values: prices, exchange rates, quantities and product composition can all change the series. They do not measure prefectural or individual food exposure, organic status or chemical treatment.",
            "", "## Joint-country models: primary sample", "",
            "Both country covariates are included together. HC3 standard errors and t reference distributions are reported below. A coefficient is the TFR difference associated with one log-point higher import value conditional on included terms; multiply by log(1.10) for a 10% value difference. Causal or biological interpretations are not justified.", "",
            table(selected,["spec","country","coefficient","se","p","ci_low","ci_high","n","residual_df"]),
            "", "Inference-method sensitivity is material: for USA in the joint linear-trend primary model, HC3 gives p = 0.128 while HAC with one lag gives p = 0.021. With nine observations, the smaller HAC p-value is not a reliable basis for selecting a significant result. The country coefficients are the same under both covariance methods; only estimated uncertainty changes.",
            "", "## Including provisional 2025", "",
            table(provisional,["spec","country","coefficient","se","p","n"]),
            "", "## Uncertainty and identification", "",
            "- Nine annual observations give only five residual degrees of freedom in the joint linear-trend model and four in the quadratic-trend model. Precision and diagnostics are fragile.",
            "- HC3 addresses heteroskedasticity and leverage, not serial dependence. HAC with one lag is also exported; with so few observations it is not a dependable asymptotic remedy. Neither is an exact finite-sample test.",
            "- Linear and quadratic trends impose different restrictions on unobserved national time patterns. Full year effects would absorb both import series, making their main effects unidentifiable. A high R² driven by the fertility trend is not evidence that imports explain fertility.",
            "- The series share national demand, exchange-rate and food-price determinants. Reverse causality and omitted economic/demographic factors remain possible. Lags and first differences do not automatically address these problems.",
            "- All predefined country-only, joint, trend, difference and lag comparisons, both covariance choices, and provisional-rate sensitivity are exported. They are exploratory specifications; do not select a conclusion using whichever p-value is smallest.",
            "- Leave-one-year-out estimates are exported to reveal influence. They are dependent diagnostics, not independent replications.",
            "", "## Moving towards stronger evidence", "",
            "1. Extend comparable historical national food series and harmonised TFR data, using a fixed definition and consistent source vintages. More years improve estimation but do not remove endogeneity.",
            "2. Measure price/quantity changes appropriately. Deflate values or use a documented volume index; converting currencies alone is not deflation. State whether the estimand concerns spending, physical imports or actual consumption.",
            "3. Obtain validated regional exposure or a defensible external supply/policy shock, with explicit assumptions about other channels. National time-series controls cannot substitute for an identification strategy.",
            "4. Specify the hypothesis, estimand, lag window, confounders, main model and sensitivity set before further result-driven model selection. Historical checks already inspected cannot be made confirmatory by relabelling them as pre-specified.",
            "5. Reserve a genuinely new period or dataset for validation and, if the aim is individual fertility or health mechanisms, obtain appropriately linked individual exposure/outcome data.",
            "", "## Reproduce", "", "```bash", "python scripts/_10_food_import_results.py", "```", "",
            "`national_food_import_models.csv` contains all numerical results. `analysis_data.csv`, `leave_one_year_out.csv` and `source_and_method.json` retain the analysis sample, influence checks and provenance.",
            "", "## Sources", "", "- MHLW national TFR workbook: "+SOURCE_URL,
            "- TFR provisional-rate note: https://www.mhlw.go.jp/toukei/saikin/hw/jinkou/geppo/nengai25/dl/tfr.pdf",
            "- Comtrade query URLs and retrieval dates: `data/food_import_sources/`.", ""]
    (DEST/"UPDATED_FOOD_IMPORT_RESULTS.md").write_text("\n".join(report))
    print(selected[["spec","country","coefficient","p","n"]].to_string(index=False))
    print(f"Results written to {DEST}")


if __name__=="__main__":
    main()
