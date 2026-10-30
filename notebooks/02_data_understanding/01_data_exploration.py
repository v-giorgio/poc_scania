# Databricks notebook source
# MAGIC %md
# MAGIC # 2.1 Exploração dos Dados — SCANIA Component X (IDA 2024)
# MAGIC
# MAGIC **Objetivo:** Inspecionar os arquivos brutos do S3, calcular estatísticas reais
# MAGIC e confirmar hipóteses de schema antes de qualquer transformação.
# MAGIC
# MAGIC **Inputs:**
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/train_tte.csv`
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/train_operational_readouts.csv`
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/train_specifications.csv`
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/validation_labels.csv`
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/test_labels.csv`
# MAGIC
# MAGIC **Outputs:** Perfil estatístico, distribuição de eventos/censuras, análise de missings.
# MAGIC Resultados devem alimentar `docs/data-discovery.md` e `docs/data-dictionary.md`.

# COMMAND ----------

import pyspark.sql.functions as F
from pyspark.sql.types import DoubleType

# Configuração — lida de secret/widget, nunca hardcode de bucket ou credenciais
dbutils.widgets.text("S3_BUCKET", "", "S3 Bucket name")
S3_BUCKET = dbutils.widgets.get("S3_BUCKET")
assert S3_BUCKET, "Defina o widget S3_BUCKET antes de executar este notebook"

RAW_PREFIX = f"s3://{S3_BUCKET}/raw/scania_component_x"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Carregamento dos arquivos brutos

# COMMAND ----------

tte = spark.read.csv(f"{RAW_PREFIX}/train_tte.csv", header=True, inferSchema=True)
specs = spark.read.csv(f"{RAW_PREFIX}/train_specifications.csv", header=True, inferSchema=True)
readouts = spark.read.csv(f"{RAW_PREFIX}/train_operational_readouts.csv", header=True, inferSchema=True)
val_labels = spark.read.csv(f"{RAW_PREFIX}/validation_labels.csv", header=True, inferSchema=True)
test_labels = spark.read.csv(f"{RAW_PREFIX}/test_labels.csv", header=True, inferSchema=True)

print("Arquivos carregados com sucesso")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Dimensões

# COMMAND ----------

for name, df in [
    ("train_tte", tte),
    ("train_specifications", specs),
    ("train_operational_readouts", readouts),
    ("validation_labels", val_labels),
    ("test_labels", test_labels),
]:
    print(f"{name}: {df.count():,} linhas × {len(df.columns)} colunas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Distribuição de eventos e censuras (train_tte)

# COMMAND ----------

print("=== Distribuição in_study_repair ===")
tte.groupBy("in_study_repair").count().orderBy("in_study_repair").show()

print("=== Estatísticas de TTE (length_of_study_time_step) ===")
tte.select(
    F.min("length_of_study_time_step").alias("min"),
    F.expr("percentile(length_of_study_time_step, 0.25)").alias("p25"),
    F.median("length_of_study_time_step").alias("median"),
    F.expr("percentile(length_of_study_time_step, 0.75)").alias("p75"),
    F.max("length_of_study_time_step").alias("max"),
).show()

print("=== TTE apenas eventos ===")
tte.filter(F.col("in_study_repair") == 1).select(
    F.min("length_of_study_time_step").alias("min"),
    F.median("length_of_study_time_step").alias("median"),
    F.max("length_of_study_time_step").alias("max"),
).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Estrutura temporal das leituras operacionais

# COMMAND ----------

print("=== Leituras por veículo ===")
per_vehicle = readouts.groupBy("vehicle_id").agg(
    F.count("*").alias("n_readouts"),
    F.min("time_step").alias("t_min"),
    F.max("time_step").alias("t_max"),
)
per_vehicle.select(
    F.min("n_readouts").alias("readouts_min"),
    F.expr("percentile(n_readouts, 0.5)").alias("readouts_median"),
    F.max("n_readouts").alias("readouts_max"),
    F.min("t_min").alias("ts_global_min"),
    F.max("t_max").alias("ts_global_max"),
).show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Taxa de valores ausentes por coluna (features operacionais)

# COMMAND ----------

n_rows = readouts.count()
feature_cols = [c for c in readouts.columns if c not in ("vehicle_id", "time_step")]

null_rates = readouts.select(
    [F.sum(F.col(c).isNull().cast("int")).alias(c) for c in feature_cols]
).collect()[0]

missing_report = sorted(
    [(col, null_rates[col], round(null_rates[col] / n_rows * 100, 3)) for col in feature_cols],
    key=lambda x: -x[1],
)

print(f"{'Coluna':<15} {'Nulos':>10} {'%':>8}")
print("-" * 36)
for col, cnt, pct in missing_report[:30]:
    if cnt > 0:
        print(f"{col:<15} {cnt:>10,} {pct:>7.3f}%")

cols_with_missing = sum(1 for _, c, _ in missing_report if c > 0)
print(f"\nTotal com missings: {cols_with_missing}/{len(feature_cols)} colunas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Distribuição das classes ordinais (validação e teste)

# COMMAND ----------

print("=== Validação — class_label ===")
val_labels.groupBy("class_label").count().orderBy("class_label").show()

print("=== Teste — class_label ===")
test_labels.groupBy("class_label").count().orderBy("class_label").show()

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Especificações — cardinalidade das colunas categóricas

# COMMAND ----------

spec_cols = [c for c in specs.columns if c != "vehicle_id"]
for col in spec_cols:
    n_unique = specs.select(col).distinct().count()
    print(f"{col}: {n_unique} categorias únicas")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Verificação: join keys entre arquivos

# COMMAND ----------

train_ids_tte = set(r.vehicle_id for r in tte.select("vehicle_id").collect())
train_ids_specs = set(r.vehicle_id for r in specs.select("vehicle_id").collect())
train_ids_readouts = set(r.vehicle_id for r in readouts.select("vehicle_id").distinct().collect())

assert train_ids_tte == train_ids_specs, "Mismatch: tte vs specs"
assert train_ids_tte == train_ids_readouts, "Mismatch: tte vs readouts"
print(f"✓ Join keys consistentes: {len(train_ids_tte):,} veículos em todos os arquivos de treino")

# Verificar que treino, validação e teste não se sobrepõem
val_ids = set(r.vehicle_id for r in val_labels.select("vehicle_id").collect())
test_ids = set(r.vehicle_id for r in test_labels.select("vehicle_id").collect())

from src.scania_poc.discovery import find_vehicles_in_multiple_splits
overlaps = find_vehicles_in_multiple_splits(list(train_ids_tte), list(val_ids), list(test_ids))
assert all(v == 0 for v in overlaps.values()), f"Sobreposição entre splits: {overlaps}"
print(f"✓ Nenhuma sobreposição entre train/val/test")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Amostra dos dados para inspeção visual

# COMMAND ----------

print("=== train_tte (5 linhas) ===")
display(tte.limit(5))

print("=== train_operational_readouts (5 linhas) ===")
display(readouts.limit(5))

print("=== train_specifications (5 linhas) ===")
display(specs.limit(5))
