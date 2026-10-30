# Databricks notebook source
# MAGIC %md
# MAGIC # 2.2 Qualidade dos Dados — SCANIA Component X (IDA 2024)
# MAGIC
# MAGIC **Objetivo:** Executar verificações de qualidade nos dados brutos.
# MAGIC Qualquer anomalia deve ser reportada antes de avançar para a Fase 3.
# MAGIC
# MAGIC **Inputs:**
# MAGIC - `s3://<S3_BUCKET>/raw/scania_component_x/` (todos os arquivos)
# MAGIC
# MAGIC **Outputs:** Relatório de qualidade — duplicatas, consistência temporal,
# MAGIC ranges de valores, join keys, schema match.

# COMMAND ----------

import pyspark.sql.functions as F
from pyspark.sql.window import Window

from src.scania_poc.schema import (
    EVENT_COL,
    FEATURE_COLS,
    SPEC_COLS,
    TTE_COL,
    TIME_STEP_COL,
    VEHICLE_ID_COL,
)
from src.scania_poc.validators import missing_rate, validate_event_col

dbutils.widgets.text("S3_BUCKET", "", "S3 Bucket name")
S3_BUCKET = dbutils.widgets.get("S3_BUCKET")
assert S3_BUCKET, "Defina o widget S3_BUCKET antes de executar este notebook"

RAW_PREFIX = f"s3://{S3_BUCKET}/raw/scania_component_x"

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Carregamento

# COMMAND ----------

tte = spark.read.csv(f"{RAW_PREFIX}/train_tte.csv", header=True, inferSchema=True)
specs = spark.read.csv(f"{RAW_PREFIX}/train_specifications.csv", header=True, inferSchema=True)
readouts = spark.read.csv(f"{RAW_PREFIX}/train_operational_readouts.csv", header=True, inferSchema=True)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Verificação de schema

# COMMAND ----------

# Colunas esperadas
expected_tte_cols = {VEHICLE_ID_COL, TTE_COL, EVENT_COL}
expected_readouts_cols = {VEHICLE_ID_COL, TIME_STEP_COL} | set(FEATURE_COLS)
expected_specs_cols = {VEHICLE_ID_COL} | set(SPEC_COLS)

assert set(tte.columns) == expected_tte_cols, f"Schema tte inesperado: {set(tte.columns) ^ expected_tte_cols}"
assert set(readouts.columns) == expected_readouts_cols, (
    f"Schema readouts inesperado: {set(readouts.columns) ^ expected_readouts_cols}"
)
assert set(specs.columns) == expected_specs_cols, (
    f"Schema specs inesperado: {set(specs.columns) ^ expected_specs_cols}"
)
print("✓ Schemas consistentes com src/scania_poc/schema.py")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Duplicatas

# COMMAND ----------

# train_tte: vehicle_id deve ser chave primária
dup_tte = tte.groupBy(VEHICLE_ID_COL).count().filter(F.col("count") > 1).count()
assert dup_tte == 0, f"Duplicatas em train_tte: {dup_tte} vehicle_ids repetidos"
print("✓ train_tte: sem vehicle_ids duplicados")

# train_operational_readouts: (vehicle_id, time_step) deve ser único
dup_readouts = (
    readouts.groupBy(VEHICLE_ID_COL, TIME_STEP_COL)
    .count()
    .filter(F.col("count") > 1)
    .count()
)
assert dup_readouts == 0, f"Duplicatas em readouts: {dup_readouts} pares (vehicle_id, time_step) repetidos"
print("✓ train_operational_readouts: sem (vehicle_id, time_step) duplicados")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Validação da coluna de evento

# COMMAND ----------

event_values = {r[EVENT_COL] for r in tte.select(EVENT_COL).distinct().collect()}
assert validate_event_col(event_values), f"Valores inesperados em {EVENT_COL}: {event_values}"
print(f"✓ {EVENT_COL} contém apenas {{0, 1}}")

# TTE deve ser positivo
neg_tte = tte.filter(F.col(TTE_COL) <= 0).count()
assert neg_tte == 0, f"TTE com valores <= 0: {neg_tte} registros"
print(f"✓ {TTE_COL} sempre positivo")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Consistência temporal

# COMMAND ----------

# time_step deve ser >= 0
neg_ts = readouts.filter(F.col(TIME_STEP_COL) < 0).count()
assert neg_ts == 0, f"time_step negativo: {neg_ts} registros"
print("✓ time_step sempre não-negativo")

# time_step máximo por veículo não deve exceder seu TTE
readouts_max_ts = readouts.groupBy(VEHICLE_ID_COL).agg(F.max(TIME_STEP_COL).alias("max_ts"))
tte_duration = tte.select(VEHICLE_ID_COL, TTE_COL)
ts_vs_tte = readouts_max_ts.join(tte_duration, VEHICLE_ID_COL).filter(
    F.col("max_ts") > F.col(TTE_COL)
)
n_violations = ts_vs_tte.count()
if n_violations > 0:
    print(f"⚠ {n_violations} veículos com max(time_step) > TTE (possível vazamento de dados)")
    ts_vs_tte.show(10)
else:
    print("✓ max(time_step) <= TTE para todos os veículos")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 6. Verificação de missings nas features operacionais

# COMMAND ----------

n_total = readouts.count()
null_agg = readouts.select(
    [F.sum(F.col(c).isNull().cast("int")).alias(c) for c in FEATURE_COLS]
).collect()[0]

high_miss = [(c, null_agg[c]) for c in FEATURE_COLS if null_agg[c] > 0]
high_miss.sort(key=lambda x: -x[1])

print(f"Colunas com missing: {len(high_miss)}/{len(FEATURE_COLS)}")
for col, cnt in high_miss[:15]:
    rate = missing_rate(cnt, n_total)
    print(f"  {col:<15}: {cnt:>8,} ({rate:.3%})")

# Verificar que nenhuma coluna tem > 10% de missing (threshold conservador)
max_missing_threshold = 0.10
violations = [(c, n) for c, n in high_miss if missing_rate(n, n_total) > max_missing_threshold]
if violations:
    print(f"⚠ Colunas com > {max_missing_threshold:.0%} de missing: {violations}")
else:
    print(f"✓ Nenhuma coluna com > {max_missing_threshold:.0%} de missing")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 7. Padrão de ausência em bloco (grupos 291 e 459)

# COMMAND ----------

# Verificar se as colunas do grupo 291 faltam sempre juntas
group_291_cols = [c for c in FEATURE_COLS if c.startswith("291_")]
group_291_null_any = readouts.filter(F.col(group_291_cols[0]).isNull())
group_291_null_count = group_291_null_any.count()

group_291_all_null = group_291_null_any.filter(
    F.expr(" AND ".join([f"{c} IS NULL" for c in group_291_cols]))
).count()

print(f"Grupo 291: {group_291_null_count:,} linhas com 291_0 nulo")
print(f"  Dessas, {group_291_all_null:,} com TODAS as colunas nulas ({group_291_all_null/group_291_null_count:.1%})")
if group_291_all_null == group_291_null_count:
    print("  ✓ Ausência em bloco confirmada para o grupo 291")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 8. Especificações — valores inesperados

# COMMAND ----------

for col in SPEC_COLS:
    null_count = specs.filter(F.col(col).isNull()).count()
    if null_count > 0:
        print(f"⚠ {col}: {null_count} valores nulos")

print("✓ Verificação de especificações concluída")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 9. Resumo de qualidade

# COMMAND ----------

print("=" * 50)
print("RESUMO DE QUALIDADE")
print("=" * 50)
print(f"train_tte       : {tte.count():>10,} linhas — OK")
print(f"train_specs     : {specs.count():>10,} linhas — OK")
print(f"train_readouts  : {readouts.count():>10,} linhas — ver missings acima")
print()
print("Próximo passo: criar config/data_contract.yaml (Fase 3)")
