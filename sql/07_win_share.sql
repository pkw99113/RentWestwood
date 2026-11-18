-- 07. Across all 8 layouts × 15 scenarios, how often does each option come out cheapest,
--     and how big is the gap to the runner-up (is it a clear win or a near tie)?

WITH ranked AS (
    SELECT *,
           -- LEAD on the cost-ordered rows gives the next-cheapest option's cost in the same scenario
           LEAD(annual_cost) OVER (PARTITION BY unit_type, rent_method, summer_plan ORDER BY annual_cost) AS runner_up_cost
    FROM sensitivity
)
SELECT
    summer_plan,
    option                                                     AS winner,
    COUNT(*)                                                   AS scenarios_won,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY summer_plan), 0) AS share_pct,
    ROUND(MEDIAN(runner_up_cost - annual_cost))                AS median_margin_usd
FROM ranked
WHERE cost_rank = 1
GROUP BY summer_plan, option
ORDER BY summer_plan, scenarios_won DESC;
