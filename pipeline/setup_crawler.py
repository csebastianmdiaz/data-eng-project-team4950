import boto3
import time

BUCKET      = "data-source-52143"
DATABASE    = "fishdb"
CRAWLER     = "fishcrawler"
IAM_ROLE    = "arn:aws:iam::891943683988:role/LabRole"

SOURCES = [
    f"s3://{BUCKET}/curated/SAU-GLOBAL-1-v48-0/",
    f"s3://{BUCKET}/curated/SAU-HighSeas-71-v48-0/",
    f"s3://{BUCKET}/curated/SAU-EEZ-242-v48-0/",
    f"s3://{BUCKET}/curated/SAU_EEZ_848_v50-1/",
]

glue = boto3.client("glue", region_name="us-east-1")

# crea la bd si no existe
try:
    glue.get_database(Name=DATABASE)
    print(f"Base de datos '{DATABASE}' ya existe")
except glue.exceptions.EntityNotFoundException:
    glue.create_database(DatabaseInput={"Name": DATABASE})
    print(f"Base de datos '{DATABASE}' creada")

# crea crawler si no existe, apuntando a las fuentes procesadas
try:
    glue.get_crawler(Name=CRAWLER)
    print(f"Crawler '{CRAWLER}' ya existe")
except glue.exceptions.EntityNotFoundException:
    glue.create_crawler(
        Name=CRAWLER,
        Role=IAM_ROLE,
        DatabaseName=DATABASE,
        Targets={
            "S3Targets": [{"Path": path} for path in SOURCES]
        },
        RecrawlPolicy={"RecrawlBehavior": "CRAWL_EVERYTHING"},
        SchemaChangePolicy={
            "UpdateBehavior": "UPDATE_IN_DATABASE",
            "DeleteBehavior": "LOG",
        },
    )
    print(f"Crawler '{CRAWLER}' creado")

# ejecuta crawler
state = glue.get_crawler(Name=CRAWLER)["Crawler"]["State"]
if state == "RUNNING":
    print("El crawler ya está corriendo, esperando...")
else:
    glue.start_crawler(Name=CRAWLER)
    print(f"Crawler iniciado...")

# esperar a que termine
while True:
    state = glue.get_crawler(Name=CRAWLER)["Crawler"]["State"]
    print(f"  Estado: {state}")
    if state == "READY":
        break
    time.sleep(15)

# verificar tablas creadas
tablas = glue.get_tables(DatabaseName=DATABASE)["TableList"]
print(f"\nTablas en '{DATABASE}':")
for t in tablas:
    print(f"  - {t['Name']}")

print("\nCrawler completado.")