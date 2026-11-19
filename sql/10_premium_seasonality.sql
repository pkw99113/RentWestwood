-- 10. Is there a seasonal pattern in Westwood's premium over West LA?
-- Compare each month's premium with the same year's average premium (removes the long-run trend),
-- then average that gap by calendar month across years.

WITH monthly AS (
    SELECT
        month,
        100 * (MAX(CASE WHEN zip = '90024' THEN zori END)
             / MAX(CASE WHEN zip = '90025' THEN zori END) - 1) AS premium_pct
    FROM zori
    WHERE month >= DATE '2018-01-01'
    GROUP BY month
),
deviation AS (
    SELECT
        month,
        premium_pct - AVG(premium_pct) OVER (PARTITION BY YEAR(month)) AS gap_vs_year_avg
    FROM monthly
)
SELECT
    MONTH(month)                                     AS calendar_month,
    ROUND(AVG(gap_vs_year_avg), 2)                   AS avg_gap_pctpt,
    COUNT(*)                                         AS years,
    SUM(CASE WHEN gap_vs_year_avg > 0 THEN 1 ELSE 0 END) AS years_above_avg
FROM deviation
GROUP BY MONTH(month)
ORDER BY calendar_month;
