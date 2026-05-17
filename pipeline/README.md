
# Data Engineer (Role 1)
- **Name:** Jessica Abril Quintero Castillo

---

# Pipeline — Data Engineer (Role 1)

## Overview
This folder contains the scripts responsible for the ingestion, transformation, and cataloging stages of the data pipeline. These scripts move data from its original CSV format into an optimized Parquet format stored in a structured S3 Data Lake, and register the schema in the AWS Glue Data Catalog.

---

## Pipeline Flow

```
[Sea Around Us URLs]         [Local file]
        |                        |
        v                        v
   ingest.py  ───────────────────────────→  s3://data-source-52143/raw/
                                                        |
                                                        v
                                              transform.py
                                                        |
                                                        v
                                      s3://data-source-52143/processed/
                                                        |
                                                        v
                                             validates data  (Role 2)
                                                        |
                                                        v
                                       s3://data-source-52143/curated/
                                                        |
                                                        v
                                             setup_crawler.py
                                                        |
                                                        v
                                           AWS Glue Data Catalog
                                                (fishdb)
```

---

## S3 Data Lake Structure

```
s3://data-source-52143/
├── raw/          ← original csv files
├── processed/    ← cleaned parquet files
└── curated/      ← Partitioned Parquet files (Role 3)
```

---

## Datasets

| File | Description | Schema changes |
|---|---|---|
| `SAU-GLOBAL-1-v48-0.csv` | Global high seas catch data (1950–2018) | None |
| `SAU-HighSeas-71-v48-0.csv` | Pacific Western Central high seas area | None |
| `SAU-EEZ-242-v48-0.csv` | Fiji Exclusive Economic Zone | `fish_name` → `common_name`, `country` → `fishing_entity` |
| `SAU_EEZ_848_v50-1.csv` | USA West Coast Exclusive Economic Zone | None |

---

## Scripts

### `ingest.py`
Creates a buckets named `data-source-52143` if it does not already exist.

Downloads the three official capstone csv files directly from the AWS source URLs and uploads them to the `raw/` zone in S3. 

The fourth dataset (`SAU_EEZ_848_v50-1.csv`) is uploaded from a local file since it is not available via a public URL. The file is located in datasets/SAU_EEZ_848_v50-1.csv.

No data is modified at this stage.

**Run:**
```bash
python pipeline/ingest.py
```

---

### `transform.py`
Reads each CSV from the `raw/` zone in S3, applies schema alignment where needed, converts to parquet format, and uploads the result to the `processed/` zone.

**Schema alignment applied:**
- `SAU-EEZ-242-v48-0.csv`: `fish_name` renamed to `common_name`, `country` renamed to `fishing_entity` to match the other datasets.
- All other files: no changes needed.

**Why Parquet?**

I used parquet because it has a columnar format. Athena only reads the columns needed by each query. Also, it provides fast queries.

Parquet, while compressed, is significantly smaller than csv.


**Run:**
```bash
python pipeline/transform.py
```

---

### `setup_crawler.py`
Creates the `fishdb` Glue database and `fishcrawler` crawler if they do not already exist, then runs the crawler against the `curated/` zone created by Role 2 and waits for it to complete. Prints the list of tables created in the Glue Data Catalog.

**Run:**
```bash
python pipeline/setup_crawler.py
```

---

## Technical Decisions

| Decision | Justification |
|---|---|
| Separate `raw/`, `processed/`, and `curated/` zones | Preserves original data for auditing; processed zone contains clean queryable data; curated zone contains partitioned data optimized for Athena |
| Parquet over CSV | Columnar storage reduces bytes scanned in Athena queries; enables compression |
| Schema alignment at transform stage | Ensures consistent column names across all four sources before cataloging |
| Crawler points to `curated/` | Data is clean, aligned, and partitioned at this point; enables Athena to leverage partitions for faster and cheaper queries |
| Fourth dataset (EEZ-848 USA West Coast) | Adds geographic diversity; introduces additional columns (`scientific_name`, `gear_type`, `functional_group`) that enrich analytics queries |

---

## How to Reproduce

### Prerequisites
- Python 3.8+
- AWS CLI configured with valid credentials
- Required libraries:

```bash
pip install boto3 pandas pyarrow
```

### Steps

```bash
# 1. Ingest raw data into S3
python pipeline/ingest.py

# 2. Transform CSV to Parquet and align schemas
python pipeline/transform.py

# 3. (Role 2) creates curated/ zone
python pipeline/partition.py

# 4. Create Glue database, crawler, and run it against curated/
python pipeline/setup_crawler.py
```

After these steps, the `fishdb` database in AWS Glue will contain four tables corresponding to the four datasets, partitioned by year and ready to be queried with Athena.
