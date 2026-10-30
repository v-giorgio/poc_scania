"""Métricas e avaliação de modelos."""

import numpy as np


def classification_cost(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, int]:
    """Calcula FP, FN e custo total com os pesos do dataset SCANIA."""
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    return {
        "false_positives": fp,
        "false_negatives": fn,
        "total_cost": 10 * fp + 500 * fn,
    }
