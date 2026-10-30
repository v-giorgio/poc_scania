# Databricks notebook source
# MAGIC %md
# MAGIC # 1.1 Entendimento do negócio — Component X
# MAGIC
# MAGIC **Pergunta analítica:** usando somente leituras disponíveis até um instante,
# MAGIC qual a distribuição do tempo/unidades residuais até o primeiro reparo
# MAGIC observado do Component X?

# COMMAND ----------

# MAGIC %md
# MAGIC ## Escopo e limites
# MAGIC
# MAGIC O dataset documenta reparos observados do Component X, incluindo veículos
# MAGIC sem reparo observado durante o acompanhamento (censura à direita). Não há
# MAGIC evidência para chamar todo reparo de falha física, generalizar para outros
# MAGIC componentes ou afirmar causalidade, segurança ou desempenho produtivo.
# MAGIC
# MAGIC Priorização de inspeções, disponibilidade e economia são hipóteses de valor
# MAGIC que exigem validação com stakeholders; não são resultados desta PoC.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Critérios de avaliação
# MAGIC
# MAGIC - Sobrevivência: discriminação, Brier com ponderação de censura e calibração
# MAGIC   em horizontes com suporte.
# MAGIC - RUL: métricas condicionais somente aos veículos com primeiro reparo observado.
# MAGIC - Ordinal: custo oficial de cinco classes, balanced accuracy, macro-F1 e recall
# MAGIC   por classe, usando a validação oficial apenas na etapa final.
# MAGIC - Split por veículo e corte estritamente anterior ao evento/fim de acompanhamento.
