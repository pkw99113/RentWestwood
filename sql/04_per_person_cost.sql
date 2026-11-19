-- 04. Per-person cost: each UCLA University Apartment type vs the same layout in each neighborhood.
--
-- Matching rule: same number of bedrooms and same number of people.
--   e.g. UCLA "2 bd / 4 person" is compared with a 2BR apartment in each ZIP split 4 ways.
--
-- Three ways to count cost (the answer depends on what the student does in summer):
--   school_year_monthly:      UCLA contract ÷ 9 months; off campus: monthly rent ÷ people
--   annual_if_away_in_summer: UCLA contract only; off campus: 12 months (typical lease)
--   annual_with_sublet:       off campus, subletting the 3 summer months and recovering 70% of rent

CREATE OR REPLACE TABLE per_person_cost AS
WITH params AS (
    SELECT 9 AS ucla_months, 12 AS lease_months, 3 AS summer_months, 0.7 AS sublet_recovery
),
ucla AS (
    SELECT
        'UCLA'                                   AS option,
        NULL                                     AS zip,
        u.unit_type, u.bedrooms, u.occupants,
        u.total_contract_usd / p.ucla_months     AS school_year_monthly,
        u.total_contract_usd                     AS annual_if_away_in_summer,
        u.total_contract_usd                     AS annual_with_sublet
    FROM ucla_apartments u, params p        -- params has one row, so this just attaches the constants
),
off_campus AS (
    SELECT
        m.area                                   AS option,
        m.zip,
        u.unit_type, u.bedrooms, u.occupants,
        m.est_market_rent / u.occupants                                              AS school_year_monthly,
        m.est_market_rent / u.occupants * p.lease_months                             AS annual_if_away_in_summer,
        m.est_market_rent / u.occupants * (p.lease_months - p.summer_months * p.sublet_recovery) AS annual_with_sublet
    FROM ucla_apartments u
    JOIN market_rent m ON m.bedrooms = u.bedrooms     -- one UCLA row × 7 ZIPs = 7 off-campus rows
    CROSS JOIN params p
)
SELECT * FROM ucla
UNION ALL
SELECT * FROM off_campus;

-- Side-by-side view for the most common layout, cheapest first
SELECT
    unit_type,
    option,
    ROUND(school_year_monthly)       AS school_year_monthly,
    ROUND(annual_if_away_in_summer)  AS annual_if_away,
    ROUND(annual_with_sublet)        AS annual_with_sublet,
    RANK() OVER (PARTITION BY unit_type ORDER BY annual_if_away_in_summer) AS rank_annual_if_away
FROM per_person_cost
WHERE unit_type = '2/4 apartment'
ORDER BY rank_annual_if_away;
