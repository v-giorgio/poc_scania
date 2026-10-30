"""Compatibility exports for canonical Component X evaluation metrics."""

from src.scania_poc.evaluation import (
    ORDINAL_COST_MATRIX,
    mean_absolute_ordinal_error,
    ordinal_total_cost,
)

__all__ = ["ORDINAL_COST_MATRIX", "mean_absolute_ordinal_error", "ordinal_total_cost"]
