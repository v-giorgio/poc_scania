# Databricks notebook source
# MAGIC %md
# MAGIC # 4.2 Experimentos MLflow
# MAGIC
# MAGIC **Inputs:** `s3://<bucket>/gold/features_predictive/`
# MAGIC
# MAGIC **Outputs:** Experimentos registrados no MLflow; melhor modelo no Model Registry

# COMMAND ----------

import mlflow

EXPERIMENT_NAME = "/poc_scania/experiments"
mlflow.set_experiment(EXPERIMENT_NAME)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Modelos Candidatos
# MAGIC
# MAGIC | Modelo | Justificativa |
# MAGIC |--------|--------------|
# MAGIC | Random Forest | Robusto a missings residuais; boa interpretabilidade via feature importance |
# MAGIC | XGBoost | Alta performance em datasets tabulares com desbalanceamento |
# MAGIC | LightGBM | Mais rápido que XGBoost; bom em datasets com muitas features |
# MAGIC
# MAGIC Para cada modelo, registrar no MLflow:
# MAGIC - [ ] Parâmetros do modelo
# MAGIC - [ ] Métricas (AUC-ROC, custo total, F1)
# MAGIC - [ ] Artefato do modelo serializado
# MAGIC - [ ] Comparação final no MLflow UI
