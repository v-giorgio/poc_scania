"""Validações de qualidade dos dados."""

from typing import Any


def validate_values(unique_values: set[Any], expected: set[Any]) -> bool:
    """Verifica se um conjunto de valores está contido no conjunto esperado."""
    return unique_values.issubset(expected)


def missing_rate(null_count: int, total_count: int) -> float:
    """Calcula a taxa de valores ausentes."""
    if total_count == 0:
        return 0.0
    return null_count / total_count


def validate_event_col(unique_values: set[Any]) -> bool:
    """Verifica se a coluna de evento contém apenas 0 e 1."""
    return unique_values.issubset({0, 1})
