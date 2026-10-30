# Databricks notebook source
# MAGIC %md
# MAGIC # 3.2 Transformação Silver — SCANIA Component X (IDA 2024)
# MAGIC
# MAGIC **Objetivo:** Transformar os dados Raw em Silver:
# MAGIC - Casting correto de tipos (float para features, int para IDs/flags)
# MAGIC - Missings já são nulos reais (NaN) — sem conversão de sentinel necessária
# MAGIC - Join entre os três arquivos de treino por vehicle_id
# MAGIC - Quality gate antes da escrita
# MAGIC - Escrita em Delta Lake particionada
# MAGIC
# MAGIC **Inputs:** `s3://<S3_BUCKET>/raw/scania_component_x/`
# MAGIC
# MAGIC **Outputs:** `s3://<S3_BUCKET>/silver/component_x/` (Delta Lake)

# COMMAND ----------

import pyspark.sql.functions as F
from pyspark.sql.types import DoubleType, FloatType, IntegerType, StringType

from src.scania_poc.quality import QualityGateError, run_quality_gate
from src.scania_poc.schema import (
    EVENT_COL,
    FEATURE_COLS,
    SPEC_COLS,
    TTE_COL,
    TIME_STEP_COL,
    VEHICLE_ID_COL,
)

dbutils.widgets.text("S3_BUCKET", "", "S3 Bucket name")
S3_BUCKET = dbutils.widgets.get("S3_BUCKET")
assert S3_BUCKET, "Defina o widget S3_BUCKET"

RAW_PREFIX = f"s3://{S3_BUCKET}/raw/scania_component_x"
SILVER_PREFIX = f"s3://{S3_BUCKET}/silver/component_x"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Carregamento dos arquivos Raw

# COMMAND ----------

tte_raw = spark.read.csv(f"{RAW_PREFIX}/train_tte.csv", header=True, inferSchema=True)
specs_raw = spark.read.csv(f"{RAW_PREFIX}/train_specifications.csv", header=True, inferSchema=True)
readouts_raw = spark.read.csv(
    f"{RAW_PREFIX}/train_operational_readouts.csv", header=True, inferSchema=True
)

print(f"TTE: {tte_raw.count():,} linhas")
print(f"Specs: {specs_raw.count():,} linhas")
print(f"Readouts: {readouts_raw.count():,} linhas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Quality gate nos dados Raw

# COMMAND ----------

for df, key in [(tte_raw, "train_tte"), (specs_raw, "train_specifications")]:
    violations = run_quality_gate(df, key, raise_on_failure=False)
    if violations:
        print(f"⚠ {key}: {violations}")
    else:
        print(f"✓ {key}: quality gate OK")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Casting e limpeza — train_tte

# COMMAND ----------

tte_silver = tte_raw.select(
    F.col(VEHICLE_ID_COL).cast(IntegerType()),
    F.col(TTE_COL).cast(DoubleType()),
    F.col(EVENT_COL).cast(IntegerType()),
)

# Verificação: sem nulos após cast
assert tte_silver.filter(F.col(VEHICLE_ID_COL).isNull()).count() == 0
assert tte_silver.filter(F.col(TTE_COL).isNull()).count() == 0
assert tte_silver.filter(F.col(EVENT_COL).isNull()).count() == 0
print("✓ TTE silver: sem nulos")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Casting e limpeza — train_specifications

# COMMAND ----------

specs_silver = specs_raw.select(
    F.col(VEHICLE_ID_COL).cast(IntegerType()),
    *[F.col(c).cast(StringType()) for c in SPEC_COLS],
)
print("✓ Specifications silver: OK")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Casting e limpeza — train_operational_readouts

# COMMAND ----------

readouts_silver = readouts_raw.select(
    F.col(VEHICLE_ID_COL).cast(IntegerType()),
    F.col(TIME_STEP_COL).cast(DoubleType()),
    *[F.col(c).cast(DoubleType()) for c in FEATURE_COLS],
)

null_check = readouts_silver.filter(
    F.col(VEHICLE_ID_COL).isNull() | F.col(TIME_STEP_COL).isNull()
).count()
assert null_check == 0, f"Nulos em colunas de identidade após cast: {null_check}"
print(f"✓ Readouts silver: {readouts_silver.count():,} linhas, sem nulos em vehicle_id/time_step")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Join: TTE + Specs (tabela de veículos silver)

# COMMAND ----------

vehicle_silver = tte_silver.join(specs_silver, on=VEHICLE_ID_COL, how="inner")
assert vehicle_silver.count() == tte_silver.count(), "Join perdeu veículos"
print(f"✓ Vehicle silver (TTE + Specs): {vehicle_silver.count():,} veículos")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Escrita em Delta Lake

# COMMAND ----------

vehicle_silver.write.format("delta").mode("overwrite").save(f"{SILVER_PREFIX}/vehicles")
print(f"✓ Escrito: {SILVER_PREFIX}/vehicles")

readouts_silver.write.format("delta").mode("overwrite").partitionBy(
    VEHICLE_ID_COL
).save(f"{SILVER_PREFIX}/readouts")
print(f"✓ Escrito: {SILVER_PREFIX}/readouts (particionado por vehicle_id)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Processar validação e teste

# COMMAND ----------

for split in ["validation", "test"]:
    labels_raw = spark.read.csv(
        f"{RAW_PREFIX}/{split}_labels.csv", header=True, inferSchema=True
    )
    specs_split = spark.read.csv(
        f"{RAW_PREFIX}/{split}_specifications.csv", header=True, inferSchema=True
    )
    readouts_split = spark.read.csv(
        f"{RAW_PREFIX}/{split}_operational_readouts.csv", header=True, inferSchema=True
    )

    labels_silver = labels_split = labels_raw.select(
        F.col(VEHICLE_ID_COL).cast(IntegerType()),
        F.col("class_label").cast(IntegerType()),
    )
    readouts_split_silver = readouts_split.select(
        F.col(VEHICLE_ID_COL).cast(IntegerType()),
        F.col(TIME_STEP_COL).cast(DoubleType()),
        *[F.col(c).cast(DoubleType()) for c in FEATURE_COLS],
    )
    specs_split_silver = specs_split.select(
        F.col(VEHICLE_ID_COL).cast(IntegerType()),
        *[F.col(c).cast(StringType()) for c in SPEC_COLS],
    )

    labels_silver.write.format("delta").mode("overwrite").save(
        f"{SILVER_PREFIX}/{split}/labels"
    )
    readouts_split_silver.write.format("delta").mode("overwrite").partitionBy(
        VEHICLE_ID_COL
    ).save(f"{SILVER_PREFIX}/{split}/readouts")
    specs_split_silver.write.format("delta").mode("overwrite").save(
        f"{SILVER_PREFIX}/{split}/specs"
    )
    print(f"✓ {split}: labels + readouts + specs escritos em Silver")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Resumo

# COMMAND ----------

print("=" * 60)
print("SILVER CONCLUÍDO")
print("=" * 60)
print(f"  {SILVER_PREFIX}/vehicles      — TTE + specs de treino")
print(f"  {SILVER_PREFIX}/readouts      — leituras de treino (Delta particionado)")
print(f"  {SILVER_PREFIX}/validation/   — labels + readouts + specs de validação")
print(f"  {SILVER_PREFIX}/test/         — labels + readouts + specs de teste")
print()
print("Próximo passo: 03_gold_features.py")
