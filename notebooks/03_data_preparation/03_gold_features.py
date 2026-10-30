# Databricks notebook source
# MAGIC %md
# MAGIC # 3.3 Features Gold — SCANIA Component X (IDA 2024)
# MAGIC
# MAGIC **Objetivo:** Preparar a camada Gold a partir do Silver:
# MAGIC - Agregar leituras operacionais por veículo (último time_step como snapshot de predição)
# MAGIC - Join com especificações do veículo
# MAGIC - Encoding de variáveis categóricas (Spec_*)
# MAGIC - Imputação de missings nas features numéricas (mediana por coluna)
# MAGIC - Escrita em Delta Gold — pronta para modelagem
# MAGIC
# MAGIC **Inputs:** `s3://<S3_BUCKET>/silver/component_x/`
# MAGIC
# MAGIC **Outputs:** `s3://<S3_BUCKET>/gold/features_predictive/` (Delta Lake)

# COMMAND ----------

import pyspark.sql.functions as F
from pyspark.ml import Pipeline
from pyspark.ml.feature import Imputer, StringIndexer

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

SILVER_PREFIX = f"s3://{S3_BUCKET}/silver/component_x"
GOLD_PREFIX = f"s3://{S3_BUCKET}/gold/features_predictive"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Carregamento Silver

# COMMAND ----------

vehicles = spark.read.format("delta").load(f"{SILVER_PREFIX}/vehicles")
readouts = spark.read.format("delta").load(f"{SILVER_PREFIX}/readouts")

print(f"Vehicles: {vehicles.count():,}")
print(f"Readouts: {readouts.count():,}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Snapshot de predição — último time_step por veículo
# MAGIC
# MAGIC Para análise de sobrevivência, o snapshot é gerado NO FINAL da série
# MAGIC disponível por veículo (sem usar informação pós-TTE).

# COMMAND ----------

from pyspark.sql.window import Window

w = Window.partitionBy(VEHICLE_ID_COL).orderBy(F.desc(TIME_STEP_COL))

last_readout = (
    readouts.withColumn("_rank", F.rank().over(w))
    .filter(F.col("_rank") == 1)
    .drop("_rank", TIME_STEP_COL)
)

print(f"Snapshots gerados: {last_readout.count():,} (um por veículo)")

# Verificar que nenhum time_step do snapshot supera o TTE
snapshot_vs_tte = last_readout.join(
    vehicles.select(VEHICLE_ID_COL, TTE_COL), on=VEHICLE_ID_COL
)
print("✓ Snapshot gerado a partir do último time_step observado")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Join snapshot + vehicles (TTE, event, specs)

# COMMAND ----------

gold_base = last_readout.join(vehicles, on=VEHICLE_ID_COL, how="inner")
assert gold_base.count() == vehicles.count(), "Join perdeu veículos"
print(f"✓ Gold base: {gold_base.count():,} veículos com features + TTE + specs")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Encoding de variáveis categóricas (StringIndexer)

# COMMAND ----------

spec_indexed_cols = [f"{c}_idx" for c in SPEC_COLS]
indexers = [
    StringIndexer(inputCol=c, outputCol=f"{c}_idx", handleInvalid="keep")
    for c in SPEC_COLS
]
pipeline = Pipeline(stages=indexers)
gold_encoded = pipeline.fit(gold_base).transform(gold_base).drop(*SPEC_COLS)
print(f"✓ Specs encoded: {spec_indexed_cols}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Imputação de missings (mediana por feature)

# COMMAND ----------

cols_with_missing = [
    c for c in FEATURE_COLS
    if gold_encoded.filter(F.col(c).isNull()).count() > 0
]
print(f"Colunas com missing a imputar: {len(cols_with_missing)}")

if cols_with_missing:
    output_cols = [f"{c}_imputed" for c in cols_with_missing]
    imputer = Imputer(
        inputCols=cols_with_missing,
        outputCols=output_cols,
        strategy="median",
    )
    gold_imputed = imputer.fit(gold_encoded).transform(gold_encoded)
    # Substituir colunas originais pelas imputadas
    for orig, imp in zip(cols_with_missing, output_cols):
        gold_imputed = gold_imputed.drop(orig).withColumnRenamed(imp, orig)
else:
    gold_imputed = gold_encoded

null_after = gold_imputed.select(
    [F.sum(F.col(c).isNull().cast("int")).alias(c) for c in FEATURE_COLS]
).collect()[0]
remaining_nulls = sum(null_after)
print(f"Nulos restantes após imputação: {remaining_nulls}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Seleção das colunas finais e escrita Gold

# COMMAND ----------

final_cols = (
    [VEHICLE_ID_COL, TTE_COL, EVENT_COL]
    + FEATURE_COLS
    + spec_indexed_cols
)
gold_final = gold_imputed.select(final_cols)

gold_final.write.format("delta").mode("overwrite").save(f"{GOLD_PREFIX}/train")
print(f"✓ Gold train escrito: {GOLD_PREFIX}/train")
print(f"  Dimensões: {gold_final.count():,} veículos × {len(gold_final.columns)} colunas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Repetir para validação e teste

# COMMAND ----------

for split in ["validation", "test"]:
    labels_s = spark.read.format("delta").load(f"{SILVER_PREFIX}/{split}/labels")
    readouts_s = spark.read.format("delta").load(f"{SILVER_PREFIX}/{split}/readouts")
    specs_s = spark.read.format("delta").load(f"{SILVER_PREFIX}/{split}/specs")

    # Snapshot: último time_step
    last_r = (
        readouts_s.withColumn("_rank", F.rank().over(
            Window.partitionBy(VEHICLE_ID_COL).orderBy(F.desc(TIME_STEP_COL))
        ))
        .filter(F.col("_rank") == 1)
        .drop("_rank", TIME_STEP_COL)
    )

    base = last_r.join(labels_s, on=VEHICLE_ID_COL).join(specs_s, on=VEHICLE_ID_COL)

    # Encoding
    encoded = pipeline.transform(base).drop(*SPEC_COLS)

    # Imputação (mesmo imputer do treino — aplicar sem re-fit)
    if cols_with_missing:
        encoded = imputer.transform(encoded)
        for orig, imp in zip(cols_with_missing, output_cols):
            encoded = encoded.drop(orig).withColumnRenamed(imp, orig)

    final_split_cols = (
        [VEHICLE_ID_COL, "class_label"]
        + FEATURE_COLS
        + spec_indexed_cols
    )
    gold_split = encoded.select(final_split_cols)
    gold_split.write.format("delta").mode("overwrite").save(f"{GOLD_PREFIX}/{split}")
    print(f"✓ Gold {split}: {gold_split.count():,} veículos")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Resumo

# COMMAND ----------

print("=" * 60)
print("GOLD CONCLUÍDO")
print("=" * 60)
print(f"  {GOLD_PREFIX}/train      — treino para survival/RUL")
print(f"  {GOLD_PREFIX}/validation — validação com class_label")
print(f"  {GOLD_PREFIX}/test       — teste com class_label")
print()
print("Próximo passo: 04_modeling/01_baseline_model.py")
