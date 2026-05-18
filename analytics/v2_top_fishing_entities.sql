-- VIEW 2: Top 10 fishing entities by total catch
-- Business question: Which countries have caught the most fish historically?
-- Table: sau_global_1_v48_0

CREATE OR REPLACE VIEW fishdb.v2_top_fishing_entities AS
SELECT
    fishing_entity,
    SUM(tonnes)                                              AS total_tonnes,
    SUM(landed_value)                                        AS total_landed_value,
    ROUND(SUM(tonnes) * 100.0 / SUM(SUM(tonnes)) OVER (), 2) AS pct_of_global_catch
FROM fishdb.sau_global_1_v48_0
GROUP BY fishing_entity
ORDER BY total_tonnes DESC
LIMIT 10;
