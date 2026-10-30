# PoC — Manutenção Preditiva de Veículos Pesados

PoC de Engenharia de Dados e Machine Learning usando o dataset público **SCANIA APS Failure**.
Contexto: frotas conectadas, similar ao Michelin Connected Fleet.

## Stack
- **AWS S3** — armazenamento em camadas (Raw / Silver / Gold)
- **Databricks + PySpark** — processamento e notebooks CRISP-DM
- **Delta Lake** — formato de tabela com ACID e schema enforcement
- **MLflow** — tracking de experimentos e model registry
- **Python 3.11** — código auxiliar, testes e automação

## Estrutura
Veja [docs/architecture.md](docs/architecture.md) para a arquitetura detalhada.
Veja [docs/setup.md](docs/setup.md) para instruções de setup.

## Metodologia
CRISP-DM — notebooks organizados por etapa em `notebooks/`.

## Dataset
SCANIA APS Failure (UCI ML Repository).
**Verificar licença antes de usar.** Instruções em `scripts/download_dataset.sh`.

## Quick Start

```bash
uv sync --dev
uv run pytest tests/unit/ -v
bash scripts/validate_structure.sh
```
