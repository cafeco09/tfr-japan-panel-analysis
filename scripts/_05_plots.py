"""Scatter + fitted plots."""
import numpy as np, statsmodels.formula.api as smf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _00_load import load_2016_2023, OUT

def run():
    df = load_2016_2023()
    d1 = df[df["income_obs"] & df["income"].notna()].copy()

    fig, ax = plt.subplots(1, 2, figsize=(13, 5))
    ax[0].scatter(d1["log_income"], d1["tfr"], s=10, alpha=0.4, color="steelblue")
    b = np.polyfit(d1["log_income"], d1["tfr"], 1)
    xs = np.linspace(d1["log_income"].min(), d1["log_income"].max(), 100)
    ax[0].plot(xs, np.polyval(b, xs), "r-", lw=2)
    ax[0].set_xlabel("log(income per resident, JPY)"); ax[0].set_ylabel("TFR")
    ax[0].set_title(f"Raw: slope={b[0]:.3f}")

    m = smf.ols("tfr ~ log_income + log_eating_out + C(region_code)+C(year)", data=d1).fit()
    pr = m.resid + m.params["log_income"]*d1["log_income"]
    ax[1].scatter(d1["log_income"], pr, s=10, alpha=0.35, color="darkgreen")
    b2 = np.polyfit(d1["log_income"], pr, 1)
    ax[1].plot(xs, np.polyval(b2, xs), "r-", lw=2)
    ax[1].set_xlabel("log(income per resident, JPY)"); ax[1].set_ylabel("Partial residual TFR")
    ax[1].set_title(f"After pref+year FE: slope={m.params['log_income']:.3f}")
    plt.tight_layout(); plt.savefig(os.path.join(OUT,"figures","scatter_income_tfr.png"), dpi=140)

    pm = d1.groupby("region_code").agg(
        mean_log_income=("log_income","mean"), mean_tfr=("tfr","mean")).reset_index()
    fig2, ax2 = plt.subplots(figsize=(7,5))
    ax2.scatter(pm["mean_log_income"], pm["mean_tfr"], s=40, color="purple")
    for _,r in pm.iterrows():
        ax2.annotate(r["region_code"], (r["mean_log_income"], r["mean_tfr"]),
                     fontsize=6, alpha=0.7, xytext=(3,3), textcoords="offset points")
    b3 = np.polyfit(pm["mean_log_income"], pm["mean_tfr"], 1)
    xs3 = np.linspace(pm["mean_log_income"].min(), pm["mean_log_income"].max(), 100)
    ax2.plot(xs3, np.polyval(b3, xs3), "r-", lw=2)
    ax2.set_xlabel("Mean log(income) 2016-2023"); ax2.set_ylabel("Mean TFR 2016-2023")
    ax2.set_title(f"Prefecture means: slope={b3[0]:.3f}")
    plt.tight_layout(); plt.savefig(os.path.join(OUT,"figures","scatter_pref_means.png"), dpi=140)
    print("figures written.")

if __name__ == "__main__":
    run()
