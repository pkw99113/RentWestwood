-- 03. Estimated market rent for each ZIP × bedroom count.
--
-- Problem: SAFMR has bedroom detail but barely separates nearby ZIPs (e.g. 90024 vs 90025: $3,450 vs $3,440).
--          ZORI shows clear gaps between ZIPs but has no bedroom detail.
-- Approach: take each ZIP's level from ZORI and the shape across bedroom counts from SAFMR.
--   estimated rent(zip, bd) = latest ZORI(zip) × SAFMR(zip, bd) / SAFMR(zip, 1BR)
-- Assumption: ZORI ≈ a typical 1-bedroom rent. Across the validation ZIPs the median
-- ZORI / SAFMR-1BR ratio is about 1.0 (see docs/02_data_quality_report.md).

CREATE OR REPLACE TABLE market_rent AS
WITH latest_zori AS (
    SELECT zip, zori
    FROM zori
    -- QUALIFY filters on a window function result: keep each ZIP's most recent month only
    QUALIFY ROW_NUMBER() OVER (PARTITION BY zip ORDER BY month DESC) = 1
),
bedroom_ratio AS (
    SELECT
        zip, area, distance_group, bedrooms, safmr,
        -- each bedroom's SAFMR ÷ the same ZIP's 1BR SAFMR (window without GROUP BY keeps every row)
        safmr / MAX(CASE WHEN bedrooms = 1 THEN safmr END) OVER (PARTITION BY zip) AS ratio_to_1br
    FROM safmr
)
SELECT
    b.zip, b.area, b.distance_group, b.bedrooms, b.safmr,
    ROUND(b.ratio_to_1br, 3)         AS ratio_to_1br,
    ROUND(z.zori * b.ratio_to_1br)   AS est_market_rent
FROM bedroom_ratio b
JOIN latest_zori z USING (zip)
WHERE b.bedrooms <= 3
ORDER BY b.bedrooms, est_market_rent DESC;

SELECT * FROM market_rent;
