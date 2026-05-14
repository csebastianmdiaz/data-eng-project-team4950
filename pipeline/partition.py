import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import io
import os

BUCKET = "data-source-52143"

ARCHIVOS = [
    "processed/SAU-GLOBAL-1-v48-0.parquet",
    "processed/SAU-HighSeas-71-v48-0.parquet",
    "processed/SAU-EEZ-242-v48-0.parquet",
    "processed/SAU_EEZ_848_v50-1.parquet",
]

s3 = boto3.client("s3")

for key in ARCHIVOS:
    nombre = key.split("/")[-1].replace(".parquet", "")
    print(f"Particionando {nombre}...")

    # leer parquet desde S3
    response = s3.get_object(Bucket=BUCKET, Key=key)
    df = pd.read_parquet(io.BytesIO(response["Body"].read()))

    # particionar por year y subir cada partición a curated/
    for year, grupo in df.groupby("year"):
        destino = f"curated/{nombre}/year={year}/data.parquet"

        buffer = io.BytesIO()
        grupo.to_parquet(buffer, index=False)
        buffer.seek(0)

        s3.upload_fileobj(buffer, BUCKET, destino)

    years = sorted(df["year"].unique())
    print(f"{len(years)} particiones ({years[0]}-{years[-1]})")

print("\nParticionamiento completado")
print(f"Revisa: s3://{BUCKET}/curated/")