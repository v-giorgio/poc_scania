# Databricks notebook source
# MAGIC %md
# MAGIC # 3.1 Ingestão do volume gerenciado → Bronze Delta
# MAGIC
# MAGIC Os oito CSVs oficiais devem estar em `RAW_VOLUME_PATH`. O notebook calcula
# MAGIC SHA-256 por arquivo, lê direto do volume e substitui a tabela Bronze em
# MAGIC reexecuções. O diretório Raw deve permanecer somente leitura após o upload.

# COMMAND ----------

from pathlib import Path

from src.scania_poc.config import (
    build_volume_raw_path,
    select_raw_files,
    validate_data_schema,
    validate_raw_volume_path,
)
from src.scania_poc.ingestion import ingest_volume_csv_to_bronze

dbutils.widgets.text("RAW_VOLUME_PATH", "", "Volume Raw terminando em /raw")
dbutils.widgets.text("DATA_SCHEMA", "", "Schema UC para tabelas gerenciadas")
dbutils.widgets.text("SOURCE_FILE", "", "Opcional: um CSV oficial para smoke test")
RAW_VOLUME_PATH = validate_raw_volume_path(
    dbutils.widgets.get("RAW_VOLUME_PATH").strip()
)
DATA_SCHEMA = validate_data_schema(dbutils.widgets.get("DATA_SCHEMA").strip())
SOURCE_FILES = select_raw_files(dbutils.widgets.get("SOURCE_FILE").strip())

# A identidade configurada no workspace precisa ter USE CATALOG/SCHEMA e
# CREATE TABLE no schema de destino.
spark.sql(f"DESCRIBE SCHEMA {DATA_SCHEMA}").collect()
missing_files = [
    filename
    for filename in SOURCE_FILES
    if not Path(build_volume_raw_path(RAW_VOLUME_PATH, filename)).is_file()
]
if missing_files:
    raise FileNotFoundError(f"Arquivos oficiais ausentes no volume Raw: {missing_files}")

# COMMAND ----------

results = {}
for filename in SOURCE_FILES:
    rows, table, sha256 = ingest_volume_csv_to_bronze(
        spark, RAW_VOLUME_PATH, filename, DATA_SCHEMA
    )
    results[filename] = {"rows": rows, "table": table, "sha256": sha256}
    print(f"{filename}: {rows:,} linhas → {table}; sha256={sha256}")

print("Ingestão concluída. Os CSVs Raw no volume não foram alterados.")
