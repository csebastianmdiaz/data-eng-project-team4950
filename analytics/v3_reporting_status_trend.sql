-- VIEW 3: Reported vs unreported catch over time
-- Business question: What proportion of global catch goes unreported each year?
-- Unreported catch = illegal, unregulated, or undeclared fishing (IUU)
-- Table: sau_global_1_v48_0

CREATE OR REPLACE VIEW fishdb.v3_reporting_status_trend AS
SELECT
    year,
    reporting_status,
    SUM(tonnes)                                                        AS total_tonnes,
    ROUND(SUM(tonnes) * 100.0 / SUM(SUM(tonnes)) OVER (PARTITION BY year), 2) AS pct_of_year_catch
FROM fishdb.sau_global_1_v48_0
GROUP BY year, reporting_status
ORDER BY year, reporting_status;
