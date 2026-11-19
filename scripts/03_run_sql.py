"""Step 3: run the SQL files in order against an in-memory DuckDB database and save each final result."""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "processed"
con = duckdb.connect()

for sql_file in sorted((ROOT / "sql").glob("*.sql")):
    result = con.execute(sql_file.read_text())  # runs every statement; keeps the last result
    if result.description is None or result.description[0][0] == "Count":
        continue  # file only creates tables
    df = result.df()
    df.to_csv(OUT / f"{sql_file.stem}.csv", index=False)
    print(f"\n=== {sql_file.name} ({len(df)} rows)")
    print(df.to_string(index=False) if len(df) <= 40 else df.tail(14).to_string(index=False))

# Full scenario table (the SQL file's last SELECT only shows a summary)
con.execute("SELECT * FROM sensitivity ORDER BY unit_type, rent_method, summer_plan, cost_rank").df() \
   .to_csv(OUT / "sensitivity_full.csv", index=False)
