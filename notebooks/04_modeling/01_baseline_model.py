# Databricks notebook source
# MAGIC %md
# MAGIC # 4.1 Modelo Baseline
# MAGIC
# MAGIC **Inputs:** `s3://<bucket>/gold/features_predictive/`
# MAGIC
# MAGIC **Outputs:** Experimento MLflow com métricas do baseline (Regressão Logística)

# COMMAND ----------

import mlflow

EXPERIMENT_NAME = "/poc_scania/baseline"
mlflow.set_experiment(EXPERIMENT_NAME)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Baseline: Regressão Logística
# MAGIC
# MAGIC Serve como referência mínima para comparar modelos subsequentes.
# MAGIC
# MAGIC **Métricas a registrar no MLflow:**
# MAGIC - AUC-ROC
# MAGIC - Precision / Recall / F1
# MAGIC - Custo total: `10 × FP + 500 × FN`
# MAGIC - Matriz de confusão
# MAGIC
# MAGIC **Referência de custo:** classificar tudo como negativo tem custo = 500 × (total de positivos).
