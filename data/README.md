# Data log

Every dataset used in v2 is listed here with its source and retrieval date. Files in `data/raw/` are kept exactly as downloaded (or as transcribed from an official page); all changes happen in `data/processed/`.

## Sources

| File | Source | Unit | Retrieved | Status |
| --- | --- | --- | --- | --- |
| `raw/ucla_university_apartments_2bd_2026_27.csv` | [UCLA Housing, 2026-27 University Apartment 2-bedroom (3 & 4 occupants) rates](https://housing.ucla.edu/2026-27-university-apartment-2-bedroom-3-4-occupants-rates) | per person, full academic year | 2026-11-18 | Transcribed, needs manual check (`verified = no`) |
| ZORI (planned) | [Zillow Research data](https://www.zillow.com/research/data/) — ZIP-level Zillow Observed Rent Index | ZIP × month | | To download |
| SAFMR FY2026 (planned) | [HUD Small Area Fair Market Rents](https://www.huduser.gov/portal/datasets/fmr/smallarea/index.html) | ZIP × bedrooms | | To download |
| UCLA residence halls (planned) | [UCLA Housing 2026-27 academic year rates](https://housing.ucla.edu/2026-2027-academic-year-rates) | per person, academic year, includes meal plan | | To collect |

## Data quality notes
- **UCLA 2/3 shared bedroom**: the three quarterly installments listed on the page sum to $13,578.30, while the stated total contract is $13,982.76 ($404.46 gap). The other unit types match. Use the stated total contract and re-check against the page.
- UCLA rates are for the academic year, not 12 months. Converting to a monthly figure needs an explicit assumption about the number of months covered (decided in step 3).
