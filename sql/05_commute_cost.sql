-- 05. Monthly commute cost for each neighborhood and commute mode (one school month).
--
-- Modes:
--   walk        Westwood (and UCLA housing): time only
--   transit     time only (undergrad transit pass is fare-free and paid by every student regardless of address)
--   car_owned   student already has a car: UCLA parking permit + fuel/maintenance per mile + time
--   car_bought  student buys a car because of where they live: car_owned + fixed ownership cost
-- Time cost = minutes × 2 trips × campus days ÷ 60 × value of time (varied in 06).
-- Driving time adds 10 minutes each way for parking and walking from the structure (assumption).

CREATE OR REPLACE TABLE commute_cost AS
WITH params AS (
    SELECT
        16                                                                            AS campus_days_per_month,
        10                                                                            AS park_walk_min,
        (SELECT value FROM cost_assumptions WHERE item = 'ucla_commuter_parking_permit') * 3 / 9.0
                                                                                      AS parking_per_school_month,
        (SELECT SUM(value) FROM cost_assumptions
          WHERE item IN ('car_fuel_cost', 'car_maintenance_repair_tires'))           AS car_cost_per_mile,
        -- fixed ownership = AAA small sedan total − its operating part at 15,000 mi/yr, spread over 12 months
        ((SELECT value FROM cost_assumptions WHERE item = 'car_small_sedan_total_annual')
          - 15000 * (SELECT SUM(value) FROM cost_assumptions
                      WHERE item IN ('car_fuel_cost', 'car_maintenance_repair_tires'))) / 12.0
                                                                                      AS car_fixed_per_month
),
modes AS (
    -- walk: only where Google gave a walking time (Westwood)
    SELECT zip, 'walk' AS mode, walk_min AS one_way_min, 0.0 AS cash_per_school_month, 0.0 AS fixed_per_month
    FROM commute_times WHERE walk_min IS NOT NULL
    UNION ALL
    SELECT zip, 'transit', transit_min, 0.0, 0.0
    FROM commute_times WHERE transit_min IS NOT NULL
    UNION ALL
    SELECT c.zip, 'car_owned', c.drive_min_mid + p.park_walk_min,
           p.parking_per_school_month + c.drive_miles * 2 * p.campus_days_per_month * p.car_cost_per_mile,
           0.0
    FROM commute_times c, params p WHERE c.drive_miles IS NOT NULL
    UNION ALL
    SELECT c.zip, 'car_bought', c.drive_min_mid + p.park_walk_min,
           p.parking_per_school_month + c.drive_miles * 2 * p.campus_days_per_month * p.car_cost_per_mile,
           p.car_fixed_per_month
    FROM commute_times c, params p WHERE c.drive_miles IS NOT NULL
)
SELECT
    m.zip,
    t.area,
    m.mode,
    m.one_way_min,
    ROUND(m.one_way_min * 2 * p.campus_days_per_month / 60.0, 1) AS hours_per_school_month,
    ROUND(m.cash_per_school_month, 2)                            AS cash_per_school_month,
    ROUND(m.fixed_per_month, 2)                                  AS fixed_per_month
FROM modes m
JOIN commute_times t USING (zip)
CROSS JOIN params p;

SELECT * FROM commute_cost ORDER BY zip, mode;
