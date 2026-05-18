-- VIEW 1: Global catch trend over time
-- Business question: How has total global fish catch evolved from 1950 to 2018?
-- Table: sau_global_1_v48_0 (SAU-GLOBAL-1, all fishing entities worldwide)

CREATE OR REPLACE VIEW fishdb.v1_global_catch_trend AS
SELECT
    year,
    SUM(tonnes)                                         AS total_tonnes,
    SUM(landed_value)                                   AS total_landed_value,
    ROUND(SUM(landed_value) / NULLIF(SUM(tonnes), 0), 2) AS avg_value_per_tonne
FROM fishdb.sau_global_1_v48_0
GROUP BY year
ORDER BY year;
