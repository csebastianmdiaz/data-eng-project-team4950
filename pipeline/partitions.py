"""
partitions.py - Costich
Pipeline step 7 & 8: Lee los parquets de processed, agrega particiones por year,
y sobreescribe en curated zone con estructura compatible con Athena.
"""

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import io
import os

# ── Configuración ─────────────────────────────────────────────────────────────
BUCKET          = "data-source-52143"
PROCESSED_PREFIX = "processed/"
CURATED_PREFIX   = "curated/"

# Archivos a procesar
FILES = [
    "SAU-EEZ-242-v48-0.parquet",
    "SAU-GLOBAL-1-v48-0.parquet",
    "SAU-HighSeas-71-v48-0.parquet",
    "SAU_EEZ_848_v50-1.parquet",
]

# Columna de partición
PARTITION_COL = "year"

# ── Cliente S3 ────────────────────────────────────────────────────────────────
s3 = boto3.client("s3", region_name="us-east-1")


def read_parquet_from_s3(bucket: str, key: str) -> pd.DataFrame:
    """Descarga un parquet de S3 y lo retorna como DataFrame."""
    print(f"  [READ] s3://{bucket}/{key}")
    response = s3.get_object(Bucket=bucket, Key=key)
    buffer = io.BytesIO(response["Body"].read())
    return pd.read_parquet(buffer)


def write_partitioned_to_s3(df: pd.DataFrame, bucket: str, prefix: str, source_name: str):
    """
    Escribe el DataFrame particionado por year en S3.
    Estructura resultante:
      curated/<source_name>/year=1950/data.parquet
      curated/<source_name>/year=1951/data.parquet
      ...
    """
    years = df[PARTITION_COL].unique()
    print(f"  [WRITE] {len(years)} particiones para '{source_name}'")

    for year in sorted(years):
        partition_df = df[df[PARTITION_COL] == year].reset_index(drop=True)

        # Convertir a parquet en memoria
        table = pa.Table.from_pandas(partition_df, preserve_index=False)
        buffer = io.BytesIO()
        pq.write_table(table, buffer, compression="snappy")
        buffer.seek(0)

        # Key destino en S3
        key = f"{prefix}{source_name}/year={year}/data.parquet"
        s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())
        print(f"    -> s3://{bucket}/{key}  ({len(partition_df):,} rows)")


def delete_existing_curated(bucket: str, prefix: str, source_name: str):
    """Elimina las particiones anteriores para sobreescribir limpio."""
    full_prefix = f"{prefix}{source_name}/"
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix=full_prefix)

    keys_to_delete = []
    for page in pages:
        for obj in page.get("Contents", []):
            keys_to_delete.append({"Key": obj["Key"]})

    if keys_to_delete:
        print(f"  [DELETE] Eliminando {len(keys_to_delete)} objetos anteriores en '{source_name}'")
        s3.delete_objects(Bucket=bucket, Delete={"Objects": keys_to_delete})


def process_file(filename: str):
    """Proceso completo para un archivo: read → partition → write."""
    source_name = filename.replace(".parquet", "")
    print(f"\n{'='*60}")
    print(f"Procesando: {filename}")
    print(f"{'='*60}")

    # 1. Leer de processed
    df = read_parquet_from_s3(BUCKET, f"{PROCESSED_PREFIX}{filename}")
    print(f"  [INFO] {len(df):,} filas | columnas: {list(df.columns)}")

    # 2. Validar que exista la columna de partición
    if PARTITION_COL not in df.columns:
        print(f"  [ERROR] Columna '{PARTITION_COL}' no encontrada. Saltando archivo.")
        return

    # 3. Limpiar curated anterior (sobreescritura limpia)
    delete_existing_curated(BUCKET, CURATED_PREFIX, source_name)

    # 4. Escribir particionado en curated
    write_partitioned_to_s3(df, BUCKET, CURATED_PREFIX, source_name)

    print(f"  [OK] {filename} procesado correctamente.")


def main():
    print("=" * 60)
    print("PARTITIONS.PY — Costich")
    print(f"Bucket  : {BUCKET}")
    print(f"Source  : s3://{BUCKET}/{PROCESSED_PREFIX}")
    print(f"Destino : s3://{BUCKET}/{CURATED_PREFIX}")
    print(f"Partición por: {PARTITION_COL}")
    print("=" * 60)

    for filename in FILES:
        process_file(filename)

    print("\nTodos los archivos procesados. Curated zone lista.")
    print(f"   Estructura: s3://{BUCKET}/{CURATED_PREFIX}<dataset>/year=YYYY/data.parquet")


if __name__ == "__main__":
    main()