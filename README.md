# 🐟 Sea Around Us (SAU) - Data Engineering Capstone

## Project Overview
This project is an end-to-end serverless Data Lake built on AWS. It processes over 500,000 global fisheries records (1950-2018) to analyze the human impact on marine ecosystems. The pipeline automatically ingests fragmented CSVs, standardizes schemas, applies strict data quality rules, and partitions the data for high-performance, cost-effective SQL querying.

## Architecture
**Storage:** Amazon S3 (Medallion Architecture: `Raw` -> `Processed` -> `Curated`).
**Compute & ETL:** AWS Glue (Python Shell).
**Data Cataloging:** AWS Glue Crawler & Data Catalog.
**Orchestration:** AWS Step Functions (Fully automated DAG).
**Analytics:** Amazon Athena (Serverless SQL) & Amazon QuickSight (BI Dashboard).

## How to Run the Pipeline
The entire workflow is 100% automated with zero manual step-by-step intervention.
1. Navigate to **AWS Step Functions** in the AWS Console.
2. Select the State Machine named `Data-Pipeline-Team4950`.
3. Click **Start Execution**.
4. The orchestrator will sequentially trigger: Transformation -> Data Quality -> Partitioning -> Crawler.

## Team 4950 Members & Roles
**Role 1 (Data Engineer):** Jessica Abril Quintero Castillo - Ingestion & Schema Transformation.
**Role 2 (Data Quality):** Gael Loreto Miranda - Row-level filtering & Validation Rules.
**Role 3 (Analytics):** Alejandro Costich Sandoval - Hive Partitioning & QuickSight Dashboards.
**Role 4 (Orchestration):** César Sebastián Mercado Díaz - Step Functions, Architecture & Security.