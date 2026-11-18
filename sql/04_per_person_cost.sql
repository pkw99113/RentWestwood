-- 04. Per-person cost: each UCLA University Apartment type vs the same layout off campus.
--
-- Matching rule: same number of bedrooms and same number of people.
--   e.g. UCLA "2 bd / 4 person" is compared with a 2BR apartment in 90024 and 90025 split 4 ways.
--
-- Two ways to count cost (the answer depends on what the student does in summer):
--   school_year_monthly: average monthly cost while living there during the school year
--       UCLA: contract ÷ 9 months (contract runs roughly mid-September to mid-June)
--       Off campus: monthly rent ÷ people
--   annual_if_away_in_summer: total paid in a year if the student leaves for the summer
--       UCLA: the contract only (nothing to pay in summer)
--       Off campus: 12 months, because a typical lease is 12 months
--   annual_with_sublet: same, but the student sublets the 3 summer months and recovers 70% of rent

CREATE OR REPLACE TABLE per_person_cost AS
WITH params AS (
    SELECT 9 AS ucla_months, 12 AS lease_months, 3 AS summer_months, 0.7 AS sublet_recovery
),
ucla AS (
    SELECT
        'UCLA University Apartments'                         AS option,
        u.unit_type,
        u.bedrooms,
        u.occupants,
        u.bedroom_sharing,
        u.total_contract_usd / p.ucla_months                 AS school_year_monthly,
        u.total_contract_usd                                  AS annual_if_away_in_summer,
        u.total_contract_usd                                  AS annual_with_sublet
    FROM ucla_apartments u, params p        -- params has one row, so this just attaches the constants
),
off_campus AS (
    SELECT
        CASE m.zip WHEN '90024' THEN 'Westwood (90024)' ELSE 'West LA (90025)' END AS option,
        u.unit_type,
        u.bedrooms,
        u.occupants,
        u.bedroom_sharing,
        m.est_market_rent / u.occupants                                            AS school_year_monthly,
        m.est_market_rent / u.occupants * p.lease_months                           AS annual_if_away_in_summer,
        m.est_market_rent / u.occupants
            * (p.lease_months - p.summer_months * p.sublet_recovery)               AS annual_with_sublet
    FROM ucla_apartments u
    JOIN market_rent m ON m.bedrooms = u.bedrooms     -- one UCLA row × two ZIPs = two off-campus rows
    CROSS JOIN params p
)
SELECT * FROM ucla
UNION ALL
SELECT * FROM off_campus;

-- Side-by-side view: one row per layout, cheapest option flagged.
SELECT
    unit_type,
    occupants,
    option,
    ROUND(school_year_monthly)       AS school_year_monthly,
    ROUND(annual_if_away_in_summer)  AS annual_if_away,
    ROUND(annual_with_sublet)        AS annual_with_sublet,
    -- Rank options within the same layout by the annual cost if the student leaves in summer
    RANK() OVER (PARTITION BY unit_type ORDER BY annual_if_away_in_summer) AS rank_annual_if_away,
    RANK() OVER (PARTITION BY unit_type ORDER BY school_year_monthly)      AS rank_monthly
FROM per_person_cost
ORDER BY bedrooms, occupants, unit_type, rank_annual_if_away;
