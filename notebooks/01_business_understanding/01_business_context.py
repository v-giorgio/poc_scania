# Databricks notebook source
# MAGIC %md
# MAGIC # 1.1 Contexto de Negócio
# MAGIC
# MAGIC **Objetivo:** Definir o problema de negócio, critérios de sucesso e restrições.
# MAGIC
# MAGIC **Inputs:** Nenhum (análise qualitativa)
# MAGIC
# MAGIC **Outputs:** Entendimento documentado do problema — base para todas as etapas seguintes

# COMMAND ----------

# MAGIC %md
# MAGIC ## Problema de Negócio
# MAGIC
# MAGIC Falhas no sistema de pressão de ar (APS) de caminhões Scania causam paradas não planejadas,
# MAGIC gerando custos elevados de reparo, perda de produtividade e impacto na cadeia logística.
# MAGIC
# MAGIC **Objetivo do modelo:** classificar veículos com risco de falha no APS antes que a falha ocorra,
# MAGIC permitindo manutenção preventiva e reduzindo paradas inesperadas.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Custo Assimétrico de Classificação
# MAGIC
# MAGIC O dataset original define uma função de custo explícita:
# MAGIC
# MAGIC | Tipo de Erro | Significado | Custo Unitário |
# MAGIC |-------------|-------------|---------------|
# MAGIC | Falso Positivo | Manutenção desnecessária | 10 |
# MAGIC | Falso Negativo | Falha não detectada, veículo quebra em campo | 500 |
# MAGIC
# MAGIC **Custo total = 10 × FP + 500 × FN**
# MAGIC
# MAGIC Minimizar este custo é o critério primário de avaliação.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Critérios de Sucesso
# MAGIC
# MAGIC | Métrica | Threshold |
# MAGIC |---------|-----------|
# MAGIC | AUC-ROC | > 0.85 |
# MAGIC | Custo total | < baseline (classificar tudo como negativo) |
# MAGIC | Pipeline | Reproduzível e documentado |
# MAGIC
# MAGIC ## Contexto de Frotas Conectadas
# MAGIC
# MAGIC Em um cenário como Michelin Connected Fleet, os dados de sensores chegam continuamente
# MAGIC de múltiplos veículos. A arquitetura desta PoC (S3 + Databricks + Delta Lake) é
# MAGIC diretamente aplicável a esse contexto de dados em escala.
