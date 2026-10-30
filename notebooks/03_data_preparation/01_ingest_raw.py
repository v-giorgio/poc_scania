# Databricks notebook source
# MAGIC %md
# MAGIC # 3.1 Ingestão Raw — SCANIA Component X (IDA 2024)
# MAGIC
# MAGIC **Objetivo:** Copiar os arquivos CSV originais para a camada Raw do S3
# MAGIC sem nenhuma modificação. A camada Raw é imutável e serve como fonte
# MAGIC de verdade para todas as transformações posteriores.
# MAGIC
# MAGIC **Inputs:** CSVs do dataset SCANIA Component X (fonte original)
# MAGIC
# MAGIC **Outputs:**
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/train_tte.csv`
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/train_operational_readouts.csv`
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/train_specifications.csv`
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/validation_labels.csv`
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/validation_operational_readouts.csv`
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/validation_specifications.csv`
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/test_labels.csv`
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/test_operational_readouts.csv`
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/test_specifications.csv`

# COMMAND ----------

dbutils.widgets.text("S3_BUCKET", "", "S3 Bucket name")
dbutils.widgets.text("SOURCE_PATH", "", "Caminho de origem dos CSVs (local ou S3)")

S3_BUCKET = dbutils.widgets.get("S3_BUCKET")
SOURCE_PATH = dbutils.widgets.get("SOURCE_PATH")

assert S3_BUCKET, "Defina o widget S3_BUCKET"
assert SOURCE_PATH, "Defina o widget SOURCE_PATH com o caminho dos CSVs originais"

RAW_PREFIX = f"s3://{S3_BUCKET}/raw/scania_component_x"

FILES = [
    "train_tte.csv",
    "train_operational_readouts.csv",
    "train_specifications.csv",
    "validation_labels.csv",
    "validation_operational_readouts.csv",
    "validation_specifications.csv",
    "test_labels.csv",
    "test_operational_readouts.csv",
    "test_specifications.csv",
]

# COMMAND ----------

# MAGIC %md
# MAGIC ## Ingestão dos arquivos

# COMMAND ----------

from src.scania_poc.ingestion import ingest_csv_to_raw

results = {}
for fname in FILES:
    source = f"{SOURCE_PATH}/{fname}"
    dest = f"{RAW_PREFIX}/{fname}"
    n_rows = ingest_csv_to_raw(spark, source, dest)
    results[fname] = n_rows
    print(f"✓ {fname}: {n_rows:,} linhas → {dest}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verificação pós-ingestão

# COMMAND ----------

from src.scania_poc.ingestion import verify_raw_file_exists

print("Verificando existência dos arquivos no S3 Raw:")
for fname in FILES:
    path = f"{RAW_PREFIX}/{fname}"
    exists = verify_raw_file_exists(spark, path)
    status = "✓" if exists else "✗ FALHOU"
    print(f"  {status} {path}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Resumo

# COMMAND ----------

print("=" * 60)
print("INGESTÃO RAW CONCLUÍDA")
print("=" * 60)
for fname, n in results.items():
    print(f"  {fname:<45} {n:>10,} linhas")
print()
print(f"Destino: s3://{S3_BUCKET}/raw/scania_component_x/")
print("Próximo passo: 02_silver_transform.py")
