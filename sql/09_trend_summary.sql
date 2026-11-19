-- 09. Rent trend summary by year (2018 onward, the window where every ZIP has data).
-- Annual average rent per ZIP, growth vs the previous year, and Westwood's premium over West LA.

WITH yearly AS (
    SELECT
        zip,
        YEAR(month)       AS year,
        AVG(zori)         AS avg_rent,
        COUNT(*)          AS months       -- 2026 has only 10 months so far; flag partial years
    FROM zori
    WHERE month >= DATE '2018-01-01'
    GROUP BY zip, YEAR(month)
),
wide AS (
    SELECT
        year,
        MAX(months)                                         AS months,
        MAX(CASE WHEN zip = '90024' THEN avg_rent END)      AS westwood,
        MAX(CASE WHEN zip = '90025' THEN avg_rent END)      AS west_la
    FROM yearly
    GROUP BY year
)
SELECT
    year,
    months,
    ROUND(westwood)                                                         AS westwood_avg,
    ROUND(west_la)                                                          AS west_la_avg,
    -- LAG without a 12-row offset: one row per year, so the previous row is last year
    ROUND(100 * (westwood / LAG(westwood) OVER (ORDER BY year) - 1), 1)     AS westwood_growth_pct,
    ROUND(100 * (west_la  / LAG(west_la)  OVER (ORDER BY year) - 1), 1)     AS west_la_growth_pct,
    ROUND(100 * (westwood / west_la - 1), 1)                                AS westwood_premium_pct,
    -- Index: each ZIP's rent relative to its own 2018 average (2018 = 100)
    ROUND(100 * westwood / FIRST_VALUE(westwood) OVER (ORDER BY year), 1)   AS westwood_index_2018,
    ROUND(100 * west_la  / FIRST_VALUE(west_la)  OVER (ORDER BY year), 1)   AS west_la_index_2018
FROM wide
ORDER BY year;
