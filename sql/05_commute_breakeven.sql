-- 05. Is a cheaper neighborhood worth the longer commute, compared with living in Westwood?
--
-- Instead of guessing each neighborhood's commute time, flip the question:
--   "How many extra minutes per one-way trip (vs walking from Westwood) can I accept
--    before the rent savings are used up?"
--   break-even minutes = monthly savings ÷ (value of time per minute × 2 trips × campus days)
-- A student compares this number with their own real commute.

WITH params AS (
    SELECT 20.0 AS value_of_time_per_hour,   -- $/hour; try 15 or 30 to see the effect
           16   AS campus_days_per_month     -- about 4 days a week
),
westwood AS (
    SELECT unit_type, school_year_monthly AS westwood_monthly
    FROM per_person_cost
    WHERE zip = '90024'
)
SELECT
    c.unit_type,
    c.option                                                        AS neighborhood,
    ROUND(c.school_year_monthly)                                    AS monthly_rent_pp,
    ROUND(w.westwood_monthly - c.school_year_monthly)               AS monthly_savings_vs_westwood,
    ROUND((w.westwood_monthly - c.school_year_monthly)
          / (p.value_of_time_per_hour / 60 * 2 * p.campus_days_per_month), 0) AS breakeven_extra_min_one_way
FROM per_person_cost c
JOIN westwood w USING (unit_type)
CROSS JOIN params p
WHERE c.zip IS NOT NULL AND c.zip <> '90024'      -- off-campus neighborhoods other than Westwood
  AND c.unit_type = '2/4 apartment'
ORDER BY breakeven_extra_min_one_way DESC;
