-- 11. Break-even value of time: below what hourly value of commuting time is each neighborhood
--     cheaper than UCLA University Apartments? (2BR shared by 4, main rent estimate)
--
-- Effective cost = cash cost + hours × v.  Neighborhood is cheaper when
--   cash_nb + 9·hours_nb·v < cash_ucla + 9·hours_ucla·v
--   ⇔ v < (cash_ucla − cash_nb) / (9 · (hours_nb − hours_ucla))
-- (9 = school months with commuting; hours are per school month)

WITH cash AS (           -- cash part only: time_value = 0 rows of the scenario table
    SELECT summer_plan, car_profile, option, annual_cost AS cash_cost
    FROM sensitivity
    WHERE unit_type = '2/4 apartment' AND rent_method = 'zori_adjusted' AND time_value = 0
),
hours AS (               -- monthly commute hours for each option under each profile
    SELECT DISTINCT area AS option,
           CASE mode WHEN 'transit' THEN 'transit' WHEN 'car_owned' THEN 'drives_owned'
                     WHEN 'car_bought' THEN 'drives_bought' END AS car_profile,
           hours_per_school_month
    FROM commute_cost WHERE mode <> 'walk'
),
ucla AS (
    SELECT c.summer_plan, c.car_profile, c.cash_cost AS ucla_cash,
           (SELECT hours_per_school_month FROM commute_cost WHERE mode = 'walk') AS ucla_hours
    FROM cash c WHERE c.option = 'UCLA'
)
SELECT
    c.car_profile,
    c.summer_plan,
    c.option                                                     AS neighborhood,
    ROUND(u.ucla_cash - c.cash_cost)                             AS cash_savings_vs_ucla,
    ROUND(9 * (h.hours_per_school_month - u.ucla_hours))         AS extra_commute_hours_per_year,
    CASE
        WHEN u.ucla_cash - c.cash_cost <= 0 THEN NULL            -- never cheaper, even if time is free
        ELSE ROUND((u.ucla_cash - c.cash_cost) / (9 * (h.hours_per_school_month - u.ucla_hours)), 1)
    END                                                          AS breakeven_usd_per_hour
FROM cash c
JOIN ucla u USING (summer_plan, car_profile)
JOIN hours h ON h.option = c.option AND h.car_profile = c.car_profile
WHERE c.option NOT IN ('UCLA', 'Westwood')
ORDER BY c.car_profile, c.summer_plan, breakeven_usd_per_hour DESC NULLS LAST;
