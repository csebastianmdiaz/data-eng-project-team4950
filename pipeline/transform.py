import boto3
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import io

BUCKET = "data-source-52143"

# esquema objetivo con tipos explícitos
SCHEMA_TIPOS = {
    "area_name":        "string",
    "area_type":        "string",
    "data_layer":       "string",
    "uncertainty_score":"float64",
    "year":             "int64",
    "scientific_name":  "string",
    "common_name":      "string",
    "functional_group": "string",
    "commercial_group": "string",
    "fishing_entity":   "string",
    "fishing_sector":   "string",
    "catch_type":       "string",
    "reporting_status": "string",
    "gear_type":        "string",
    "end_use_type":     "string",
    "tonnes":           "float64",
    "landed_value":     "float64",
}

# Schema PyArrow equivalente para el parquet
PYARROW_SCHEMA = pa.schema([
    ("area_name",         pa.string()),
    ("area_type",         pa.string()),
    ("data_layer",        pa.string()),
    ("uncertainty_score", pa.float64()),
    ("year",              pa.int64()),
    ("scientific_name",   pa.string()),
    ("common_name",       pa.string()),
    ("functional_group",  pa.string()),
    ("commercial_group",  pa.string()),
    ("fishing_entity",    pa.string()),
    ("fishing_sector",    pa.string()),
    ("catch_type",        pa.string()),
    ("reporting_status",  pa.string()),
    ("gear_type",         pa.string()),
    ("end_use_type",      pa.string()),
    ("tonnes",            pa.float64()),
    ("landed_value",      pa.float64()),
])

ARCHIVOS = [
    {"csv": "raw/SAU-GLOBAL-1-v48-0.csv",    "parquet": "processed/SAU-GLOBAL-1-v48-0.parquet",    "renombrar": {}},
    {"csv": "raw/SAU-HighSeas-71-v48-0.csv", "parquet": "processed/SAU-HighSeas-71-v48-0.parquet", "renombrar": {}},
    {"csv": "raw/SAU-EEZ-242-v48-0.csv",     "parquet": "processed/SAU-EEZ-242-v48-0.parquet",     "renombrar": {"fish_name": "common_name", "country": "fishing_entity"}},
    {"csv": "raw/SAU_EEZ_848_v50-1.csv",     "parquet": "processed/SAU_EEZ_848_v50-1.parquet",     "renombrar": {}},
]

s3 = boto3.client("s3")

def castear_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Castea cada columna al tipo objetivo, manejando errores y nulos."""
    for col, tipo in SCHEMA_TIPOS.items():
        if col not in df.columns:
            # agregar columna faltante vacía con el tipo correcto
            if tipo == "string":
                df[col] = pd.array([], dtype="string").dtype.na_value
                df[col] = pd.NA
                df[col] = df[col].astype("string")
            elif tipo == "float64":
                df[col] = pd.array([pd.NA] * len(df), dtype="Float64")
            elif tipo == "int64":
                df[col] = pd.array([pd.NA] * len(df), dtype="Int64")
        else:
            try:
                if tipo == "string":
                    df[col] = df[col].astype(str).replace("nan", pd.NA).astype("string")
                elif tipo == "float64":
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                elif tipo == "int64":
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
            except Exception as e:
                print(f"  ⚠ Error casteando '{col}' a {tipo}: {e}")
    return df

for archivo in ARCHIVOS:
    print(f"Procesando {archivo['csv']}...")

    # leer CSV desde S3
    response = s3.get_object(Bucket=BUCKET, Key=archivo["csv"])
    df = pd.read_csv(io.BytesIO(response["Body"].read()))
    print(f"  Filas: {len(df)} | Columnas originales: {list(df.columns)}")

    # renombrar columnas si aplica
    if archivo["renombrar"]:
        df.rename(columns=archivo["renombrar"], inplace=True)
        print(f"  Columnas renombradas: {archivo['renombrar']}")

    # castear y rellenar columnas al esquema unificado
    df = castear_columnas(df)

    # reordenar columnas
    df = df[list(SCHEMA_TIPOS.keys())]

    # verificación rápida
    print("  Tipos resultantes:")
    for col in df.columns:
        print(f"    {col}: {df[col].dtype}")

    # convertir a PyArrow con schema explícito y subir
    tabla = pa.Table.from_pandas(df, schema=PYARROW_SCHEMA)
    buffer = io.BytesIO()
    pq.write_table(tabla, buffer)
    buffer.seek(0)
    s3.upload_fileobj(buffer, BUCKET, archivo["parquet"])
    print(f"  ✓ Subido a s3://{BUCKET}/{archivo['parquet']}\n")

print("Transformación completa.")