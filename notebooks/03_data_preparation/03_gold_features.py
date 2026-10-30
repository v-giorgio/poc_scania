# Databricks notebook source
# MAGIC %md
# MAGIC # 3.3 Gold: snapshots de treino sem leakage
# MAGIC
# MAGIC Divide veículos antes de selecionar snapshots ou ajustar preprocessadores.
# MAGIC Seleciona uma leitura determinística pseudoaleatória por veículo, sempre
# MAGIC anterior ao primeiro reparo ou fim de acompanhamento. Validação/teste oficiais
# MAGIC conservam o último readout fornecido; seus rótulos não entram no treino.

# COMMAND ----------

import pyspark.sql.functions as F
from pyspark.ml import Pipeline
from pyspark.ml.feature import Imputer, StringIndexer
from pyspark.sql.window import Window

from src.scania_poc.features import build_survival_snapshots
from src.scania_poc.config import qualified_table_name, validate_data_schema
from src.scania_poc.schema import (
    EVENT_COL,
    FEATURE_COLS,
    ORDINAL_HORIZON,
    SPEC_COLS,
    TTE_COL,
    TIME_STEP_COL,
    VEHICLE_ID_COL,
)
from src.scania_poc.splitting import split_by_vehicle

dbutils.widgets.text("DATA_SCHEMA", "", "Schema UC das tabelas gerenciadas")
dbutils.widgets.text("SEED", "42", "Seed para split e seleção de snapshot")
DATA_SCHEMA = validate_data_schema(dbutils.widgets.get("DATA_SCHEMA").strip())
SEED = int(dbutils.widgets.get("SEED"))


def load_silver(name):
    return spark.read.table(qualified_table_name(DATA_SCHEMA, "silver", name))


vehicles = load_silver("train_vehicles")
readouts = load_silver("train_operational_readouts")

# COMMAND ----------

# Fixar as partições por veículo antes de derivar linhas temporais.
vehicle_events = [
    (int(row[VEHICLE_ID_COL]), int(row[EVENT_COL]))
    for row in vehicles.select(VEHICLE_ID_COL, EVENT_COL).collect()
]
train_ids, internal_validation_ids, internal_test_ids = split_by_vehicle(
    [item[0] for item in vehicle_events],
    [item[1] for item in vehicle_events],
    ratios=(0.70, 0.15, 0.15),
    seed=SEED,
)
partition_rows = (
    [(vehicle_id, "train_fit") for vehicle_id in train_ids]
    + [(vehicle_id, "internal_validation") for vehicle_id in internal_validation_ids]
    + [(vehicle_id, "internal_test") for vehicle_id in internal_test_ids]
)
partition_df = spark.createDataFrame(partition_rows, [VEHICLE_ID_COL, "model_partition"])

readouts_by_id = {}
for partition_name, ids in [
    ("train_fit", train_ids),
    ("internal_validation", internal_validation_ids),
    ("internal_test", internal_test_ids),
]:
    partition_targets = vehicles.join(partition_df, VEHICLE_ID_COL).filter(
        F.col("model_partition") == partition_name
    )
    selected = build_survival_snapshots(
        readouts,
        partition_targets.select(
            VEHICLE_ID_COL, TTE_COL, EVENT_COL, "_tte_source_uri", "_tte_source_version"
        ),
        seed=SEED,
    )
    selected = selected.join(
        partition_targets.select(VEHICLE_ID_COL, *SPEC_COLS, "_specs_source_uri", "_specs_source_version"),
        on=VEHICLE_ID_COL,
        how="inner",
    )
    selected = selected.withColumn(
        "class_label_derived",
        F.when(
            ((F.col("event_observed") == 1) & (F.col("residual_time") > ORDINAL_HORIZON))
            | ((F.col("event_observed") == 0) & (F.col("residual_time") > ORDINAL_HORIZON)),
            F.lit(0),
        )
        .when(
            (F.col("event_observed") == 1)
            & (F.col("residual_time") > 24)
            & (F.col("residual_time") < 48),
            F.lit(1),
        )
        .when(
            (F.col("event_observed") == 1)
            & (F.col("residual_time") > 12)
            & (F.col("residual_time") < 24),
            F.lit(2),
        )
        .when(
            (F.col("event_observed") == 1)
            & (F.col("residual_time") > 6)
            & (F.col("residual_time") < 12),
            F.lit(3),
        )
        .when(
            (F.col("event_observed") == 1)
            & (F.col("residual_time") > 0)
            & (F.col("residual_time") < 6),
            F.lit(4),
        )
        .otherwise(F.lit(None).cast("int")),
    )
    if selected.count() != len(ids):
        no_snapshot = len(ids) - selected.count()
        print(f"{partition_name}: {no_snapshot} veículos sem readout elegível; excluídos e registrados")
    boundary_or_zero = selected.filter(
        F.col("residual_time").isin(0.0, 6.0, 12.0, 24.0, 48.0)
    ).count()
    censored_below_horizon = selected.filter(
        (F.col("event_observed") == 0) & (F.col("residual_time") < ORDINAL_HORIZON)
    ).count()
    unknown_labels = selected.filter(F.col("class_label_derived").isNull()).count()
    print(
        f"{partition_name}: rótulos ordinais desconhecidos={unknown_labels:,}; "
        f"fronteira/evento zero={boundary_or_zero:,}; "
        f"censura <48={censored_below_horizon:,}"
    )
    readouts_by_id[partition_name] = selected

# COMMAND ----------

# Ajustar indexers e imputador exclusivamente no treino interno.
train_fit = readouts_by_id["train_fit"]
indexed_cols = [f"{col}_idx" for col in SPEC_COLS]
imputed_cols = [f"{col}_imputed" for col in FEATURE_COLS]
stages = [
    StringIndexer(inputCol=col, outputCol=f"{col}_idx", handleInvalid="keep")
    for col in SPEC_COLS
]
stages.append(Imputer(inputCols=FEATURE_COLS, outputCols=imputed_cols, strategy="median"))
preprocessing = Pipeline(stages=stages).fit(train_fit)


def write_gold(frame, artifact, include_targets):
    transformed = preprocessing.transform(frame)
    columns = (
        [VEHICLE_ID_COL, "prediction_time", "residual_time", "event_observed", "class_label_derived"]
        if include_targets
        else [VEHICLE_ID_COL, "prediction_time"]
    )
    columns += imputed_cols + indexed_cols
    columns += ["_readouts_source_uri", "_readouts_source_version"]
    columns += ["_specs_source_uri", "_specs_source_version"]
    if include_targets:
        columns += ["_tte_source_uri", "_tte_source_version"]
    output = transformed.select(*columns)
    table = qualified_table_name(DATA_SCHEMA, "gold", artifact)
    output.write.format("delta").mode("overwrite").option(
        "overwriteSchema", "true"
    ).saveAsTable(table)
    return output.count()


for partition_name in ("train_fit", "internal_validation", "internal_test"):
    count = write_gold(
        readouts_by_id[partition_name],
        partition_name,
        include_targets=True,
    )
    print(f"{partition_name}: {count:,} snapshots Gold")

# COMMAND ----------

# A validação oficial e o teste não possuem TTE para construir alvo de sobrevivência.
# Os readouts já terminam no corte selecionado pela organização do desafio.
for split in ("validation", "test"):
    split_readouts = load_silver(f"{split}_operational_readouts")
    split_specs = load_silver(f"{split}_specifications")
    latest = (
        split_readouts.withColumn(
            "_rank",
            F.row_number().over(
                Window.partitionBy(VEHICLE_ID_COL).orderBy(F.desc(TIME_STEP_COL))
            ),
        )
        .filter(F.col("_rank") == 1)
        .withColumnRenamed(TIME_STEP_COL, "prediction_time")
        .drop("_rank")
    )
    latest = latest.join(
        split_specs.select(VEHICLE_ID_COL, *SPEC_COLS, "_specs_source_uri", "_specs_source_version"),
        on=VEHICLE_ID_COL,
        how="inner",
    )
    count = write_gold(latest, f"challenge_{split}", include_targets=False)
    print(f"challenge_{split}: {count:,} snapshots Gold, sem rótulo carregado")

print(f"Seed do split/snapshot: {SEED}; horizonte ordinal: {ORDINAL_HORIZON} time_steps")
