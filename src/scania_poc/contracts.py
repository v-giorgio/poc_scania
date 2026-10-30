"""Validação de contratos de dados para o dataset SCANIA Component X.

Carrega o contrato de config/data_contract.yaml e verifica DataFrames PySpark
contra as regras definidas. Deve ser executado antes de qualquer escrita em Silver.

Funções puras (load_contract, validate_required_columns) não dependem de PySpark
e podem ser usadas em testes locais. Funções que recebem DataFrame importam
pyspark lazily para não bloquear testes sem Spark.
"""

from pathlib import Path
from typing import Any

import yaml

from src.scania_poc.validators import missing_rate


def load_contract(contract_path: str | Path) -> dict[str, Any]:
    """Carrega o contrato de dados do YAML."""
    with open(contract_path) as f:
        return yaml.safe_load(f)


def validate_required_columns(df: Any, required_cols: list[str]) -> list[str]:
    """Retorna lista de colunas obrigatórias ausentes no DataFrame."""
    return [col for col in required_cols if col not in df.columns]


def validate_no_unexpected_nulls(df: Any, col: str, nullable: bool) -> int:
    """Retorna contagem de nulos em coluna não-nullable. Zero se nullable=True."""
    if nullable:
        return 0
    import pyspark.sql.functions as F  # noqa: PLC0415

    return df.filter(F.col(col).isNull()).count()


def validate_allowed_values(df: Any, col: str, allowed: list[Any]) -> set:
    """Retorna valores encontrados que não estão na lista de permitidos."""
    found = {r[col] for r in df.select(col).distinct().collect()}
    return found - set(allowed)


def validate_uniqueness(df: Any, col: str) -> int:
    """Retorna número de valores duplicados em coluna que deve ser única."""
    total = df.count()
    distinct = df.select(col).distinct().count()
    return total - distinct


def validate_contract(
    df: Any,
    file_key: str,
    contract_path: str | Path = "config/data_contract.yaml",
) -> dict[str, list[str]]:
    """Valida um DataFrame PySpark contra o contrato do arquivo especificado.

    Retorna dict com chave=nome-da-regra e valor=lista de violações encontradas.
    Dict vazio significa que o DataFrame passou em todas as verificações.
    """
    import pyspark.sql.functions as F  # noqa: PLC0415

    contract = load_contract(contract_path)
    file_spec = contract["files"].get(file_key)
    if file_spec is None:
        raise ValueError(f"Arquivo '{file_key}' não encontrado no contrato")

    violations: dict[str, list[str]] = {}
    required_cols_spec = file_spec.get("required_columns", {})
    required_col_names = list(required_cols_spec.keys())

    missing_cols = validate_required_columns(df, required_col_names)
    if missing_cols:
        violations["missing_columns"] = missing_cols

    for col, spec in required_cols_spec.items():
        if col not in df.columns:
            continue

        nullable = spec.get("nullable", True)
        null_violations = validate_no_unexpected_nulls(df, col, nullable)
        if null_violations > 0:
            violations.setdefault("non_nullable_nulls", []).append(
                f"{col}: {null_violations} nulls"
            )

        if "allowed_values" in spec:
            bad_vals = validate_allowed_values(df, col, spec["allowed_values"])
            if bad_vals:
                violations.setdefault("invalid_values", []).append(f"{col}: {bad_vals}")

        if spec.get("unique", False):
            dups = validate_uniqueness(df, col)
            if dups > 0:
                violations.setdefault("uniqueness", []).append(f"{col}: {dups} duplicates")

        if "min_value" in spec:
            below_min = df.filter(F.col(col) < spec["min_value"]).count()
            if below_min > 0:
                violations.setdefault("range_violations", []).append(
                    f"{col}: {below_min} values below {spec['min_value']}"
                )

    max_missing = file_spec.get("max_missing_rate", 1.0)
    n_total = df.count()
    n_cells = n_total * len(df.columns)
    if n_cells > 0:
        null_count = df.select([F.sum(F.col(c).isNull().cast("int")) for c in df.columns])
        total_nulls = sum(null_count.collect()[0])
        global_rate = missing_rate(total_nulls, n_cells)
        if global_rate > max_missing:
            violations["global_missing_rate"] = [f"{global_rate:.3%} > threshold {max_missing:.3%}"]

    return violations
