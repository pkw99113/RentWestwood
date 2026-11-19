"""Tidy, labeled CSVs for the Tableau Public dashboard (run after scripts/03_run_sql.py)."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P, OUT = ROOT / "data" / "processed", ROOT / "data" / "tableau"
for old in OUT.glob("*.csv"):
    old.unlink()

SUMMER = {"away": "1. Leave LA", "sublet_50": "2. Sublet 50%", "sublet_70": "3. Sublet 70%",
          "sublet_90": "4. Sublet 90%", "stay_in_la": "5. Stay in LA"}
METHOD = {"zori_adjusted": "Main (ZORI-adjusted)", "safmr": "Conservative (HUD SAFMR)",
          "safmr_110": "High (SAFMR x 1.1)"}
PROFILE = {"transit": "1. Transit", "drives_owned": "2. Drives own car", "drives_bought": "3. Buys a car to commute"}

# 1. Rent trend: already long (one row per ZIP × month)
pd.read_csv(P / "02_zori_trend.csv").to_csv(OUT / "rent_trend.csv", index=False)

# 2. Scenario costs: layout × rent method × summer plan × commute profile × time value × option
s = pd.read_csv(P / "sensitivity_full.csv")
occ = pd.read_csv(ROOT / "data" / "raw" / "ucla_university_apartments_2026_27.csv")[["unit_type", "occupants"]]
s = s.merge(occ, on="unit_type", how="left")
s["group_size"] = s["occupants"].map(lambda n: "2 people" if n <= 2 else f"{n} people")
s["summer_plan_label"] = s["summer_plan"].map(SUMMER)
s["rent_method_label"] = s["rent_method"].map(METHOD)
s["car_profile_label"] = s["car_profile"].map(PROFILE)
s["time_value_label"] = s["time_value"].map(lambda v: f"${v:.0f}/hr")
s["is_cheapest"] = (s["cost_rank"] == 1).astype(int)
for c in ["annual_rent", "annual_commute_cost", "annual_cost"]:
    s[c] = s[c].round(0)
s.to_csv(OUT / "scenario_costs.csv", index=False)

# 3. Commute cost by neighborhood and mode, and the time-value break-even table
pd.read_csv(P / "05_commute_cost.csv").to_csv(OUT / "commute_cost.csv", index=False)
b = pd.read_csv(P / "11_time_value_breakeven.csv")
b["car_profile_label"] = b["car_profile"].map(PROFILE)
b["summer_plan_label"] = b["summer_plan"].map(SUMMER)
b.to_csv(OUT / "time_value_breakeven.csv", index=False)
print(sorted(p.name for p in OUT.glob("*.csv")), len(s), "scenario rows")
