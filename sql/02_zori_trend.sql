-- 02. How have rents moved in each ZIP, and is Westwood's premium over West LA growing?
-- Output: one row per month since 2018: rent in each ZIP, year-over-year change, and the premium.

WITH yoy AS (
    SELECT
        zip,
        month,
        zori,
        -- LAG looks back 12 rows within the same ZIP (rows ordered by month) = same month last year
        LAG(zori, 12) OVER (PARTITION BY zip ORDER BY month) AS zori_last_year
    FROM zori
),
wide AS (
    -- Turn two rows per month (one per ZIP) into one row per month with a column per ZIP
    SELECT
        month,
        MAX(CASE WHEN zip = '90024' THEN zori END)           AS westwood,
        MAX(CASE WHEN zip = '90025' THEN zori END)           AS west_la,
        MAX(CASE WHEN zip = '90024' THEN zori_last_year END) AS westwood_ly,
        MAX(CASE WHEN zip = '90025' THEN zori_last_year END) AS west_la_ly
    FROM yoy
    GROUP BY month
)
SELECT
    month,
    ROUND(westwood)                                   AS westwood_rent,
    ROUND(west_la)                                    AS west_la_rent,
    ROUND(100 * (westwood / westwood_ly - 1), 1)      AS westwood_yoy_pct,
    ROUND(100 * (west_la / west_la_ly - 1), 1)        AS west_la_yoy_pct,
    ROUND(100 * (westwood / west_la - 1), 1)          AS westwood_premium_pct
FROM wide
WHERE month >= DATE '2018-01-01'
ORDER BY month;
