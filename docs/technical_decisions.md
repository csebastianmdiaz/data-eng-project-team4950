Decision: Convert all source CSV files to Apache Parquet format before storing them in the processed/ zone.
Reasons: Parquet is a columnar format: Athena only reads the columns a query needs, not the entire file. This directly reduces bytes scanned and cost. Parquet files are much smaller than csv due to built-in compression. Also, parquet preserves data types, which avoids type inference issues when querying with Athena.

Decision: Separate the S3 bucket into three zones: raw/, processed/, and curated/.
Reasons: raw/ preserves the original source files untouched. If something goes wrong at any stage, we can always reprocess from the original data. Then, processed/ holds the cleaned and schema-aligned parquet files. Finally, curated/ holds only data that has passed quality validations and partitioning. This is the trusted zone that feeds Athena and QuickSight.

Decision: Rename mismatched columns in SAU-EEZ-242 during the transform step, before uploading to processed/.
Reasons: The EEZ-242 (Fiji) file uses fish_name and country instead of common_name and fishing_entity used by the other datasets. Fixing this at the transform stage ensures all four datasets share the same schema in processed/ and Glue can catalog them consistently.

Decision: Add missing columns as null values with the correct data types to datasets that don't have them, so all four files share the same 17-column schema.
Reasons: GLOBAL only has 9 columns; HighSeas has 15. Without alignment, Glue would catalog them with different schemas and cross-dataset queries would fail or return incorrect results.