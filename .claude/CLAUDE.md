# CLAUDE.md — poc_scania_michelin

## Contexto do Projeto
PoC exploratória sobre o tempo residual até o primeiro reparo observado do SCANIA Component X (IDA 2024).
Demonstra competências de Engenharia de Dados, ML e Cloud no contexto de frotas conectadas (Michelin Connected Fleet).

## Stack
- **Armazenamento:** Unity Catalog managed volume para Raw; tabelas UC gerenciadas em Delta para Bronze/Silver/Gold
- **Processamento:** Databricks Free Edition serverless + PySpark/Spark Connect
- **Tracking:** MLflow (integrado ao Databricks)
- **Código auxiliar:** Python 3.11+
- **Metodologia:** CRISP-DM

## Estrutura de dados no Databricks
```
/Volumes/<catalog>/<schema>/<volume>/raw/  # CSVs originais, sem modificações
<catalog>.<schema>.bronze_<arquivo>        # Delta com path/SHA-256/horário
<catalog>.<schema>.silver_<artefato>       # dados tipados e validados
<catalog>.<schema>.gold_<partição>         # features prontas para modelagem
```

## Convenções de Notebooks Databricks
- Formato `.py` com `# COMMAND ----------` para delimitar células
- Nome: `NN_descricao_snake_case.py`
- Primeira célula: docstring/magic com objetivo, inputs e outputs esperados

## Regras para Claude Code
- Não criar credenciais, tokens ou secrets em arquivos rastreados pelo git
- Não versionar datasets, artefatos de modelo (.pkl, .mlflow) nem checkpoints
- Não usar `test_labels.csv`: o pacote oficial não fornece rótulos de teste
- Excluir do treino ordinal censurados antes de 48 unidades e tempos exatamente nas fronteiras
- Nunca usar features após o corte ou TTE/status como feature
- Respeitar a metodologia CRISP-DM na organização dos notebooks
- Código Python deve passar em `ruff check` e `ruff format`
- Testes em `tests/unit/` para toda função em `src/`
- Antes de criar novos subagentes em `.claude/agents/`, consultar o usuário

## Decisões Pendentes
- Dataset: arquivos são obtidos manualmente da página oficial; não automatizar download
- `RAW_VOLUME_PATH` e `DATA_SCHEMA`: informar como widgets de execução
- Free Edition é pessoal/não comercial e sujeita a quotas de compute
- Estratégia de deploy do modelo: batch score vs. endpoint REST
- Estratégia de deploy do modelo: batch score vs. endpoint REST
- Ver `docs/decisions/ADR-001-stack-choices.md` para contexto
