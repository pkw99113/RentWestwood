-- 02. How have rents moved in each neighborhood, and how does each compare with Westwood?
-- Output (long format): one row per ZIP × month since 2018.

WITH base AS (
    SELECT
        zip,
        area,
        month,
        zori,
        -- 12 rows back within the same ZIP (rows ordered by month) = same month last year
        LAG(zori, 12) OVER (PARTITION BY zip ORDER BY month) AS zori_last_year,
        -- Westwood's rent in the same month, attached to every ZIP's row
        MAX(CASE WHEN zip = '90024' THEN zori END) OVER (PARTITION BY month) AS westwood_same_month
    FROM zori
)
SELECT
    zip,
    area,
    month,
    ROUND(zori)                                            AS rent,
    ROUND(100 * (zori / zori_last_year - 1), 1)            AS yoy_pct,
    ROUND(100 * (zori / westwood_same_month - 1), 1)       AS pct_vs_westwood
FROM base
WHERE month >= DATE '2018-01-01'   -- filter AFTER the LAG, so 2018 rows still see their 2017 values
ORDER BY zip, month;
