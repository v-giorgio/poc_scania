# Databricks notebook source
# MAGIC %md
# MAGIC # 3.2 Validação e transformação das tabelas Bronze → Silver
# MAGIC
# MAGIC Lê somente Delta Bronze, conserva a linhagem da origem e interrompe a
# MAGIC execução em falhas de contrato ou joins que alterem a cardinalidade.
# MAGIC Nenhuma tabela é particionada por `vehicle_id`.

# COMMAND ----------

import pyspark.sql.functions as F
from pyspark.sql.types import DoubleType, IntegerType, StringType

from src.scania_poc.contracts import validate_contract
from src.scania_poc.config import qualified_table_name, validate_data_schema
from src.scania_poc.schema import (
    EVENT_COL,
    FEATURE_COLS,
    SPEC_COLS,
    TTE_COL,
    TIME_STEP_COL,
    VEHICLE_ID_COL,
)

dbutils.widgets.text("DATA_SCHEMA", "", "Schema UC das tabelas gerenciadas")
DATA_SCHEMA = validate_data_schema(dbutils.widgets.get("DATA_SCHEMA").strip())


def load_bronze(name):
    return spark.read.table(qualified_table_name(DATA_SCHEMA, "bronze", name))


def write_silver(frame, name):
    table = qualified_table_name(DATA_SCHEMA, "silver", name)
    (
        frame.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table)
    )


def enforce_contract(df, key):
    violations = validate_contract(df, key)
    if violations:
        raise ValueError(f"Contrato {key} falhou: {violations}")


def assert_same_ids(left, right, key, name):
    left_ids = left.select(key).distinct()
    right_ids = right.select(key).distinct()
    left_only = left_ids.join(right_ids, on=key, how="left_anti").limit(1).count()
    right_only = right_ids.join(left_ids, on=key, how="left_anti").limit(1).count()
    if left_only or right_only:
        raise ValueError(f"IDs divergentes em {name}: left_only={left_only}, right_only={right_only}")


def check_join(left, right, key, name):
    if left.groupBy(key).count().filter(F.col("count") > 1).limit(1).count():
        raise ValueError(f"Chave duplicada no lado esquerdo do join {name}")
    if right.groupBy(key).count().filter(F.col("count") > 1).limit(1).count():
        raise ValueError(f"Chave duplicada no lado direito do join {name}")
    assert_same_ids(left, right, key, name)
    joined = left.join(right, on=key, how="inner")
    if joined.count() != left.count() or joined.count() != right.count():
        raise ValueError(f"Join {name} perdeu ou multiplicou veículos")
    return joined


def cast_readouts(df):
    cast_features = [
        F.when(
            F.isnan(F.col(c).cast(DoubleType())),
            F.lit(None).cast(DoubleType()),
        )
        .otherwise(F.col(c).cast(DoubleType()))
        .alias(c)
        for c in FEATURE_COLS
    ]
    typed = df.select(
        F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
        F.col(TIME_STEP_COL).cast(DoubleType()).alias(TIME_STEP_COL),
        *cast_features,
        F.col("_source_uri"),
        F.col("_source_version"),
        F.col("_ingested_at"),
    )
    if typed.filter(F.col(VEHICLE_ID_COL).isNull() | F.col(TIME_STEP_COL).isNull()).limit(1).count():
        raise ValueError("Falha de parsing em vehicle_id/time_step")
    return typed


# COMMAND ----------

tte_raw = load_bronze("train_tte")
specs_raw = load_bronze("train_specifications")
tte = tte_raw.select(
    F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
    F.col(TTE_COL).cast(DoubleType()).alias(TTE_COL),
    F.col(EVENT_COL).cast(IntegerType()).alias(EVENT_COL),
    F.col("_source_uri").alias("_tte_source_uri"),
    F.col("_source_version").alias("_tte_source_version"),
)
specs = specs_raw.select(
    F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
    *[F.col(c).cast(StringType()).alias(c) for c in SPEC_COLS],
    F.col("_source_uri").alias("_specs_source_uri"),
    F.col("_source_version").alias("_specs_source_version"),
)
enforce_contract(tte, "train_tte")
enforce_contract(specs, "train_specifications")
vehicles = check_join(tte, specs, VEHICLE_ID_COL, "train TTE + specifications")

for name, contract_key in [
    ("train_operational_readouts", "train_operational_readouts"),
    ("validation_operational_readouts", "validation_operational_readouts"),
    ("test_operational_readouts", "test_operational_readouts"),
]:
    readouts = cast_readouts(load_bronze(name))
    enforce_contract(readouts, contract_key)
    if name == "train_operational_readouts":
        assert_same_ids(readouts, vehicles, VEHICLE_ID_COL, name)
    readouts = readouts.withColumnRenamed("_source_uri", "_readouts_source_uri").withColumnRenamed(
        "_source_version", "_readouts_source_version"
    )
    write_silver(readouts, name)

write_silver(vehicles, "train_vehicles")

for split in ("validation", "test"):
    split_specs = load_bronze(f"{split}_specifications").select(
        F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
        *[F.col(c).cast(StringType()).alias(c) for c in SPEC_COLS],
        F.col("_source_uri").alias("_specs_source_uri"),
        F.col("_source_version").alias("_specs_source_version"),
    )
    enforce_contract(split_specs, f"{split}_specifications")
    split_readouts = spark.read.table(
        qualified_table_name(DATA_SCHEMA, "silver", f"{split}_operational_readouts")
    )
    assert_same_ids(split_specs, split_readouts, VEHICLE_ID_COL, f"{split} specs + readouts")
    write_silver(split_specs, f"{split}_specifications")

    if split == "validation":
        labels = load_bronze("validation_labels").select(
            F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
            F.col("class_label").cast(IntegerType()).alias("class_label"),
            F.col("_source_uri").alias("_labels_source_uri"),
            F.col("_source_version").alias("_labels_source_version"),
        )
        enforce_contract(labels, "validation_labels")
        assert_same_ids(labels, split_specs, VEHICLE_ID_COL, "validation labels + specs")
        write_silver(labels, "validation_labels")

print("Silver criado com contratos e linhagem. Nenhum rótulo de teste foi carregado.")
