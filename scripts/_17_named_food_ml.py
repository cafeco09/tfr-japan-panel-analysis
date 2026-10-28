"""Chronological ML rerun with whole soyabeans separated from other foods.

No synthetic observations or country splits. Run after stages 15 and 16.
"""
import hashlib
import json
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone

from _13_ml_sensitivity_projections import grids, select, temporal_comparison, parameter_text, table

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "output" / "named_food_ml"


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    products = pd.read_csv(ROOT / "output/food_names/named_food_products_2016_2025.csv",
                           dtype={"hs4": str, "hs6": str})
    groups = pd.read_csv(ROOT / "output/food_names/food_groups_2016_2025.csv", dtype={"hs2": str})
    source = pd.read_csv(ROOT / "output/external_food_imports/analysis_data.csv")
    mapped = products[products.included_in_bec_food].groupby("year").import_value_current_usd.sum()
    soy = products[products.hs4.eq("1201")].groupby("year").import_value_current_usd.sum()
    source["soyabeans_usd"] = source.year.map(soy)
    source["other_mapped_food_usd"] = source.year.map(mapped) - source.soyabeans_usd
    for col in ["soyabeans_usd", "other_mapped_food_usd"]:
        assert source[col].gt(0).all() and source[col].notna().all()
        source["log_" + col] = np.log(source[col])
    assert np.allclose(source.soyabeans_usd + source.other_mapped_food_usd, source.year.map(mapped))
    wide = groups.pivot(index="year", columns="hs2", values="import_value_current_usd")
    # Coverage rule uses only the first outer training window, never later outcomes.
    eligible = wide.loc[2016:2020].notna().all() & wide.loc[2016:2020].gt(0).all()
    codes = list(wide.columns[eligible])
    excluded = list(wide.columns[~eligible])
    for code in codes:
        source["log_group_" + code] = np.log(source.year.map(wide[code]))
    primary = source[source.year.le(2024)].sort_values("year").reset_index(drop=True)
    assert len(primary) == 9 and primary.year.is_unique
    assert primary.filter(regex="^log_").replace([np.inf, -np.inf], np.nan).notna().all().all()
    feature_sets = {
        "total_external_food": ["log_external_food", "trend"],
        "soyabeans_and_other_food": ["log_soyabeans_usd", "log_other_mapped_food_usd", "trend"],
        "named_food_groups": ["log_group_" + c for c in codes] + ["trend"],
    }
    predictions, metrics, tuning = [], [], []
    fitted, parameters = {}, []
    sensitivity, stability = [], []
    for label, features in feature_sets.items():
        candidates = grids()
        if label == "named_food_groups":
            # Unregularised OLS is underdetermined here; it is not a valid comparison.
            del candidates["OLS_imports_and_trend"]
        p, m, t = temporal_comparison(primary, label, 5, candidates, features=features)
        predictions.append(p); metrics.append(m); tuning.append(t)
        for name, options in candidates.items():
            model, score = select(options, primary[features], primary.national_tfr)
            model.fit(primary[features], primary.national_tfr)
            fitted[label, name] = model
            parameters.append(dict(feature_set=label, model=name, inner_mse=score,
                                   parameters=parameter_text(model)))
            if label != "soyabeans_and_other_food":
                continue
            x = primary[features]
            for col in features[:-1]:
                changed = x.copy(); changed[col] += np.log1p(.01)
                support = ((changed >= x.min()) & (changed <= x.max())).all(axis=1)
                delta = model.predict(changed) - model.predict(x)
                sensitivity.append(dict(model=name, feature=col, change_fraction=.01,
                                        mean_tfr_change=float(delta[support].mean()),
                                        supported_points=int(support.sum())))
                for omitted in range(len(primary)):
                    keep = np.arange(len(primary)) != omitted
                    fit = clone(model).fit(x.loc[keep], primary.national_tfr.loc[keep])
                    support = ((changed >= x.loc[keep].min()) & (changed <= x.loc[keep].max()) &
                               (x >= x.loc[keep].min()) & (x <= x.loc[keep].max())).all(axis=1)
                    delta = fit.predict(changed) - fit.predict(x)
                    stability.append(dict(model=name, feature=col, omitted_year=int(primary.year.iloc[omitted]),
                                          mean_tfr_change=float(delta[support].mean()) if support.any() else np.nan,
                                          supported_points=int(support.sum())))
    pred = pd.concat(predictions, ignore_index=True)
    scores = pd.concat(metrics, ignore_index=True)
    assert pred.groupby(["dataset", "model"]).year.apply(list).apply(lambda y: y == [2021,2022,2023,2024]).all()
    assert (pred.train_end < pred.year).all()
    pred.to_csv(DEST / "chronological_predictions.csv", index=False)
    scores.to_csv(DEST / "model_comparison.csv", index=False)
    pd.concat(tuning).to_csv(DEST / "nested_tuning.csv", index=False)
    pd.DataFrame(parameters).to_csv(DEST / "selected_parameters.csv", index=False)
    pd.DataFrame(sensitivity).to_csv(DEST / "soyabean_predictive_sensitivity.csv", index=False)
    pd.DataFrame(stability).to_csv(DEST / "soyabean_leave_year_out.csv", index=False)
    source.to_csv(DEST / "analysis_data.csv", index=False)

    # Future values are assumptions. Preserve the primary final-rate fit and
    # separately report a fit including the provisional 2025 fertility rate.
    forecasts = []
    features = feature_sets["soyabeans_and_other_food"]
    anchor = source.loc[source.year.eq(2025)].iloc[0]
    scenarios = {"flat_2025_values": (0., 0.), "soy_plus_5pct_other_flat": (.05, 0.),
                 "soy_minus_5pct_other_flat": (-.05, 0.), "both_plus_5pct": (.05, .05),
                 "both_minus_5pct": (-.05, -.05)}
    for vintage, training in [("through_2024_final", primary), ("through_2025_provisional_rate", source)]:
        for name, options in grids().items():
            model, _ = select(options, training[features], training.national_tfr)
            model.fit(training[features], training.national_tfr)
            for scenario, (gs, go) in scenarios.items():
                for year in range(2026, 2031):
                    point = pd.DataFrame({"log_soyabeans_usd": [np.log(anchor.soyabeans_usd) + (year-2025)*np.log1p(gs)],
                                          "log_other_mapped_food_usd": [np.log(anchor.other_mapped_food_usd) + (year-2025)*np.log1p(go)],
                                          "trend": [year-2016]})
                    forecasts.append(dict(training_vintage=vintage, model=name, scenario=scenario, year=year,
                                          projected_tfr=float(model.predict(point)[0]),
                                          assumed_soyabeans_usd=float(np.exp(point.log_soyabeans_usd.iloc[0])),
                                          assumed_other_food_usd=float(np.exp(point.log_other_mapped_food_usd.iloc[0])),
                                          imports_outside_marginal_training_ranges=bool(((point[features[:-1]] < training[features[:-1]].min()) |
                                               (point[features[:-1]] > training[features[:-1]].max())).any(axis=None)),
                                          time_outside_training_range=True))
    forecast = pd.DataFrame(forecasts)
    forecast.to_csv(DEST / "projections_2026_2030.csv", index=False)
    metadata = dict(run_utc=datetime.now(timezone.utc).isoformat(), primary_n=9,
                    primary_years=list(range(2016,2025)), held_out_years=[2021,2022,2023,2024],
                    feature_sets=feature_sets, excluded_groups_initial_training_coverage=excluded,
                    group_coverage_rule="Positive, returned records in every initial training year 2016–2020; no zero imputation",
                    selection="Past-only nested expanding-window tuning and fold-specific scaling; four outer errors per model",
                    soy_scope="Whole soyabeans HS1201 including separately flagged sowing seeds; derivatives stay in other food",
                    other_food_scope="Mapped BEC food minus whole soyabeans, not published World total minus soyabeans",
                    synthetic_observations=0, projection_scope="Conditional nominal-value scenarios, no calibrated prediction intervals",
                    limitations="Contemporaneous imports supplied; conditional hindcasts, not advance forecasts. Many features and only nine outcomes; comparisons exploratory, no causal identification or significance claim.",
                    versions={p:version(p) for p in ["numpy","pandas","scikit-learn"]})
    metadata["input_sha256"] = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [
        ROOT/"output/food_names/named_food_products_2016_2025.csv", ROOT/"output/food_names/food_groups_2016_2025.csv",
        ROOT/"output/external_food_imports/analysis_data.csv"]}
    (DEST/"methods.json").write_text(json.dumps(metadata, indent=2)+"\n")
    flat = forecast[forecast.scenario.eq("flat_2025_values") & forecast.training_vintage.eq("through_2025_provisional_rate")]
    baseline = float(scores.loc[scores.model.eq("Linear_trend_only"), "MAE"].iloc[0])
    import_scores = scores[~scores.model.isin(["Persistence", "Linear_trend_only"])]
    beat_baseline = bool(import_scores.MAE.lt(baseline).any())
    stability_summary = pd.DataFrame(stability).groupby(["model", "feature"]).mean_tfr_change.agg(["min", "max"]).reset_index()
    report = ["# ML rerun: named foods and soyabeans", "",
        "Nine observed annual outcomes, 2016–2024. Identical expanding-window held-out years 2021–2024. Tuning and scaling use past data only. Contemporaneous import inputs make these conditional hindcasts. No synthetic rows are pooled.", "",
        "## Chronological comparison", "", table(scores,["dataset","model","validation_n","MAE","RMSE"]), "",
        f"Trend-only MAE is {baseline:.5f} TFR units. At least one import model beats it: {beat_baseline}. All import specifications and model families are retained rather than selecting a favourable result.", "",
        "The soyabean OLS model predicts approximately 0.096 for 2021 versus observed 1.30. This failure is retained in the scores. Whole-soyabean values varied little in the initial five training years before rising sharply in 2021; the short-sample multivariable fit extrapolates poorly. A small full-sample coefficient cannot be interpreted as evidence of reliable prediction.", "",
        "The first set reproduces the total-import benchmark. The second separates whole soyabeans (HS1201, including sowing seed) from other mapped food, without double counting. Soy oil, flour and sauce remain in other food. The third includes named HS2 groups that had complete positive records in the initial 2016–2020 training window. No missing values are replaced with zero. Underidentified OLS is omitted from the group model.", "",
        f"Named group model: {len(codes)} groups plus trend. Excluded initial-coverage groups: {', '.join(excluded) or 'none'}. The number of predictors is large relative to nine outcomes. Regularisation does not create independent information. Comparing many specifications against four errors risks selecting chance winners; these results are exploratory and no fresh untouched test set remains.", "",
        "## Soyabean predictive sensitivity", "", table(pd.DataFrame(sensitivity),["model","feature","change_fraction","mean_tfr_change","supported_points"]), "",
        "A 1% increase in one nominal import value holds time and the other import value fixed. Marginal support checks do not ensure realistic joint inputs. These are fitted responses, not causal effects or significance tests. Leave-year-out stability results are exported separately; those ranges are not confidence intervals.", "",
        table(stability_summary,["model","feature","min","max"]), "",
        "## Flat-import scenario, 2026–2030", "",
        "This table includes provisional 2025 TFR in training. Fits excluding that rate and all five import scenarios are also exported. These are extrapolations, not official forecasts or calibrated intervals. Tree and RBF models extrapolate time poorly.", "",
        table(flat.pivot(index="year",columns="model",values="projected_tfr").reset_index(),["year","OLS_imports_and_trend","Ridge","ElasticNet","SVR_RBF","RandomForest_shallow"]), "",
        "## Reproduce", "", "```bash", "python scripts/_15_external_food_analysis.py", "python scripts/_17_named_food_ml.py", "```", "",
        "Inputs, source hashes, coverage rules and software versions are in methods.json. Product provenance is retained in output/food_names/source_batches.csv and the archived Comtrade responses.", ""]
    (DEST/"ML_RERUN_RESULTS.md").write_text("\n".join(report))
    print(scores.to_string(index=False))
    print(pd.DataFrame(sensitivity).to_string(index=False))


if __name__ == "__main__":
    main()
