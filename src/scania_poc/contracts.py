"""Validação de contratos de dados para o dataset SCANIA Component X.

Carrega o contrato de config/data_contract.yaml e verifica DataFrames PySpark
contra as regras definidas. Deve ser executado antes de qualquer escrita em Silver.

Funções puras (load_contract, validate_required_columns) não dependem de PySpark
e podem ser usadas em testes locais. Funções que recebem DataFrame importam
pyspark lazily para não bloquear testes sem Spark.
"""

import re
from pathlib import Path
from typing import Any

import yaml

from src.scania_poc.validators import missing_rate

DEFAULT_CONTRACT_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "data_contract.yaml"
)


def load_contract(contract_path: str | Path = DEFAULT_CONTRACT_PATH) -> dict[str, Any]:
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
    contract_path: str | Path = DEFAULT_CONTRACT_PATH,
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

    dtype_aliases = {
        "int": {"int", "bigint", "smallint", "tinyint"},
        "float": {"float", "double", "decimal"},
        "str": {"string"},
    }
    for col, spec in required_cols_spec.items():
        if col not in df.columns:
            continue

        expected_type = spec.get("dtype")
        actual_type = df.schema[col].dataType.simpleString().lower()
        if expected_type in dtype_aliases and not any(
            actual_type.startswith(alias) for alias in dtype_aliases[expected_type]
        ):
            violations.setdefault("dtype_mismatch", []).append(
                f"{col}: expected {expected_type}, observed {actual_type}"
            )

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

        if "pattern" in spec:
            invalid = df.filter(
                F.col(col).isNotNull() & ~F.col(col).cast("string").rlike(spec["pattern"])
            ).count()
            if invalid:
                violations.setdefault("pattern_violations", []).append(
                    f"{col}: {invalid} values do not match {spec['pattern']}"
                )

    feature_spec = file_spec.get("feature_columns", {})
    feature_pattern = feature_spec.get("prefix")
    feature_cols = [col for col in df.columns if feature_pattern and re.match(feature_pattern, col)]
    measured_cols = [col for col in required_col_names if col in df.columns] + feature_cols
    if feature_spec and len(feature_cols) != 105:
        violations["feature_column_count"] = [
            f"expected 105 sensor columns, found {len(feature_cols)}"
        ]

    for col in feature_cols:
        actual_type = df.schema[col].dataType.simpleString().lower()
        if actual_type not in dtype_aliases.get(feature_spec.get("dtype"), set()):
            violations.setdefault("dtype_mismatch", []).append(
                f"{col}: expected {feature_spec.get('dtype')}, observed {actual_type}"
            )

    numeric_cols = [
        col
        for col in measured_cols
        if col in df.columns
        and (col in feature_cols or required_cols_spec.get(col, {}).get("dtype") == "float")
    ]
    for col in numeric_cols:
        non_finite = df.filter(
            F.col(col).isNotNull()
            & (F.isnan(F.col(col)) | F.col(col).isin(float("inf"), float("-inf")))
        ).count()
        if non_finite:
            violations.setdefault("non_finite_values", []).append(
                f"{col}: {non_finite} NaN/Infinity values"
            )

    key_cols = file_spec.get("unique_key", [])
    if key_cols and all(col in df.columns for col in key_cols):
        duplicate_keys = df.groupBy(*key_cols).count().filter(F.col("count") > 1).count()
        if duplicate_keys:
            violations["duplicate_keys"] = [f"{key_cols}: {duplicate_keys} duplicate key groups"]

    max_missing = file_spec.get("max_missing_rate", 1.0)
    n_total = df.count()
    n_cells = n_total * len(measured_cols)
    if n_cells > 0:
        null_count = df.select(
            [F.sum(F.col(c).isNull().cast("int")).alias(c) for c in measured_cols]
        )
        total_nulls = sum(null_count.collect()[0])
        global_rate = missing_rate(total_nulls, n_cells)
        if global_rate > max_missing:
            violations["global_missing_rate"] = [f"{global_rate:.3%} > threshold {max_missing:.3%}"]

    if feature_cols and n_total:
        nulls_by_feature = df.select(
            [F.sum(F.col(c).isNull().cast("int")).alias(c) for c in feature_cols]
        ).collect()[0]
        threshold = feature_spec.get("max_missing_rate", 1.0)
        for col in feature_cols:
            rate = nulls_by_feature[col] / n_total
            if rate > threshold:
                violations.setdefault("feature_missing_rate", []).append(
                    f"{col}: {rate:.3%} > threshold {threshold:.3%}"
                )

    return violations
