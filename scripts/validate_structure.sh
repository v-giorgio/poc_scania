#!/usr/bin/env bash
# Valida que a estrutura de diretórios e arquivos essenciais existe.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ERRORS=0

check() {
    local path="$ROOT/$1"
    if [ -e "$path" ]; then
        echo "  OK      $1"
    else
        echo "  MISSING $1"
        ERRORS=$((ERRORS + 1))
    fi
}

echo "=== Validando estrutura: $ROOT ==="
echo ""

echo "--- Raiz ---"
check "CLAUDE.md"
check "README.md"
check "pyproject.toml"
check ".gitignore"

echo ""
echo "--- Claude Code ---"
check ".claude/CLAUDE.md"
check ".claude/agents"

echo ""
echo "--- Documentação ---"
check "docs/architecture.md"
check "docs/setup.md"
check "docs/cloud_cost_estimate.md"
check "docs/crisp_dm_plan.md"
check "docs/decisions/ADR-001-stack-choices.md"

echo ""
echo "--- Notebooks (CRISP-DM) ---"
check "notebooks/01_business_understanding/01_business_context.py"
check "notebooks/02_data_understanding/01_data_exploration.py"
check "notebooks/02_data_understanding/02_data_quality.py"
check "notebooks/03_data_preparation/01_ingest_raw.py"
check "notebooks/03_data_preparation/02_silver_transform.py"
check "notebooks/03_data_preparation/03_gold_features.py"
check "notebooks/04_modeling/01_baseline_model.py"
check "notebooks/04_modeling/02_mlflow_experiments.py"
check "notebooks/05_evaluation/01_model_evaluation.py"
check "notebooks/06_deployment/01_deployment_concept.py"

echo ""
echo "--- Código Python ---"
check "src/config.py"
check "src/data/schema.py"
check "src/data/validators.py"
check "src/features/engineering.py"
check "src/models/evaluation.py"

echo ""
echo "--- Testes ---"
check "tests/conftest.py"
check "tests/unit/test_schema.py"
check "tests/unit/test_validators.py"
check "tests/unit/test_evaluation.py"

echo ""
echo "--- Configuração ---"
check "config/dev.env.example"
check "config/databricks.yml.example"

echo ""
echo "--- CI ---"
check ".github/workflows/ci.yml"

echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "Estrutura válida. Todos os arquivos essenciais presentes."
else
    echo "$ERRORS arquivo(s) ausente(s). Revise antes de continuar."
    exit 1
fi
