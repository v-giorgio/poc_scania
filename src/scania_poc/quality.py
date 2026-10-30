"""Quality gate — validação de dados antes da escrita em Silver.

Usa src/scania_poc/contracts.py para verificar o contrato e
lança QualityGateError se houver violações críticas.
"""

from pathlib import Path
from typing import Any

from src.scania_poc.contracts import DEFAULT_CONTRACT_PATH, validate_contract


class QualityGateError(Exception):
    """Levantado quando dados não passam no contrato antes de escrever em Silver."""


def run_quality_gate(
    df: Any,
    file_key: str,
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
    *,
    raise_on_failure: bool = True,
) -> dict[str, list[str]]:
    """Executa o quality gate para um DataFrame PySpark.

    Se raise_on_failure=True (padrão) e houver violações, lança QualityGateError.
    Se raise_on_failure=False, retorna o dict de violações para inspeção manual.
    """
    violations = validate_contract(df, file_key, contract_path)
    if violations and raise_on_failure:
        summary = "; ".join(f"{k}: {v}" for k, v in violations.items())
        raise QualityGateError(f"Quality gate falhou para '{file_key}': {summary}")
    return violations
