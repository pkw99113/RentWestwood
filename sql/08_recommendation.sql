-- 08. Recommendation table for the most common layout (2BR shared by 4):
--     for each summer plan × commute profile × value of time, is the cheapest option the same
--     under all three rent estimates? If yes, the recommendation is robust.

WITH winners AS (
    SELECT summer_plan, car_profile, time_value, rent_method, option
    FROM sensitivity
    WHERE cost_rank = 1 AND unit_type = '2/4 apartment'
)
SELECT
    car_profile,
    time_value,
    summer_plan,
    CASE WHEN COUNT(DISTINCT option) = 1 THEN MODE(option) || ' (robust)'
         ELSE MODE(option) || ' (depends on rent estimate)' END                   AS recommendation,
    STRING_AGG(rent_method || '=' || option, ', ' ORDER BY rent_method)           AS detail
FROM winners
GROUP BY car_profile, time_value, summer_plan
ORDER BY
    CASE car_profile WHEN 'transit' THEN 1 WHEN 'drives_owned' THEN 2 ELSE 3 END,
    time_value,
    CASE summer_plan WHEN 'away' THEN 1 WHEN 'sublet_50' THEN 2 WHEN 'sublet_70' THEN 3
                     WHEN 'sublet_90' THEN 4 ELSE 5 END;
