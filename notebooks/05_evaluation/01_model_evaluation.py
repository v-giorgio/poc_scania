# Databricks notebook source
# MAGIC %md
# MAGIC # 5.1 Avaliação do Modelo
# MAGIC
# MAGIC **Inputs:** Melhor modelo do MLflow Model Registry
# MAGIC
# MAGIC **Outputs:** Relatório de avaliação, análise de erros, decisão de promoção do modelo

# COMMAND ----------

# MAGIC %md
# MAGIC ## Critérios de Aprovação
# MAGIC
# MAGIC | Métrica | Threshold |
# MAGIC |---------|-----------|
# MAGIC | AUC-ROC | > 0.85 |
# MAGIC | Custo total | < baseline (tudo negativo) |
# MAGIC
# MAGIC ## Análises Planejadas
# MAGIC
# MAGIC - [ ] Curva ROC e AUC no conjunto de teste
# MAGIC - [ ] Matriz de confusão
# MAGIC - [ ] Custo total comparado ao baseline e entre modelos
# MAGIC - [ ] Feature importance (SHAP se viável)
# MAGIC - [ ] Análise de erros: quais amostras o modelo erra mais?
# MAGIC - [ ] Comparação de todos os runs no MLflow UI
