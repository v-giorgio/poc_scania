# CLAUDE.md — poc_scania_michelin

## Contexto do Projeto
PoC de manutenção preditiva de veículos pesados usando o dataset público SCANIA APS Failure.
Demonstra competências de Engenharia de Dados, ML e Cloud no contexto de frotas conectadas (Michelin Connected Fleet).

## Stack
- **Armazenamento:** AWS S3 (camadas Raw / Silver / Gold via Delta Lake)
- **Processamento:** Databricks + PySpark
- **Tracking:** MLflow (integrado ao Databricks)
- **Código auxiliar:** Python 3.11+
- **Metodologia:** CRISP-DM

## Estrutura de Dados no S3
```
s3://<bucket>/
  raw/scania_component_x/         # dataset original, sem modificações
  silver/component_x/             # dados limpos, tipados, particionados
  gold/features_predictive/       # features prontas para modelagem
```

## Convenções de Notebooks Databricks
- Formato `.py` com `# COMMAND ----------` para delimitar células
- Nome: `NN_descricao_snake_case.py`
- Primeira célula: docstring/magic com objetivo, inputs e outputs esperados

## Regras para Claude Code
- Não criar credenciais, tokens ou secrets em arquivos rastreados pelo git
- Não versionar datasets, artefatos de modelo (.pkl, .mlflow) nem checkpoints
- Respeitar a metodologia CRISP-DM na organização dos notebooks
- Código Python deve passar em `ruff check` e `ruff format`
- Testes em `tests/unit/` para toda função em `src/`
- Antes de criar novos subagentes em `.claude/agents/`, consultar o usuário

## Decisões Pendentes
- Dataset: verificar licença e método de download antes de automatizar
- Bucket S3 e permissões IAM: a definir
- Cluster Databricks: tamanho e configuração a definir
- Estratégia de deploy do modelo: batch score vs. endpoint REST
- Ver `docs/decisions/ADR-001-stack-choices.md` para contexto
