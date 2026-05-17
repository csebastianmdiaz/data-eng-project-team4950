-- VIEW 4: High seas vs EEZ catch comparison by year
-- Business question: Is fishing pressure shifting from coastal EEZ waters to the high seas?
-- Combines SAU-HighSeas-71 and SAU-EEZ-242 datasets
-- Tables: sau_highseas_71_v48_0, sau_eez_242_v48_0

CREATE OR REPLACE VIEW fishdb.v4_highseas_vs_eez AS
SELECT
    year,
    'High Seas'  AS zone,
    SUM(tonnes)  AS total_tonnes
FROM fishdb.sau_highseas_71_v48_0
GROUP BY year

UNION ALL

SELECT
    year,
    'EEZ (242)'  AS zone,
    SUM(tonnes)  AS total_tonnes
FROM fishdb.sau_eez_242_v48_0
GROUP BY year

ORDER BY year, zone;
