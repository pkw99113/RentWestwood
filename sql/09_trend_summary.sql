-- 09. Rent trend summary by year and neighborhood (2018 onward, the window where every ZIP has data).

WITH yearly AS (
    SELECT
        zip,
        area,
        YEAR(month)   AS year,
        AVG(zori)     AS avg_rent,
        COUNT(*)      AS months       -- 2026 has only 10 months so far; flag partial years
    FROM zori
    WHERE month >= DATE '2018-01-01'
    GROUP BY zip, area, YEAR(month)
)
SELECT
    zip,
    area,
    year,
    months,
    ROUND(avg_rent)                                                                   AS avg_rent,
    -- one row per ZIP per year, so the previous row within the ZIP is last year
    ROUND(100 * (avg_rent / LAG(avg_rent) OVER (PARTITION BY zip ORDER BY year) - 1), 1) AS growth_pct,
    -- index: each ZIP relative to its own 2018 average (2018 = 100)
    ROUND(100 * avg_rent / FIRST_VALUE(avg_rent) OVER (PARTITION BY zip ORDER BY year), 1) AS index_2018,
    -- Westwood's premium over this ZIP in the same year
    ROUND(100 * (MAX(CASE WHEN zip = '90024' THEN avg_rent END) OVER (PARTITION BY year) / avg_rent - 1), 1)
                                                                                      AS westwood_premium_pct
FROM yearly
ORDER BY zip, year;
