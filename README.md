# RentWestwood: Where Should a UCLA Student Live?

**Question**: For a UCLA student choosing where to live, which option costs less once rent, lease length, and commute are counted: UCLA University Apartments, Westwood (90024), or West LA / Sawtelle (90025)?

📄 **Full report (Korean): [REPORT.md](REPORT.md)**

This is v2 of the project. v1 (a Zillow scraper + rent price model) was retired because its data could not be trusted. See [archive/v1](archive/v1/README.md) for what went wrong and why.

## Key findings so far
- **The summer plan decides the answer.** A student who leaves LA for the summer pays less in UCLA University Apartments in 88% of scenarios (median gap about $3,400/year), because off-campus leases run 12 months.
- **Group size matters next.** Two people sharing: UCLA is cheaper in almost every scenario. Four people in a 2-bedroom who sublet or stay in LA: West LA is cheaper in every scenario.
- **Westwood is never the cheapest option, and the gap is widening.** Its premium over West LA grew from 8% (2018 average) to 13% (2026). It costs about 12% more than West LA (ZORI, Oct 2026); choosing it only makes sense if the shorter commute is worth more than about $15–24 per hour.

## Approach
1. **Problem definition**: define the decision, the options, and one main metric: *effective monthly cost per person* (rent + utilities + commute cost + value of commute time). → [docs/01_problem_definition.md](docs/01_problem_definition.md)
2. **Data collection**: public, citable sources only (Zillow Research ZORI, HUD Small Area Fair Market Rents, UCLA Housing rates). Every source and data quality check is logged.
3. **Cleaning + SQL**: load into a database and build per-person cost tables with SQL.
4. **Analysis**: compare neighborhoods, track rent trends, and run scenarios (number of roommates, commute mode, value of time).
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
