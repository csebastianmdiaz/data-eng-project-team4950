# Architecture Decision Records (ADRs)

This document justifies the key technical decisions made throughout the pipeline development.

## Data Engineering (Role 1)
| Decision | Justification |
| :--- | :--- |
| **Zone Separation in S3** | Separating the bucket into `raw/`, `processed/`, and `curated/` preserves original files untouched. If failures occur, we can reprocess from `raw/`. Only validated data reaches `curated/` for Athena. |
| **CSV to Parquet Conversion** | Parquet is a columnar format. Athena only reads needed columns, reducing bytes scanned and costs. It also features built-in compression and preserves data types. |
| **Schema Harmonization** | Renamed mismatched columns (e.g., `fish_name` to `common_name` in Fiji) and injected missing columns with nulls to ensure all datasets share a strict 17-column schema for Glue Catalog compatibility. |

## Data Quality (Role 2)
| Decision | Justification |
| :--- | :--- |
| **Row-level filtering** | Instead of rejecting an entire file for a few errors (e.g., EEZ-848 had 2.1% invalid rows), the script dynamically drops bad rows and saves the good ones, preserving 97.9% of valid data. |
| **Pandas Asserts over External Libs** | Standard Pandas with documented assertions was chosen over Pandera/Great Expectations for lower overhead while maintaining the same technical depth and generating an automated HTML report. |

## Orchestration & Security (Role 4)
| Decision | Justification |
| :--- | :--- |
| **AWS Step Functions over Glue Workflows** | Step Functions provides visual debugging, explicit state transitions, native error catching (`Catch` block to `Pipeline_Failure`), and true Serverless orchestration compared to traditional Glue Workflows. |
| **In-place Partitioning** | The partition script reads from `curated/` and writes the partitioned folders back to `curated/`, deleting the flat files. This avoids creating a 4th S3 zone, saving storage costs. |