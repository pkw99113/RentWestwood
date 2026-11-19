-- 06. Sensitivity analysis on the EFFECTIVE annual cost per person:
--     rent (depends on summer plan) + commute cash cost + value of commute time.
--
-- Four assumptions are varied together for each of the 8 UCLA layouts:
--   rent_method (3):   zori_adjusted (main) / safmr (conservative) / safmr_110 (SAFMR × 1.1)
--   summer_plan (5):   away / sublet_50 / sublet_70 / sublet_90 / stay_in_la
--                        away: off-campus tenant still pays 12 months; UCLA pays the contract only
--                        sublet_X: off-campus tenant recovers X% of 3 summer months
--                        stay_in_la: UCLA resident rents 3 summer months in the cheapest neighborhood
--   car_profile (3):   how the student actually commutes from a non-Westwood neighborhood
--                        transit:      bus/rail
--                        drives_owned: drives a car they already own (parking + fuel/maintenance)
--                        drives_bought: drives a car bought because of where they live (+ ownership cost)
--                      Westwood and UCLA housing residents walk in every profile.
--   time_value (3):    $0, $20, $35 per hour of commuting
-- 3 × 5 × 3 × 3 = 135 scenarios per layout, 1,080 in total.
-- Commuting happens in the 9 school months. UCLA housing is treated like Westwood (walk).

CREATE OR REPLACE TABLE sensitivity AS
WITH rent_method(rent_method) AS (
    VALUES ('zori_adjusted'), ('safmr'), ('safmr_110')
),
summer_plan(summer_plan, sublet_recovery, ucla_needs_summer_housing) AS (
    VALUES ('away', 0.0, FALSE), ('sublet_50', 0.5, FALSE), ('sublet_70', 0.7, FALSE),
           ('sublet_90', 0.9, FALSE), ('stay_in_la', 0.0, TRUE)
),
car_profile(car_profile) AS (
    VALUES ('transit'), ('drives_owned'), ('drives_bought')
),
time_value(time_value) AS (
    VALUES (0.0), (20.0), (35.0)
),
-- Off-campus unit rent for every ZIP × bedrooms × rent method
rent AS (
    SELECT m.zip, m.area, m.bedrooms, r.rent_method,
           CASE r.rent_method
               WHEN 'zori_adjusted' THEN m.est_market_rent
               WHEN 'safmr'         THEN m.safmr
               WHEN 'safmr_110'     THEN m.safmr * 1.10
           END AS unit_rent
    FROM market_rent m
    CROSS JOIN rent_method r
),
-- Annual commute cost (9 school months) for every ZIP × mode × time value
commute_annual AS (
    SELECT c.zip, c.mode, t.time_value,
           9 * (c.cash_per_school_month + c.hours_per_school_month * t.time_value)
             + 12 * c.fixed_per_month                                   AS annual_commute_cost
    FROM commute_cost c CROSS JOIN time_value t
),
-- Commute cost per ZIP for each profile: walk where walking is possible (Westwood), otherwise the profile's mode
best_commute AS (
    SELECT a.zip, p.car_profile, a.time_value, MIN(a.annual_commute_cost) AS annual_commute_cost
    FROM commute_annual a
    CROSS JOIN car_profile p
    WHERE a.mode = 'walk'
       OR (p.car_profile = 'transit'       AND a.mode = 'transit')
       OR (p.car_profile = 'drives_owned'  AND a.mode = 'car_owned')
       OR (p.car_profile = 'drives_bought' AND a.mode = 'car_bought')
    GROUP BY a.zip, p.car_profile, a.time_value
),
pp AS (
    SELECT u.unit_type, u.occupants, u.total_contract_usd,
           r.zip, r.area, r.rent_method, r.unit_rent / u.occupants AS pp_monthly
    FROM ucla_apartments u
    JOIN rent r ON r.bedrooms = u.bedrooms
),
ucla_commute AS (       -- UCLA housing is on/next to campus: same walking cost as Westwood
    SELECT car_profile, time_value, annual_commute_cost FROM best_commute WHERE zip = '90024'
),
scenarios AS (
    -- Off-campus options
    SELECT p.unit_type, p.rent_method, s.summer_plan, b.car_profile, b.time_value,
           p.area AS option,
           p.pp_monthly * (12 - 3 * s.sublet_recovery)          AS annual_rent,
           b.annual_commute_cost
    FROM pp p
    CROSS JOIN summer_plan s
    JOIN best_commute b ON b.zip = p.zip
    UNION ALL
    -- UCLA option: one row per scenario (GROUP BY collapses the 7 ZIP rows of pp)
    SELECT p.unit_type, p.rent_method, s.summer_plan, uc.car_profile, uc.time_value,
           'UCLA' AS option,
           MIN(p.total_contract_usd)
             + CASE WHEN s.ucla_needs_summer_housing THEN 3 * MIN(p.pp_monthly) ELSE 0 END AS annual_rent,
           MIN(uc.annual_commute_cost)
    FROM pp p
    CROSS JOIN summer_plan s
    CROSS JOIN ucla_commute uc
    GROUP BY p.unit_type, p.rent_method, s.summer_plan, s.ucla_needs_summer_housing, uc.car_profile, uc.time_value
)
SELECT *,
       annual_rent + annual_commute_cost AS annual_cost,
       RANK() OVER (PARTITION BY unit_type, rent_method, summer_plan, car_profile, time_value
                    ORDER BY annual_rent + annual_commute_cost) AS cost_rank
FROM scenarios;

-- Main-case view: 2BR shared by 4, main rent estimate, sublet 70%, time valued at $20/hour
SELECT car_profile, option,
       ROUND(annual_rent) AS annual_rent, ROUND(annual_commute_cost) AS annual_commute,
       ROUND(annual_cost) AS annual_total, cost_rank
FROM sensitivity
WHERE unit_type = '2/4 apartment' AND rent_method = 'zori_adjusted'
  AND summer_plan = 'sublet_70' AND time_value = 20
ORDER BY car_profile, cost_rank;
