# Databricks notebook source
# MAGIC %md
# MAGIC # 2.1 Discovery — SCANIA Component X (IDA 2024)
# MAGIC
# MAGIC Recalcula agregados e valida chaves a partir das tabelas Bronze. Não exibe
# MAGIC registros brutos nem carrega rótulos de teste, que não existem no pacote oficial.

# COMMAND ----------

import pyspark.sql.functions as F
from pyspark.sql.types import DoubleType, IntegerType

from src.scania_poc.discovery import (
    describe_class_distribution,
    describe_event_distribution,
    describe_readouts_structure,
    find_vehicles_in_multiple_splits,
)
from src.scania_poc.config import qualified_table_name, validate_data_schema
from src.scania_poc.schema import EVENT_COL, TTE_COL, VEHICLE_ID_COL

dbutils.widgets.text("DATA_SCHEMA", "", "Schema UC das tabelas Bronze")
DATA_SCHEMA = validate_data_schema(dbutils.widgets.get("DATA_SCHEMA").strip())


def load_bronze(name):
    return spark.read.table(qualified_table_name(DATA_SCHEMA, "bronze", name))


files = {
    name: load_bronze(name)
    for name in [
        "train_tte",
        "train_specifications",
        "train_operational_readouts",
        "validation_labels",
        "validation_specifications",
        "validation_operational_readouts",
        "test_specifications",
        "test_operational_readouts",
    ]
}
for name, frame in files.items():
    source_columns = [col for col in frame.columns if not col.startswith("_")]
    print(f"{name}: {frame.count():,} linhas × {len(source_columns)} colunas")
    print(f"  schema: {[(field.name, field.dataType.simpleString()) for field in frame.schema.fields if not field.name.startswith('_')]}")

# COMMAND ----------

tte = files["train_tte"].select(
    F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
    F.col(TTE_COL).cast(DoubleType()).alias(TTE_COL),
    F.col(EVENT_COL).cast(IntegerType()).alias(EVENT_COL),
)
readouts_source = files["train_operational_readouts"]
readouts = readouts_source.select(
    F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
    F.col("time_step").cast(DoubleType()).alias("time_step"),
    *[
        F.when(
            F.isnan(F.col(col).cast(DoubleType())), F.lit(None).cast(DoubleType())
        ).otherwise(F.col(col).cast(DoubleType())).alias(col)
        for col in readouts_source.columns
        if not col.startswith("_") and col not in (VEHICLE_ID_COL, "time_step")
    ],
)
validation_labels = files["validation_labels"].select(
    F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
    F.col("class_label").cast(IntegerType()).alias("class_label"),
)
print("Eventos/censuras e TTE:", describe_event_distribution(tte, EVENT_COL, TTE_COL))
print(
    "Estrutura temporal treino:",
    describe_readouts_structure(readouts, VEHICLE_ID_COL, "time_step"),
)
print(
    "Distribuição dos rótulos oficiais de validação:",
    describe_class_distribution(validation_labels, "class_label"),
)

feature_cols = [c for c in readouts.columns if not c.startswith("_") and c not in (VEHICLE_ID_COL, "time_step")]
num_rows = readouts.count()
missing = readouts.select(
    [F.sum(F.col(col).isNull().cast("long")).alias(col) for col in feature_cols]
).first()
missing_rates = {col: float(missing[col] / num_rows) for col in feature_cols}
print(f"Features com valores ausentes: {sum(rate > 0 for rate in missing_rates.values())}/{len(feature_cols)}")
print(f"Taxa máxima de missing por feature: {max(missing_rates.values(), default=0.0):.4%}")

# COMMAND ----------

train_ids = [row[VEHICLE_ID_COL] for row in tte.select(VEHICLE_ID_COL).collect()]
validation_ids = [
    row[VEHICLE_ID_COL]
    for row in files["validation_specifications"]
    .select(F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL))
    .collect()
]
test_ids = [
    row[VEHICLE_ID_COL]
    for row in files["test_specifications"]
    .select(F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL))
    .collect()
]
overlaps = find_vehicles_in_multiple_splits(train_ids, validation_ids, test_ids)
if any(overlaps.values()):
    raise ValueError(f"Sobreposição de vehicle_id entre conjuntos: {overlaps}")
print(f"Sem sobreposição de veículos entre train/validation/test: {overlaps}")

# Nenhum registro, segredo ou rótulo de teste é escrito pelo relatório de discovery.
