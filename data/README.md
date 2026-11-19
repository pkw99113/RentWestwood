# Data log

Every dataset used in v2 is listed here with its source and retrieval date. Files in `data/raw/` are kept exactly as downloaded (or as transcribed from an official page); all changes happen in `data/processed/`.

## Sources

| File | Source | Unit | Retrieved | Status |
| --- | --- | --- | --- | --- |
| `raw/Zip_zori_uc_sfrcondomfr_sm_month.csv` (not committed, 10 MB) | [Zillow Research data](https://www.zillow.com/research/data/) → Rentals → ZORI (Smoothed): All Homes Plus Multifamily, Geography: ZIP Code | ZIP × month, 2015-01 to 2026-10 | 2026-11-18 | Downloaded |
| `raw/fy2026_safmrs_revised.xlsx` (not committed, 4 MB) | [HUD Small Area Fair Market Rents](https://www.huduser.gov/portal/datasets/fmr/smallarea/index.html) → FY2026 SAFMRs (revised) | ZIP × bedrooms (0-4BR) | 2026-11-18 | Downloaded |
| `raw/ucla_university_apartments_2026_27.csv` | UCLA Housing 2026-27 University Apartment rates: [1-bedroom](https://housing.ucla.edu/2026-27-university-apartment-1-bedroom-2-3-occupants-rates), [2-bedroom](https://housing.ucla.edu/2026-27-university-apartment-2-bedroom-3-4-occupants-rates) | per person, full academic year | 2026-11-18 | Transcribed, needs manual check (`verified = no`) |
| `raw/commute_times_google_maps.csv` | Google Maps, looked up 2026-11-19: transit (to Bruin Plaza) and driving (to UCLA Parking Structure 8) times and driving miles, arriving by 9:00 AM on Tue 2026-12-01; first (recommended) route; one origin intersection per neighborhood | ZIP | 2026-11-19 | Collected |
| `raw/commute_cost_assumptions.csv` | UCLA Transportation parking rates; AAA Your Driving Costs 2026; UCLA Bruin U-Pass (URLs in the file) | item | 2026-11-19 | Collected |
| `processed/zori_study_zips.csv` | Built by `scripts/02_extract_study_area.py` | 7 study ZIPs × month | | |
| `processed/safmr_study_zips.csv` | Built by `scripts/02_extract_study_area.py` | 7 study ZIPs × bedrooms | | |

To rebuild the processed files: put the two raw downloads in `data/raw/` and run `python scripts/02_extract_study_area.py`.

## Data quality notes
- **UCLA 2/3 shared bedroom**: the three quarterly installments listed on the page sum to $13,578.30, while the stated total contract is $13,982.76 ($404.46 gap). The other unit types match. Use the stated total contract and re-check against the page.
- UCLA rates are for the academic year, not 12 months. Converting to a monthly figure needs an explicit assumption about the number of months covered (decided in step 3).
