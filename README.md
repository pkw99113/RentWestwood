# RentWestwood: Where Should a UCLA Student Live?

**Question**: For a UCLA student choosing where to live, which option costs less once rent, lease length, and commute are counted: UCLA University Apartments, Westwood (90024), or West LA / Sawtelle (90025)?

This is v2 of the project. v1 (a Zillow scraper + rent price model) was retired because its data could not be trusted. See [archive/v1](archive/v1/README.md) for what went wrong and why.

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
| 4 | Neighborhood comparison | Next |
| 5 | Rent trends | |
| 6 | Price drivers (interpretable regression) | |
| 7 | Scenario analysis | |
| 8 | Dashboard + report | |

## Repository structure
```
docs/        step-by-step notes (problem definition, data log, findings)
data/raw/    original downloads (unchanged)
data/processed/  cleaned tables
sql/         SQL queries
notebooks/   analysis notebooks
scripts/     data preparation scripts
archive/v1/  retired first version (reference only)
```
