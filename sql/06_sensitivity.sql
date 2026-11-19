-- 06. Sensitivity analysis: does the cheapest option change when the assumptions change?
--
-- Two assumptions are varied at the same time (3 × 5 = 15 scenarios per layout):
--   rent_method:  how off-campus rent is estimated
--       zori_adjusted  ZORI level × SAFMR bedroom ratio (main estimate, from 03)
--       safmr          HUD SAFMR as published (conservative, nearly no gap between ZIPs)
--       safmr_110      SAFMR × 1.10 (HUD's upper payment standard, closer to asking rents)
--   summer_plan:  what the student does in the 3 summer months
--       away           leaves LA; off-campus tenant still pays 12 months, UCLA pays the contract only
--       sublet_50/70/90  leaves LA and sublets, recovering 50/70/90% of summer rent
--       stay_in_la     stays in LA; off-campus tenant uses all 12 months,
--                      UCLA resident must rent summer housing for 3 months (priced at the cheapest neighborhood, same layout)

CREATE OR REPLACE TABLE sensitivity AS
WITH rent_method(rent_method) AS (
    VALUES ('zori_adjusted'), ('safmr'), ('safmr_110')
),
summer_plan(summer_plan, sublet_recovery, ucla_needs_summer_housing) AS (
    VALUES ('away', 0.0, FALSE), ('sublet_50', 0.5, FALSE), ('sublet_70', 0.7, FALSE),
           ('sublet_90', 0.9, FALSE), ('stay_in_la', 0.0, TRUE)
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
    CROSS JOIN rent_method r          -- every row × every method
),
-- Per-person monthly rent for every UCLA layout, both ZIPs, every method
pp AS (
    SELECT u.unit_type, u.occupants, u.total_contract_usd,
           r.zip, r.area, r.rent_method, r.unit_rent / u.occupants AS pp_monthly
    FROM ucla_apartments u
    JOIN rent r ON r.bedrooms = u.bedrooms
),
scenarios AS (
    -- Off-campus options
    SELECT p.unit_type, p.rent_method, s.summer_plan,
           p.area AS option,
           p.pp_monthly * (12 - 3 * s.sublet_recovery) AS annual_cost
    FROM pp p CROSS JOIN summer_plan s
    UNION ALL
    -- UCLA option (one per layout × method × summer plan)
    SELECT p.unit_type, p.rent_method, s.summer_plan,
           'UCLA' AS option,
           MIN(p.total_contract_usd)
             + CASE WHEN s.ucla_needs_summer_housing THEN 3 * MIN(p.pp_monthly) ELSE 0 END AS annual_cost
    FROM pp p CROSS JOIN summer_plan s
    -- pp has one row per ZIP for each layout; GROUP BY collapses them so UCLA appears once per scenario
    GROUP BY p.unit_type, p.rent_method, s.summer_plan, s.ucla_needs_summer_housing
)
SELECT *,
       RANK() OVER (PARTITION BY unit_type, rent_method, summer_plan ORDER BY annual_cost) AS cost_rank
FROM scenarios;

-- Winner of each scenario, laid out as summer plan (rows) × rent method (columns), for the most common layout
SELECT
    summer_plan,
    MAX(CASE WHEN rent_method = 'zori_adjusted' THEN option END) AS winner_zori_adjusted,
    MAX(CASE WHEN rent_method = 'safmr'         THEN option END) AS winner_safmr,
    MAX(CASE WHEN rent_method = 'safmr_110'     THEN option END) AS winner_safmr_110
FROM sensitivity
WHERE cost_rank = 1 AND unit_type = '2/4 apartment'
GROUP BY summer_plan
ORDER BY summer_plan;
