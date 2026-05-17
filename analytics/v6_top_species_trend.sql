-- VIEW 6: Top commercial species catch trend in EEZ 848
-- Business question: Are the most commercially important species being overfished over time?
-- EEZ 848 = Mexico's Exclusive Economic Zone
-- Table: sau_eez_848_v50_1

CREATE OR REPLACE VIEW fishdb.v6_top_species_trend AS
WITH top_species AS (
    SELECT
        common_name,
        SUM(tonnes) AS total_tonnes
    FROM fishdb.sau_eez_848_v50_1
    GROUP BY common_name
    ORDER BY total_tonnes DESC
    LIMIT 8
)
SELECT
    t.year,
    t.common_name,
    SUM(t.tonnes) AS total_tonnes
FROM fishdb.sau_eez_848_v50_1 t
INNER JOIN top_species s ON t.common_name = s.common_name
GROUP BY t.year, t.common_name
ORDER BY t.year, total_tonnes DESC;
