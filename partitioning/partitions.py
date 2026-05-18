"""
partitions_local.py - Costich
Versión local (sin dependencias de AWS Glue).
Lee los parquets de curated (validados por Rol 2), agrega particiones por year,
y sobreescribe en curated zone con estructura compatible con Athena.
"""

import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import io

# ── Configuración ─────────────────────────────────────────────────────────────
BUCKET         = "data-source-52143"
CURATED_PREFIX = "curated/"

PARTITION_COL = "year"

# ── Cliente S3 ────────────────────────────────────────────────────────────────
s3 = boto3.client("s3", region_name="us-east-1")


def discover_files(bucket: str, prefix: str) -> list:
    """Descubre dinámicamente los .parquet planos disponibles en curated/."""
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/")

    files = []
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".parquet"):
                filename = key.replace(prefix, "")
                files.append(filename)

    print(f"  [DISCOVER] {len(files)} archivos encontrados en curated/: {files}")
    return files


def read_parquet_from_s3(bucket: str, key: str) -> pd.DataFrame:
    print(f"  [READ] s3://{bucket}/{key}")
    response = s3.get_object(Bucket=bucket, Key=key)
    buffer = io.BytesIO(response["Body"].read())
    return pd.read_parquet(buffer)


def write_partitioned_to_s3(df: pd.DataFrame, bucket: str, prefix: str, source_name: str):
    years = df[PARTITION_COL].unique()
    print(f"  [WRITE] {len(years)} particiones para '{source_name}'")

    for year in sorted(years):
        partition_df = df[df[PARTITION_COL] == year].reset_index(drop=True)

        # ✅ Eliminar columna 'year' del archivo — ya está en el path de partición
        partition_df = partition_df.drop(columns=[PARTITION_COL])

        table  = pa.Table.from_pandas(partition_df, preserve_index=False)
        buffer = io.BytesIO()
        pq.write_table(table, buffer, compression="snappy")
        buffer.seek(0)

        key = f"{prefix}{source_name}/year={year}/data.parquet"
        s3.put_object(Bucket=bucket, Key=key, Body=buffer.getvalue())
        print(f"    -> s3://{bucket}/{key}  ({len(partition_df):,} rows)")


def delete_existing_curated(bucket: str, prefix: str, source_name: str):
    full_prefix = f"{prefix}{source_name}/"
    paginator   = s3.get_paginator("list_objects_v2")
    pages       = paginator.paginate(Bucket=bucket, Prefix=full_prefix)

    keys_to_delete = []
    for page in pages:
        for obj in page.get("Contents", []):
            keys_to_delete.append({"Key": obj["Key"]})

    if keys_to_delete:
        print(f"  [DELETE] Eliminando {len(keys_to_delete)} objetos anteriores en '{source_name}'")
        s3.delete_objects(Bucket=bucket, Delete={"Objects": keys_to_delete})


def process_file(filename: str):
    source_name = filename.replace(".parquet", "")
    print(f"\n{'='*60}")
    print(f"Procesando: {filename}")
    print(f"{'='*60}")

    # 1. Leer de curated/ (validados por Rol 2)
    df = read_parquet_from_s3(BUCKET, f"{CURATED_PREFIX}{filename}")
    print(f"  [INFO] {len(df):,} filas | columnas: {list(df.columns)}")

    if PARTITION_COL not in df.columns:
        print(f"  [ERROR] Columna '{PARTITION_COL}' no encontrada. Saltando archivo.")
        return

    # 2. Eliminar archivo plano de Rol 2
    print(f"  [DELETE] Eliminando archivo plano: {CURATED_PREFIX}{filename}")
    s3.delete_object(Bucket=BUCKET, Key=f"{CURATED_PREFIX}{filename}")

    # 3. Limpiar particiones anteriores
    delete_existing_curated(BUCKET, CURATED_PREFIX, source_name)

    # 4. Escribir particionado (sin columna year dentro del archivo)
    write_partitioned_to_s3(df, BUCKET, CURATED_PREFIX, source_name)

    print(f"  [OK] {filename} procesado correctamente.")


def main():
    print("=" * 60)
    print("PARTITIONS_LOCAL.PY — Costich")
    print(f"Bucket : {BUCKET}")
    print(f"Input  : s3://{BUCKET}/{CURATED_PREFIX}<archivo>.parquet")
    print(f"Output : s3://{BUCKET}/{CURATED_PREFIX}<dataset>/year=YYYY/data.parquet")
    print(f"Partición por: {PARTITION_COL}")
    print("=" * 60)

    files = discover_files(BUCKET, CURATED_PREFIX)

    if not files:
        print("  [WARN] No se encontraron archivos .parquet planos en curated/. Nada que procesar.")
        return

    for filename in files:
        process_file(filename)

    print("\nTodos los archivos procesados. Curated zone lista.")
    print(f"   Estructura: s3://{BUCKET}/{CURATED_PREFIX}<dataset>/year=YYYY/data.parquet")


if __name__ == "__main__":
    main()