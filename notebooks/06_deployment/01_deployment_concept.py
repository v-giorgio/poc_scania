# Databricks notebook source
# MAGIC %md
# MAGIC # 6.1 Conceito de Implantação
# MAGIC
# MAGIC **Objetivo:** Documentar as opções de deploy e decisões necessárias.
# MAGIC Este notebook é conceitual — não executa um deploy real.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Opções de Deploy
# MAGIC
# MAGIC ### Opção A: Batch Scoring (recomendado para PoC)
# MAGIC - Databricks Job agendado (ex: diário ou por turno)
# MAGIC - Lê dados novos da tabela UC Gold
# MAGIC - Aplica modelo carregado do MLflow Model Registry
# MAGIC - Grava predições em uma tabela UC ou destino definido pelo consumidor
# MAGIC - **Vantagem:** simples, barato, sem cluster always-on
# MAGIC
# MAGIC ### Opção B: Endpoint REST (produção futura)
# MAGIC - MLflow Model Serving no Databricks
# MAGIC - API REST para scoring em tempo real por veículo
# MAGIC - **Desvantagem:** requer cluster always-on (custo maior)
# MAGIC
# MAGIC ## Decisões Pendentes
# MAGIC
# MAGIC - [ ] Definir consumidor das predições (dashboard, sistema de manutenção, alerta)
# MAGIC - [ ] Definir frequência de retreat e retreinamento
# MAGIC - [ ] Definir estratégia de monitoramento de drift de dados
# MAGIC - [ ] Definir SLA de latência (batch vs. real-time)
