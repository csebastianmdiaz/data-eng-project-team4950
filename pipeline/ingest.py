import boto3
import urllib.request

BUCKET = "data-source-52143"

ARCHIVOS = {
    "SAU-GLOBAL-1-v48-0.csv": "https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACDENG-1-91570/lab-capstone/s3/SAU-GLOBAL-1-v48-0.csv",
    "SAU-HighSeas-71-v48-0.csv": "https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACDENG-1-91570/lab-capstone/s3/SAU-HighSeas-71-v48-0.csv",
    "SAU-EEZ-242-v48-0.csv": "https://aws-tc-largeobjects.s3.us-west-2.amazonaws.com/CUR-TF-200-ACDENG-1-91570/lab-capstone/s3/SAU-EEZ-242-v48-0.csv",
}

s3 = boto3.client("s3")

for nombre, url in ARCHIVOS.items():
    destino = f"raw/{nombre}"
    print(f"Descargando {nombre} en s3://{BUCKET}/{destino} ...")
    with urllib.request.urlopen(url) as response:
        s3.upload_fileobj(response, BUCKET, destino)
    print(f"Completado: s3://{BUCKET}/{destino}")

print("\nIngesta completa. Archivos en s3://{BUCKET}/raw/")