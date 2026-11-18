-- 08. Recommendation table: for each layout × summer plan, is the cheapest option the same
--     under all three rent estimates? If yes, the recommendation is robust.

WITH winners AS (
    SELECT unit_type, summer_plan, rent_method, option
    FROM sensitivity
    WHERE cost_rank = 1
),
summary AS (
    SELECT
        unit_type,
        summer_plan,
        COUNT(DISTINCT option)                                  AS n_distinct_winners,
        MODE(option)                                            AS most_common_winner,   -- most frequent value
        STRING_AGG(rent_method || '=' || option, ', ' ORDER BY rent_method) AS detail
    FROM winners
    GROUP BY unit_type, summer_plan
)
SELECT
    unit_type,
    summer_plan,
    CASE
        WHEN n_distinct_winners = 1 THEN most_common_winner || ' (robust)'
        ELSE most_common_winner || ' (depends on rent estimate)'
    END AS recommendation,
    detail
FROM summary
ORDER BY unit_type,
         -- custom sort order for summer plans (not alphabetical)
         CASE summer_plan WHEN 'away' THEN 1 WHEN 'sublet_50' THEN 2 WHEN 'sublet_70' THEN 3
                          WHEN 'sublet_90' THEN 4 ELSE 5 END;
