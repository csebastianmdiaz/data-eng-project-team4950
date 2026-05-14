import boto3
import urllib.request
import os

BUCKET = "data-source-52143"

s3 = boto3.client("s3")

ARCHIVOS_WEB = {
    "SAU-GLOBAL-1-v48-0.csv": "https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACDENG-1-91570/lab-capstone/s3/SAU-GLOBAL-1-v48-0.csv",
    "SAU-HighSeas-71-v48-0.csv": "https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACDENG-1-91570/lab-capstone/s3/SAU-HighSeas-71-v48-0.csv",
    "SAU-EEZ-242-v48-0.csv": "https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACDENG-1-91570/lab-capstone/s3/SAU-EEZ-242-v48-0.csv",
}

for nombre, url in ARCHIVOS_WEB.items():
    destino = f"raw/{nombre}"
    print(f"Descargando {nombre} → s3://{BUCKET}/{destino} ...")
    with urllib.request.urlopen(url) as response:
        s3.upload_fileobj(response, BUCKET, destino)
    print(f"Listo")

ARCHIVOS_LOCAL = {
    "datasets/SAU EEZ 848 v50-1.csv": "raw/SAU_EEZ_848_v50-1.csv",
}

for ruta_local, destino in ARCHIVOS_LOCAL.items():
    print(f"Subiendo {ruta_local} → s3://{BUCKET}/{destino} ...")
    with open(ruta_local, "rb") as f:
        s3.upload_fileobj(f, BUCKET, destino)
    print(f"Listo")

print("\nIngesta completa.")