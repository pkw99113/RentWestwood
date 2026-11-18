"""Step 2: extract the study-area ZIPs from the raw public files and run quality checks.

Raw files (not committed, see data/README.md for download steps):
  data/raw/Zip_zori_uc_sfrcondomfr_sm_month.csv   Zillow Research, ZORI, ZIP level
  data/raw/fy2026_safmrs_revised.xlsx             HUD, FY2026 Small Area FMRs (revised)

Outputs:
  data/processed/zori_study_zips.csv     zip, area, month, zori   (long format)
  data/processed/safmr_study_zips.csv    zip, area, bedrooms, safmr
  docs/02_data_quality_report.md         results of the checks below
"""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"

# Analysis scope: the two ZIPs next to campus.
STUDY_ZIPS = {
    "90024": ("Westwood", "adjacent"),
    "90025": ("West LA / Sawtelle", "near"),
}
# Wider set used only to check that ZORI and SAFMR agree (a correlation needs more than 2 points).
VALIDATION_ZIPS = {
    **STUDY_ZIPS,
    "90064": ("Rancho Park", "near"),
    "90049": ("Brentwood", "near"),
    "90034": ("Palms", "far"),
    "90066": ("Mar Vista", "far"),
    "90005": ("Koreatown (90005)", "far"),
    "90020": ("Koreatown (90020)", "far"),
}
report = []

def log(line=""):
    print(line)
    report.append(line)

# ---------- ZORI ----------
zori = pd.read_csv(RAW / "Zip_zori_uc_sfrcondomfr_sm_month.csv", dtype={"RegionName": str})
zori["RegionName"] = zori["RegionName"].str.zfill(5)  # ZIPs can lose leading zeros
month_cols = [c for c in zori.columns if c[:2] == "20"]
log("## ZORI (Zillow Observed Rent Index)")
log(f"- Raw file: {len(zori):,} ZIPs, {len(month_cols)} months ({month_cols[0]} to {month_cols[-1]})")
log(f"- Duplicate ZIP rows: {zori['RegionName'].duplicated().sum()}")

z = zori[zori["RegionName"].isin(STUDY_ZIPS)]
log(f"- Study ZIPs found: {len(z)} of {len(STUDY_ZIPS)}")
z_long = z.melt(id_vars="RegionName", value_vars=month_cols, var_name="month", value_name="zori")
z_long = z_long.rename(columns={"RegionName": "zip"})
z_long["month"] = pd.to_datetime(z_long["month"]).dt.to_period("M").astype(str)
z_long["area"] = z_long["zip"].map(lambda k: STUDY_ZIPS[k][0])
z_long["distance_group"] = z_long["zip"].map(lambda k: STUDY_ZIPS[k][1])

log("- Months with data per ZIP (missing months are blank in the source, i.e. not enough listings):")
log("")
log("| ZIP | Area | First month | Last month | Months with data | Missing |")
log("| --- | --- | --- | --- | --- | --- |")
for k, g in z_long.groupby("zip"):
    ok = g.dropna(subset=["zori"])
    log(f"| {k} | {STUDY_ZIPS[k][0]} | {ok['month'].min()} | {ok['month'].max()} | {len(ok)} | {g['zori'].isna().sum()} |")
log("")
z_long = z_long.dropna(subset=["zori"]).sort_values(["zip", "month"])
z_long["zori"] = z_long["zori"].round(2)
z_long[["zip", "area", "distance_group", "month", "zori"]].to_csv(OUT / "zori_study_zips.csv", index=False)

# ---------- SAFMR ----------
safmr = pd.read_excel(RAW / "fy2026_safmrs_revised.xlsx", dtype={"ZIP\nCode": str})
safmr.columns = [" ".join(str(c).split()) for c in safmr.columns]  # headers contain line breaks
safmr["ZIP Code"] = safmr["ZIP Code"].str.zfill(5)
log("## HUD Small Area Fair Market Rents, FY2026 (revised)")
log(f"- Raw file: {len(safmr):,} rows, {safmr['ZIP Code'].nunique():,} unique ZIPs")
dup = safmr["ZIP Code"].duplicated(keep=False)
log(f"- ZIPs listed in more than one HUD area: {safmr.loc[dup, 'ZIP Code'].nunique():,} (a ZIP can cross metro boundaries)")

s = safmr[safmr["ZIP Code"].isin(STUDY_ZIPS)].copy()
log(f"- Study ZIPs found: {s['ZIP Code'].nunique()} of {len(STUDY_ZIPS)}, rows: {len(s)}")
log(f"- HUD areas for study ZIPs: {', '.join(sorted(' '.join(str(a).split()) for a in s['HUD Fair Market Rent Area Name'].unique()))}")
base_cols = {f"SAFMR {b}BR": b for b in range(5)}
s_long = s.melt(id_vars="ZIP Code", value_vars=list(base_cols), var_name="col", value_name="safmr")
s_long["bedrooms"] = s_long["col"].map(base_cols)
s_long = s_long.rename(columns={"ZIP Code": "zip"}).drop(columns="col")
s_long["area"] = s_long["zip"].map(lambda k: STUDY_ZIPS[k][0])
s_long["distance_group"] = s_long["zip"].map(lambda k: STUDY_ZIPS[k][1])
s_long = s_long.sort_values(["zip", "bedrooms"])
s_long[["zip", "area", "distance_group", "bedrooms", "safmr"]].to_csv(OUT / "safmr_study_zips.csv", index=False)
log(f"- Missing SAFMR values: {s_long['safmr'].isna().sum()}")
log("")

# ---------- Cross-check: ZORI vs SAFMR (validation set) ----------
last_month = month_cols[-1]
latest = zori.set_index("RegionName").loc[list(VALIDATION_ZIPS), last_month]
fmr = safmr.set_index("ZIP Code").loc[list(VALIDATION_ZIPS), ["SAFMR 1BR", "SAFMR 2BR"]]
fmr.columns = [1, 2]
log(f"## Cross-check: ZORI ({last_month[:7]}) vs SAFMR, validation set of {len(VALIDATION_ZIPS)} West/Central LA ZIPs")
log("ZORI is a typical market rent across all unit sizes; SAFMR is HUD's 40th-percentile rent (rent + utilities) by bedroom count.")
log("If ZORI sits between the 1BR and 2BR SAFMR, the two sources are telling a consistent story.")
log("")
log("| ZIP | Area | ZORI | SAFMR 1BR | SAFMR 2BR | ZORI / SAFMR 1BR |")
log("| --- | --- | --- | --- | --- | --- |")
for k in VALIDATION_ZIPS:
    log(f"| {k} | {VALIDATION_ZIPS[k][0]} | ${latest[k]:,.0f} | ${fmr.loc[k, 1]:,.0f} | ${fmr.loc[k, 2]:,.0f} | {latest[k] / fmr.loc[k, 1]:.2f} |")
log("")
corr = pd.concat([latest, fmr[1]], axis=1).corr().iloc[0, 1]
log(f"- Correlation between ZORI and SAFMR 1BR across the validation ZIPs: {corr:.2f}")

(ROOT / "docs" / "02_data_quality_report.md").write_text(
    "# 2단계. 데이터 품질 점검 결과 (자동 생성)\n\n`scripts/02_extract_study_area.py` 실행 결과. 해석은 `docs/02_data_collection.md` 참고.\n\n"
    + "\n".join(report) + "\n"
)
