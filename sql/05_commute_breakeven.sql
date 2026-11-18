-- 05. Is the cheaper rent in West LA worth the longer commute?
--
-- Break-even value of time = monthly savings vs Westwood ÷ extra commute hours per month.
-- If a student values an hour of their time above this number, Westwood is the better deal.
-- Assumptions (edit in params): West LA adds 15 minutes each way vs walking from Westwood,
-- 4 campus days a week ≈ 16 days per school month.

WITH params AS (
    SELECT 15 AS extra_minutes_one_way, 16 AS campus_days_per_month
),
pivoted AS (
    SELECT
        unit_type,
        occupants,
        MAX(CASE WHEN option = 'Westwood (90024)' THEN school_year_monthly END) AS westwood,
        MAX(CASE WHEN option = 'West LA (90025)'  THEN school_year_monthly END) AS west_la
    FROM per_person_cost
    GROUP BY unit_type, occupants
)
SELECT
    unit_type,
    occupants,
    ROUND(westwood)                                                 AS westwood_monthly,
    ROUND(west_la)                                                  AS west_la_monthly,
    ROUND(westwood - west_la)                                       AS monthly_savings_west_la,
    ROUND(p.extra_minutes_one_way * 2 * p.campus_days_per_month / 60.0, 1) AS extra_hours_per_month,
    ROUND((westwood - west_la)
          / (p.extra_minutes_one_way * 2 * p.campus_days_per_month / 60.0), 2) AS breakeven_usd_per_hour
FROM pivoted, params p
ORDER BY occupants, unit_type;
