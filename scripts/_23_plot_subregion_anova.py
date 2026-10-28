"""Reproducible graphs for controlled prefectural ANOVA and contrasts."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"output/subregion_anova"
DEST=SOURCE/"figures"
BLUE="#25638B";ORANGE="#BB6A27";GREY="#89939D";INK="#203445"


def save(fig,name):
    fig.savefig(DEST/(name+".png"),dpi=180,bbox_inches="tight",facecolor="white")
    fig.savefig(DEST/(name+".svg"),bbox_inches="tight",facecolor="white")
    plt.close(fig)


def main():
    DEST.mkdir(parents=True,exist_ok=True)
    r=pd.read_csv(SOURCE/"significance_each_prefecture.csv").sort_values("difference_from_adjusted_prefecture_mean").reset_index(drop=True)
    anova=pd.read_csv(SOURCE/"ANOVA_type_II_classical.csv")
    assert len(r)==47 and r.year_cluster_Holm_significant_5pct.sum()==30
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.labelcolor":INK,
                         "text.color":INK,"axes.spines.top":False,"axes.spines.right":False,
                         "svg.fonttype":"none"})
    y=np.arange(len(r));effects=r.difference_from_adjusted_prefecture_mean.to_numpy()
    significant=r.year_cluster_Holm_significant_5pct.to_numpy()
    colours=np.where(significant,np.where(effects<0,ORANGE,BLUE),GREY)
    fig,ax=plt.subplots(figsize=(10,16))
    for i,row in r.iterrows():
        ax.plot([row.year_cluster_pointwise_ci_low,row.year_cluster_pointwise_ci_high],[i,i],color=colours[i],linewidth=1.4)
        ax.scatter(row.difference_from_adjusted_prefecture_mean,i,s=26,color=colours[i],zorder=3)
    ax.axvline(0,color=INK,linewidth=1,linestyle="--")
    ax.set_yticks(y,labels=r.prefecture);ax.invert_yaxis()
    ax.set_xlabel("Adjusted TFR difference from equally weighted prefectural mean")
    ax.grid(axis="x",color="#E4E9ED",linewidth=.7);ax.set_axisbelow(True)
    ax.set_title("Adjusted TFR differences across 47 prefectures",loc="left",fontsize=16,pad=42)
    ax.text(0,1.012,"2016–2022 · 329 records · 7 annual clusters\nControls: food imports, income, eating-out proxy and linear time trend",transform=ax.transAxes,fontsize=10)
    handles=[Line2D([0],[0],marker="o",color=ORANGE,label="Below mean; cluster-t Holm p < 0.05"),
             Line2D([0],[0],marker="o",color=BLUE,label="Above mean; cluster-t Holm p < 0.05"),
             Line2D([0],[0],marker="o",color=GREY,label="Cluster-t Holm p ≥ 0.05")]
    fig.legend(handles=handles,loc="lower left",bbox_to_anchor=(.16,.025),frameon=False,fontsize=9)
    fig.text(.16,.012,"Bars: pointwise 95% year-clustered intervals, not simultaneous intervals.\n30/47 pass the cluster-t Holm test; none passes bootstrap Holm (coarse seven-cluster resolution).",fontsize=9)
    fig.subplots_adjust(left=.2,right=.97,top=.92,bottom=.11)
    save(fig,"prefecture_adjusted_tfr_differences")

    # Every displayed method has the same 47-comparison Holm family.
    columns=["classical_Holm_p","year_cluster_Holm_p","wild_cluster_Holm_p"]
    values=r[columns].to_numpy();strength=np.minimum(-np.log10(np.maximum(values,1e-300)),6)
    fig,ax=plt.subplots(figsize=(10,16))
    cmap=plt.get_cmap("Blues");im=ax.imshow(strength,aspect="auto",cmap=cmap,vmin=0,vmax=6)
    ax.set_yticks(y,labels=r.prefecture);ax.set_xticks([0,1,2],labels=["Classical iid\nHolm p","Year-cluster t\nHolm p","Wild cluster\nHolm p"])
    ax.tick_params(axis="both",length=0,pad=7)
    for i in range(47):
        for j in range(3):
            ax.text(j,i,f"{values[i,j]:.2g}",ha="center",va="center",fontsize=8.5,color="white" if strength[i,j]>3 else INK)
    ax.set_title("Regional significance depends on inference assumptions",loc="left",fontsize=15,pad=55)
    ax.text(0,1.015,"Each prefecture versus adjusted prefectural mean · 47-test Holm correction\nNumbers are corrected p-values; p < 0.05 is the stated threshold",transform=ax.transAxes,fontsize=10)
    cbar=fig.colorbar(im,ax=ax,fraction=.035,pad=.04);cbar.set_label("−log₁₀(Holm p), colour capped at 6")
    counts=(values<.05).sum(axis=0)
    fig.text(.2,.045,f"Passing 5% threshold: classical {counts[0]}/47; cluster-t {counts[1]}/47; wild bootstrap {counts[2]}/47.",fontsize=10)
    fig.text(.2,.02,"Seven year clusters; 128 bootstrap sign patterns. Minimum two-sided bootstrap p = 0.015625,\nso none can pass 47-test Holm correction. This resolution limit does not establish equal regional TFR.",fontsize=9)
    fig.subplots_adjust(left=.2,right=.88,top=.9,bottom=.085)
    save(fig,"prefecture_significance_inference_sensitivity")

    terms=["C(region_code)","trend","log_income","log_food","log_eating_out"]
    a=anova.set_index("term").loc[terms]
    labels=["Prefecture category (46 df)","Linear time trend (1 df)","Log income (1 df)","Log food imports (1 df)","Log eating-out proxy (1 df)"]
    fig,ax=plt.subplots(figsize=(12,5.7))
    ax.barh(np.arange(5),a.F,color=[BLUE if p<.05 else GREY for p in a.p_classical],height=.58)
    ax.set_yticks(np.arange(5),labels=labels);ax.invert_yaxis();ax.set_xscale("log")
    ax.set_xlim(.008,500);ax.set_xlabel("Classical Type II F statistic (logarithmic axis)")
    ax.grid(axis="x",color="#E4E9ED",linewidth=.7);ax.set_axisbelow(True)
    for i,(_,row) in enumerate(a.iterrows()):
        ax.text(1.025,i,f"F = {row.F:.3g}\np = {row.p_classical:.3g}",transform=ax.get_yaxis_transform(),va="center",fontsize=10)
    ax.set_title("Controlled ANOVA: classical iid-error benchmark",loc="left",fontsize=15,pad=30)
    ax.text(0,1.025,"TFR outcome · 329 records, 2016–2022 · residual df = 278",transform=ax.transAxes,fontsize=10)
    fig.text(.26,.02,"F tests use different numerator degrees of freedom and assume iid homoskedastic errors.\nThese are not cluster-robust tests or causal importance scores. A 46-df cluster omnibus test is rank-deficient.",fontsize=9)
    fig.subplots_adjust(left=.27,right=.79,top=.81,bottom=.2)
    save(fig,"controlled_anova_classical_terms")
    print("Exported three checked-source figures in PNG and SVG.")


if __name__=="__main__":
    main()
