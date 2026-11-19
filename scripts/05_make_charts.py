"""Charts for REPORT.md (run after scripts/03_run_sql.py)."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path(__file__).resolve().parents[1]
P, IMG = ROOT / "data" / "processed", ROOT / "images"
for old in IMG.glob("*.png"):
    old.unlink()

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
# One fixed color per option across every chart (reference categorical palette, slots 1-8)
COLOR = {"Westwood": "#2a78d6", "West LA / Sawtelle": "#eb6834", "UCLA": "#1baf7a",
         "Brentwood": "#eda100", "Palms": "#e87ba4", "Rancho Park": "#008300",
         "Mar Vista": "#6250d6", "Koreatown": "#e34948"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
})
money = matplotlib.ticker.FuncFormatter(lambda v, _: f"${v:,.0f}")
pct = matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%")

# ---------- 1. Rent trend by neighborhood ----------
t = pd.read_csv(P / "02_zori_trend.csv", parse_dates=["month"])
fig, ax = plt.subplots(figsize=(9.5, 5.6))
last = t[t["month"] == t["month"].max()].sort_values("rent")
for area, g in t.groupby("area"):
    ax.plot(g["month"], g["rent"], color=COLOR[area], lw=2)
# direct labels at the line ends, nudged apart so they don't overlap
ys, min_gap = [], 70
for _, r in last.iterrows():
    y = r["rent"] if not ys else max(r["rent"], ys[-1] + min_gap)
    ys.append(y)
    ax.annotate(f"{r['area']}  ${r['rent']:,.0f}", (r["month"], y), xytext=(8, 0),
                textcoords="offset points", va="center", fontsize=9.5, color=INK)
ax.set_xlim(t["month"].min(), t["month"].max() + pd.Timedelta(days=900))
ax.yaxis.set_major_formatter(money)
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_title("Typical market rent by neighborhood (Zillow ZORI), Jan 2018 – Oct 2026", loc="left", fontsize=13, pad=10)
fig.savefig(IMG / "01_rent_trend.png", dpi=160, bbox_inches="tight")
plt.close(fig)

# ---------- 2. Effective annual cost: rent + commute (main case) ----------
s = pd.read_csv(P / "sensitivity_full.csv")
cc = pd.read_csv(P / "05_commute_cost.csv")
m = s[(s["unit_type"] == "2/4 apartment") & (s["rent_method"] == "zori_adjusted")
      & (s["summer_plan"] == "sublet_70") & (s["car_profile"] == "transit") & (s["time_value"] == 20)].copy()
m = m.sort_values("annual_cost", ascending=True)
fig, ax = plt.subplots(figsize=(9.5, 4.9))
y = range(len(m))[::-1]
SEG = {"Rent": "#52514e", "Commute time ($20/hr)": "#b4b2ab"}
ax.barh(y, m["annual_rent"], color=SEG["Rent"], height=0.62, label="Rent")
ax.barh(y, m["annual_commute_cost"], left=m["annual_rent"], color=SEG["Commute time ($20/hr)"],
        height=0.62, label="Commute time ($20/hr)", edgecolor=SURFACE, linewidth=2)
for yi, (_, r) in zip(y, m.iterrows()):
    ax.text(r["annual_cost"] + 150, yi, f"${r['annual_cost']/1000:.1f}K", va="center", fontsize=9.5)
ax.set_yticks(list(y), m["option"])
for lbl in ax.get_yticklabels():
    lbl.set_color(COLOR[lbl.get_text()])
    lbl.set_fontweight("bold")
ax.xaxis.set_major_formatter(money)
ax.set_xlim(0, m["annual_cost"].max() * 1.12)
ax.grid(axis="y", visible=False)
ax.legend(frameon=False, ncol=2, loc="upper left", bbox_to_anchor=(0, -0.08))
ax.set_title("Effective annual cost per person: 2BR shared by 4, transit, sublet summer (70%)",
             loc="left", fontsize=12.5, pad=10)
fig.savefig(IMG / "02_effective_cost.png", dpi=160, bbox_inches="tight")
plt.close(fig)

# ---------- 3. Who wins as commute time gets valued (transit riders) ----------
w = s[(s["cost_rank"] == 1)]
order = ["Koreatown", "Palms", "Westwood", "UCLA"]
fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
titles = {"transit": "Transit", "drives_owned": "Drives own car", "drives_bought": "Buys a car to commute"}
for ax, prof in zip(axes, ["transit", "drives_owned", "drives_bought"]):
    share = (w[w["car_profile"] == prof].groupby("time_value")["option"]
             .value_counts(normalize=True).mul(100).unstack(fill_value=0).reindex(columns=order, fill_value=0))
    left = pd.Series(0.0, index=share.index)
    yy = list(range(len(share)))[::-1]
    for opt in order:
        ax.barh(yy, share[opt], left=left, color=COLOR[opt], height=0.6, edgecolor=SURFACE, linewidth=2,
                label=opt)
        for yi, (tv, v) in zip(yy, share[opt].items()):
            if v >= 12:
                ax.text(left[tv] + v / 2, yi, f"{v:.0f}%", ha="center", va="center", fontsize=9, color="white")
        left += share[opt]
    ax.set_yticks(yy, [f"${v:.0f}/hr" for v in share.index])
    ax.set_xlim(0, 100)
    ax.xaxis.set_major_formatter(pct)
    ax.grid(axis="y", visible=False)
    ax.set_title(titles[prof], loc="left", fontsize=11)
axes[0].set_ylabel("Value of commute time")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, ncol=4, frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.08))
fig.suptitle("Cheapest option across scenarios, by how the student commutes and how they value commute time",
             x=0.01, y=1.07, ha="left", fontsize=12.5)
fig.savefig(IMG / "03_winner_by_time_value.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("saved", sorted(p.name for p in IMG.glob("*.png")))
