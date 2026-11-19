"""Step 5: static charts for REPORT.md (run after scripts/03_run_sql.py)."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path(__file__).resolve().parents[1]
P, IMG = ROOT / "data" / "processed", ROOT / "images"

# Reference palette (validated: categorical slots 1-3, light mode)
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
COLOR = {"Westwood": "#2a78d6", "West LA": "#eb6834", "UCLA": "#1baf7a"}

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "text.color": INK, "font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
})

def dollars(ax, axis="y"):
    fmt = matplotlib.ticker.FuncFormatter(lambda v, _: f"${v:,.0f}")
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)

# ---------- 1. Rent trend (two panels, no dual axis) ----------
t = pd.read_csv(P / "02_zori_trend.csv", parse_dates=["month"])
fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 6.2), sharex=True,
                             gridspec_kw={"height_ratios": [2.2, 1], "hspace": 0.12})
for col, name in [("westwood_rent", "Westwood"), ("west_la_rent", "West LA")]:
    a1.plot(t["month"], t[col], color=COLOR[name], lw=2)
    last = t.iloc[-1]
    a1.annotate(f"{name}  ${last[col]:,.0f}", (last["month"], last[col]), xytext=(6, 0),
                textcoords="offset points", va="center", color=INK, fontsize=10)
a1.set_title("Typical market rent (Zillow ZORI), Jan 2018 – Oct 2026", loc="left", fontsize=13, pad=10)
dollars(a1)
a2.plot(t["month"], t["westwood_premium_pct"], color=INK2, lw=2)
a2.set_ylabel("Westwood premium\nover West LA (%)")
a2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
a2.xaxis.set_major_locator(mdates.YearLocator())
a2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
a1.set_xlim(t["month"].min(), t["month"].max() + pd.Timedelta(days=420))
fig.savefig(IMG / "01_rent_trend.png", dpi=160, bbox_inches="tight")
plt.close(fig)

# ---------- 2. Annual cost per person, 2BR / 4 people, by summer plan ----------
s = pd.read_csv(P / "sensitivity_full.csv")
s = s[(s["unit_type"] == "2/4 apartment") & (s["rent_method"] == "zori_adjusted")]
plans = ["away", "sublet_50", "sublet_70", "sublet_90", "stay_in_la"]
labels = ["Leave LA", "Sublet\n50%", "Sublet\n70%", "Sublet\n90%", "Stay in LA"]
opts = ["UCLA", "West LA", "Westwood"]
fig, ax = plt.subplots(figsize=(9, 4.8))
w, gap = 0.26, 0.02
for i, o in enumerate(opts):
    vals = [s[(s["summer_plan"] == p) & (s["option"] == o)]["annual_cost"].iloc[0] for p in plans]
    xs = [j + (i - 1) * (w + gap) for j in range(len(plans))]
    ax.bar(xs, vals, width=w, color=COLOR[o], label=o)
    for x, v in zip(xs, vals):
        ax.text(x, v + 150, f"${v/1000:.1f}K", ha="center", va="bottom", fontsize=8.5, color=INK2)
ax.set_xticks(range(len(plans)), labels)
ax.set_ylim(0, 17500)
dollars(ax)
ax.grid(axis="x", visible=False)
ax.set_title("Annual cost per person: 2-bedroom shared by 4, by summer plan", loc="left", fontsize=13, pad=10)
ax.legend(frameon=False, ncol=3, loc="upper left", bbox_to_anchor=(0, 1.0))
fig.savefig(IMG / "02_cost_by_summer_plan.png", dpi=160, bbox_inches="tight")
plt.close(fig)

# ---------- 3. How often UCLA is cheapest, by summer plan ----------
wsh = pd.read_csv(P / "07_win_share.csv")
u = wsh[wsh["winner"] == "UCLA"].set_index("summer_plan")["share_pct"].reindex(plans).fillna(0)
fig, ax = plt.subplots(figsize=(9, 3.8))
bars = ax.barh(range(len(plans))[::-1], u.values, color=COLOR["UCLA"], height=0.55)
for b, v in zip(bars, u.values):
    ax.text(v + 1.5, b.get_y() + b.get_height() / 2, f"{v:.0f}%", va="center", fontsize=10, color=INK)
ax.set_yticks(range(len(plans))[::-1], [l.replace("\n", " ") for l in labels])
ax.set_xlim(0, 100)
ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
ax.grid(axis="y", visible=False)
ax.set_title("Share of scenarios where UCLA University Apartments are cheapest\n(8 unit layouts × 3 rent estimates per summer plan; West LA wins the rest)",
             loc="left", fontsize=12, pad=10)
fig.savefig(IMG / "03_ucla_win_share.png", dpi=160, bbox_inches="tight")
plt.close(fig)
print("saved", sorted(p.name for p in IMG.glob("*.png")))
