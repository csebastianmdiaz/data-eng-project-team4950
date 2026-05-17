-- VIEW 5: Most efficient fishing gear types by value per tonne
-- Business question: Which fishing gear generates the most economic value per tonne caught?
-- Helps identify high-value vs high-volume fishing methods
-- Table: sau_global_1_v48_0

CREATE OR REPLACE VIEW fishdb.v5_gear_efficiency AS
SELECT
    gear_type,
    SUM(tonnes)                                              AS total_tonnes,
    SUM(landed_value)                                        AS total_landed_value,
    ROUND(SUM(landed_value) / NULLIF(SUM(tonnes), 0), 2)    AS value_per_tonne,
    ROUND(SUM(tonnes) * 100.0 / SUM(SUM(tonnes)) OVER (), 2) AS pct_of_total_catch
FROM fishdb.sau_global_1_v48_0
GROUP BY gear_type
ORDER BY value_per_tonne DESC;
