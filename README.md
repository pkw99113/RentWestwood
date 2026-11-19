# RentWestwood: Where Should a UCLA Student Live?

**Question**: For a UCLA student choosing where to live, which option costs less once rent, lease length, and commute (time, parking, car costs) are counted: UCLA University Apartments or one of seven nearby neighborhoods (Westwood, West LA/Sawtelle, Rancho Park, Brentwood, Palms, Mar Vista, Koreatown)?

📄 **Full report (Korean): [REPORT.md](REPORT.md)**

This is v2 of the project. v1 (a Zillow scraper + rent price model) was retired because its data could not be trusted. See [archive/v1](archive/v1/README.md) for what went wrong and why.

## Key findings
- **Koreatown has the lowest rent, but commute time erases the savings.** With commute time valued at $0, Koreatown is cheapest in 92% of transit scenarios; valued at $20/hour, it is never the cheapest. It only beats UCLA housing if a student values commute time below about $13–19/hour.
- **A car does not fix a far neighborhood.** On Google Maps, driving from Koreatown is no faster than transit (typically 35–80 min vs 59 min) and adds about $200/month in parking and running costs. Buying a car in order to live farther away loses in every scenario, even when time is free.
- **Palms is the best value for transit riders.** For four people sharing a 2-bedroom who sublet in summer: $11.4K/year per person including commute time, vs $12.0K in Westwood and $13.0K in UCLA housing.
- **The summer plan still decides UCLA housing vs off campus.** Off-campus leases run 12 months, so students who leave LA in summer are usually better off in UCLA housing.

## Approach
1. **Problem definition**: define the decision, the options, and one main metric: *effective annual cost per person* (rent + commute cash cost + value of commute time). → [docs/01_problem_definition.md](docs/01_problem_definition.md)
2. **Data collection**: public, citable sources only (Zillow Research ZORI, HUD Small Area Fair Market Rents, UCLA Housing and Transportation rates, AAA driving costs, Google Maps commute times). Every source and data quality check is logged.
3. **Cleaning + SQL**: load into a database and build per-person cost tables with SQL.
4. **Analysis**: 1,080 scenarios (rent estimate × summer plan × commute mode × value of time × unit layout), time-value break-even, rent trends.
5. **Dashboard + report**: a recommendation table a student can actually use.

## Status
| Step | Topic | Status |
| --- | --- | --- |
| 1 | Problem definition and metrics | Done |
| 2 | Data collection and quality checks | Done → [docs/02_data_collection.md](docs/02_data_collection.md) |
| 3 | Cleaning + SQL | Done → [docs/03_sql_per_person_cost.md](docs/03_sql_per_person_cost.md) |
| 4 | Sensitivity analysis + recommendation | Done → [docs/04_sensitivity_and_recommendation.md](docs/04_sensitivity_and_recommendation.md) |
| 5 | Rent trends + charts | Done → [docs/05_rent_trend.md](docs/05_rent_trend.md) |
| 6 | Report + dashboard | Report done → [REPORT.md](REPORT.md) · Dashboard data ready → [docs/06_tableau_guide.md](docs/06_tableau_guide.md) |

## Understanding the code
Step-by-step code walkthrough (Korean): [docs/CODE_WALKTHROUGH.md](docs/CODE_WALKTHROUGH.md)

## Repository structure
```
docs/        step-by-step notes (problem definition, data log, findings)
data/raw/    original downloads (unchanged)
data/processed/  cleaned tables
sql/         SQL queries
notebooks/   analysis notebooks
scripts/     data preparation scripts
images/      charts used in the report
archive/v1/  retired first version (reference only)
```
