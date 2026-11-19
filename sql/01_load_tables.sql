-- 01. Load the three cleaned datasets into DuckDB tables.
-- read_csv_auto infers column types from the file; we force zip to text so leading zeros are kept.

CREATE OR REPLACE TABLE zori AS
SELECT CAST(zip AS VARCHAR) AS zip, area, distance_group, CAST(month || '-01' AS DATE) AS month, zori
FROM read_csv_auto('data/processed/zori_study_zips.csv', types = {'zip': 'VARCHAR'});

CREATE OR REPLACE TABLE safmr AS
SELECT CAST(zip AS VARCHAR) AS zip, area, distance_group, bedrooms, safmr
FROM read_csv_auto('data/processed/safmr_study_zips.csv', types = {'zip': 'VARCHAR'});

CREATE OR REPLACE TABLE ucla_apartments AS
SELECT unit_type, bedrooms, occupants, bedroom_sharing, total_contract_usd
FROM read_csv_auto('data/raw/ucla_university_apartments_2026_27.csv');
