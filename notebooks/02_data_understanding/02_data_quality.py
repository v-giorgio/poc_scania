# Databricks notebook source
# MAGIC %md
# MAGIC # 2.2 Quality checks sobre as tabelas Bronze
# MAGIC
# MAGIC Verifica parsing, contratos, chaves e consistência sem imprimir registros.
# MAGIC Falhas críticas interrompem a progressão para Silver.

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

dbutils.widgets.text("DATA_SCHEMA", "", "Schema UC das tabelas Bronze")
DATA_SCHEMA = validate_data_schema(dbutils.widgets.get("DATA_SCHEMA").strip())


def bronze(name):
    return spark.read.table(qualified_table_name(DATA_SCHEMA, "bronze", name))


def assert_contract(frame, key):
    violations = validate_contract(frame, key)
    if violations:
        raise ValueError(f"Contrato {key} falhou: {violations}")


def vehicle_ids(frame):
    return frame.select(VEHICLE_ID_COL).distinct()


def assert_same_ids(left, right, label):
    a = vehicle_ids(left)
    b = vehicle_ids(right)
    missing = a.join(b, VEHICLE_ID_COL, "left_anti").limit(1).count()
    extra = b.join(a, VEHICLE_ID_COL, "left_anti").limit(1).count()
    if missing or extra:
        raise ValueError(f"IDs divergentes em {label}: missing={missing}, extra={extra}")


tte = bronze("train_tte").select(
    F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
    F.col(TTE_COL).cast(DoubleType()).alias(TTE_COL),
    F.col(EVENT_COL).cast(IntegerType()).alias(EVENT_COL),
)
specs = bronze("train_specifications").select(
    F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
    *[F.col(col).cast(StringType()).alias(col) for col in SPEC_COLS],
)
readouts_source = bronze("train_operational_readouts")
readouts = readouts_source.select(
    F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
    F.col(TIME_STEP_COL).cast(DoubleType()).alias(TIME_STEP_COL),
    *[
        F.when(
            F.isnan(F.col(col).cast(DoubleType())), F.lit(None).cast(DoubleType())
        ).otherwise(F.col(col).cast(DoubleType())).alias(col)
        for col in FEATURE_COLS
    ],
)
assert_contract(tte, "train_tte")
assert_contract(specs, "train_specifications")
assert_contract(readouts, "train_operational_readouts")

# COMMAND ----------

dup_tte = tte.groupBy(VEHICLE_ID_COL).count().filter(F.col("count") > 1).count()
dup_readouts = (
    readouts.groupBy(VEHICLE_ID_COL, TIME_STEP_COL)
    .count()
    .filter(F.col("count") > 1)
    .count()
)
if dup_tte or dup_readouts:
    raise ValueError(f"Duplicatas: train_tte={dup_tte}, readout_keys={dup_readouts}")
assert_same_ids(tte, specs, "train TTE/specifications")
assert_same_ids(tte, readouts, "train TTE/readouts")
print(f"Integridade de IDs e chaves OK: {tte.count():,} veículos; {readouts.count():,} readouts")

bad_event = tte.filter(~F.col(EVENT_COL).isin(0, 1)).count()
bad_duration = tte.filter(
    F.col(TTE_COL).isNull()
    | F.isnan(F.col(TTE_COL))
    | F.col(TTE_COL).isin(float("inf"), float("-inf"))
    | (F.col(TTE_COL) <= 0)
).count()
bad_time = readouts.filter(
    F.col(TIME_STEP_COL).isNull()
    | F.isnan(F.col(TIME_STEP_COL))
    | F.col(TIME_STEP_COL).isin(float("inf"), float("-inf"))
    | (F.col(TIME_STEP_COL) < 0)
).count()
if bad_event or bad_duration or bad_time:
    raise ValueError(f"Domínios inválidos: event={bad_event}, TTE={bad_duration}, time_step={bad_time}")

# Descrever, sem descartar, veículos cuja última leitura excede o TTE resumido.
max_readout = readouts.groupBy(VEHICLE_ID_COL).agg(F.max(TIME_STEP_COL).alias("max_time"))
temporal = max_readout.join(tte.select(VEHICLE_ID_COL, TTE_COL), VEHICLE_ID_COL)
late_readouts = temporal.filter(F.col("max_time") >= F.col(TTE_COL)).count()
print(f"Veículos com readout no instante/depois do fim TTE: {late_readouts:,}; snapshot Gold os excluirá.")

# COMMAND ----------

validation_labels = bronze("validation_labels").select(
    F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
    F.col("class_label").cast(IntegerType()).alias("class_label"),
)
validation_specs = bronze("validation_specifications").select(
    F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
    *[F.col(col).cast(StringType()).alias(col) for col in SPEC_COLS],
)
test_specs = bronze("test_specifications").select(
    F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
    *[F.col(col).cast(StringType()).alias(col) for col in SPEC_COLS],
)


def cast_readouts(df):
    return df.select(
        F.col(VEHICLE_ID_COL).cast(IntegerType()).alias(VEHICLE_ID_COL),
        F.col(TIME_STEP_COL).cast(DoubleType()).alias(TIME_STEP_COL),
        *[
            F.when(
                F.isnan(F.col(col).cast(DoubleType())), F.lit(None).cast(DoubleType())
            ).otherwise(F.col(col).cast(DoubleType())).alias(col)
            for col in FEATURE_COLS
        ],
    )


validation_readouts = cast_readouts(bronze("validation_operational_readouts"))
test_readouts = cast_readouts(bronze("test_operational_readouts"))
assert_contract(validation_labels, "validation_labels")
assert_contract(validation_specs, "validation_specifications")
assert_contract(test_specs, "test_specifications")
assert_contract(validation_readouts, "validation_operational_readouts")
assert_contract(test_readouts, "test_operational_readouts")
assert_same_ids(validation_labels, validation_specs, "validation labels/specifications")
assert_same_ids(validation_specs, validation_readouts, "validation specifications/readouts")
assert_same_ids(test_specs, test_readouts, "test specifications/readouts")

train_ids = vehicle_ids(tte)
validation_ids = vehicle_ids(validation_specs)
test_ids = vehicle_ids(test_specs)
overlaps = {
    "train_validation": train_ids.join(validation_ids, VEHICLE_ID_COL).count(),
    "train_test": train_ids.join(test_ids, VEHICLE_ID_COL).count(),
    "validation_test": validation_ids.join(test_ids, VEHICLE_ID_COL).count(),
}
if any(overlaps.values()):
    raise ValueError(f"Sobreposição entre partições: {overlaps}")
print(f"Sem sobreposição entre partições: {overlaps}")
print("Quality checks Bronze concluídos; nenhum CSV ou registro bruto foi exibido.")
