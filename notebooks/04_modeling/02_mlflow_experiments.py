# Databricks notebook source
# MAGIC %md
# MAGIC # 4.2 Inspeção dos runs MLflow
# MAGIC
# MAGIC Resume os benchmarks calculados contra a validação interna. Este notebook
# MAGIC não retreina, não ajusta parâmetros e não consulta rótulos oficiais.

# COMMAND ----------

import mlflow

from src.scania_poc.tracking import personal_experiment_path

EXPERIMENT_NAME = personal_experiment_path(spark)
runs = mlflow.search_runs(
    experiment_names=[EXPERIMENT_NAME],
    order_by=["attributes.start_time DESC"],
)
if runs.empty:
    raise ValueError(f"Nenhum run encontrado em {EXPERIMENT_NAME}")

metric_columns = [
    column
    for column in runs.columns
    if column.startswith("metrics.validation/")
]
tag_columns = [
    column
    for column in (
        "tags.model_type",
        "tags.target",
        "params.git_revision",
        "tags.limitation",
    )
    if column in runs.columns
]
display(runs[["run_id", "status", *tag_columns, *metric_columns]])
