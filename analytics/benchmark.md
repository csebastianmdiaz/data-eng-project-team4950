# Benchmark: CSV without partitioning vs Parquet with partitioning

## Methodology

Three identical business queries were executed twice each:
1. Against the **raw CSV files** in `s3://data-source-52143/raw/` (no partitioning, no columnar format)
2. Against the **curated Parquet files** in `s3://data-source-52143/curated/` (partitioned by `year`, Snappy-compressed Parquet)

Execution time and bytes scanned were recorded from the Athena query execution details panel.
Estimated cost calculated at **$5.00 per TB scanned** (AWS Athena standard pricing, us-east-1).

---

## Queries benchmarked

### Q1 — Total catch for a single year
```sql
-- CSV version (raw)
SELECT SUM(tonnes) FROM fishdb.sau_global_1_raw WHERE year = 2010;

-- Parquet + partition version (curated)
SELECT SUM(tonnes) FROM fishdb.sau_global_1_v48_0 WHERE year = 2010;
```

### Q2 — Top 5 fishing entities in a decade
```sql
-- CSV version (raw)
SELECT fishing_entity, SUM(tonnes) AS total
FROM fishdb.sau_global_1_raw
WHERE year BETWEEN 2000 AND 2010
GROUP BY fishing_entity
ORDER BY total DESC
LIMIT 5;

-- Parquet + partition version (curated)
SELECT fishing_entity, SUM(tonnes) AS total
FROM fishdb.sau_global_1_v48_0
WHERE year BETWEEN 2000 AND 2010
GROUP BY fishing_entity
ORDER BY total DESC
LIMIT 5;
```

### Q3 — Reported vs unreported catch for a specific year
```sql
-- CSV version (raw)
SELECT reporting_status, SUM(tonnes)
FROM fishdb.sau_global_1_raw
WHERE year = 1990
GROUP BY reporting_status;

-- Parquet + partition version (curated)
SELECT reporting_status, SUM(tonnes)
FROM fishdb.sau_global_1_v48_0
WHERE year = 1990
GROUP BY reporting_status;
```

---

## Results

| Query | Format / Partition        | Time (s) | Bytes scanned | Estimated cost |
|-------|---------------------------|----------|---------------|----------------|
| Q1    | CSV / No partition        | _._      | _ MB          | $_.____        |
| Q1    | Parquet / year=2010       | _._      | _ MB          | $_.____        |
| Q2    | CSV / No partition        | _._      | _ MB          | $_.____        |
| Q2    | Parquet / year 2000-2010  | _._      | _ MB          | $_.____        |
| Q3    | CSV / No partition        | _._      | _ MB          | $_.____        |
| Q3    | Parquet / year=1990       | _._      | _ MB          | $_.____        |

> Fill in the values from Athena's query execution details after running each query.
> In Athena: after each query runs, click **"Execution details"** → copy "Data scanned" and "Execution time".

---

## How to calculate estimated cost

```
cost = (bytes_scanned / 1,099,511,627,776) * 5.00
     = (bytes_scanned / 1TB_in_bytes) * $5.00
```

---

## Analysis

*(Fill in after running the benchmark)*

Expected findings:
- **Parquet** should scan 10–20x fewer bytes than CSV for the same query, because it is columnar (only reads the columns needed) and Snappy-compressed.
- **Partitioning by year** adds an additional filter pushdown: Athena skips all partitions not matching the `WHERE year = ...` clause entirely.
- Together, Parquet + partitioning typically reduces scanned data by **85–95%** vs raw CSV.
- Cost savings follow proportionally: a query that costs $0.025 on CSV may cost $0.001 on partitioned Parquet.
