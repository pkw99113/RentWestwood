"""Step 6: tidy, labeled CSVs for the Tableau Public dashboard (run after scripts/03_run_sql.py)."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P, OUT = ROOT / "data" / "processed", ROOT / "data" / "tableau"

SUMMER = {"away": "1. Leave LA", "sublet_50": "2. Sublet 50%", "sublet_70": "3. Sublet 70%",
          "sublet_90": "4. Sublet 90%", "stay_in_la": "5. Stay in LA"}
METHOD = {"zori_adjusted": "Main (ZORI-adjusted)", "safmr": "Conservative (HUD SAFMR)",
          "safmr_110": "High (SAFMR x 1.1)"}

# 1. Rent trend, long format: one row per month × area
z = pd.read_csv(P / "02_zori_trend.csv")
trend = z.melt(id_vars=["month", "westwood_premium_pct"], value_vars=["westwood_rent", "west_la_rent"],
               var_name="area", value_name="rent")
trend["area"] = trend["area"].map({"westwood_rent": "Westwood (90024)", "west_la_rent": "West LA (90025)"})
trend.to_csv(OUT / "rent_trend.csv", index=False)

# 2. Scenario costs: every layout × rent method × summer plan × option
s = pd.read_csv(P / "sensitivity_full.csv")
occ = pd.read_csv(ROOT / "data" / "raw" / "ucla_university_apartments_2026_27.csv")[["unit_type", "bedrooms", "occupants"]]
s = s.merge(occ, on="unit_type", how="left")
s["group_size"] = s["occupants"].map(lambda n: "2 people" if n <= 2 else f"{n} people")
s["summer_plan_label"] = s["summer_plan"].map(SUMMER)
s["rent_method_label"] = s["rent_method"].map(METHOD)
s["is_cheapest"] = (s["cost_rank"] == 1).astype(int)
s["annual_cost"] = s["annual_cost"].round(0)
s.to_csv(OUT / "scenario_costs.csv", index=False)

# 3. Commute break-even
pd.read_csv(P / "05_commute_breakeven.csv").to_csv(OUT / "commute_breakeven.csv", index=False)
print(sorted(p.name for p in OUT.glob("*.csv")), len(s), "scenario rows")
