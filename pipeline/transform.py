import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import io

BUCKET = "data-source-52143"

ARCHIVOS = [
    {"csv": "raw/SAU-GLOBAL-1-v48-0.csv",    "parquet": "processed/SAU-GLOBAL-1-v48-0.parquet",    "renombrar": {}},
    {"csv": "raw/SAU-HighSeas-71-v48-0.csv", "parquet": "processed/SAU-HighSeas-71-v48-0.parquet", "renombrar": {}},
    {"csv": "raw/SAU-EEZ-242-v48-0.csv",     "parquet": "processed/SAU-EEZ-242-v48-0.parquet",     "renombrar": {"fish_name": "common_name", "country": "fishing_entity"}},
    {"csv": "raw/SAU_EEZ_848_v50-1.csv",     "parquet": "processed/SAU_EEZ_848_v50-1.parquet",     "renombrar": {}}, 
]

s3 = boto3.client("s3")

for archivo in ARCHIVOS:
    print(f"Procesando {archivo['csv']}...")

    # leer csv desde S3
    response = s3.get_object(Bucket=BUCKET, Key=archivo["csv"])
    df = pd.read_csv(io.BytesIO(response["Body"].read()))
    print(f"  Filas: {len(df)} | Columnas: {list(df.columns)}")

    # renombrar columnas si aplica (solo EEZ)
    if archivo["renombrar"]:
        df.rename(columns=archivo["renombrar"], inplace=True)
        print(f"Columnas renombradas: {archivo['renombrar']}")

    # Convertir a parquet y subir a S3
    buffer = io.BytesIO()
    df.to_parquet(buffer, index=False)
    buffer.seek(0)
    s3.upload_fileobj(buffer, BUCKET, archivo["parquet"])
    print(f"Subido a s3://{BUCKET}/{archivo['parquet']}\n")

print("Transformación completa.")