"""Métricas e avaliação de modelos."""

import numpy as np


def classification_cost(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, int]:
    """Calcula FP, FN e custo total para classificação binária (pesos IDA 2024)."""
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    return {
        "false_positives": fp,
        "false_negatives": fn,
        "total_cost": 10 * fp + 500 * fn,
    }


def mean_absolute_ordinal_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calcula o erro absoluto médio entre classes ordinais."""
    return float(np.mean(np.abs(y_true.astype(int) - y_pred.astype(int))))
