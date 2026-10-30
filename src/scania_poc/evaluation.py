"""Evaluation metrics for the SCANIA Component X PoC."""

import numpy as np

ORDINAL_COST_MATRIX = np.asarray(
    [
        [0, 7, 8, 9, 10],
        [200, 0, 7, 8, 9],
        [300, 200, 0, 7, 8],
        [400, 300, 200, 0, 7],
        [500, 400, 300, 200, 0],
    ],
    dtype=np.int64,
)


def ordinal_total_cost(y_true: np.ndarray, y_pred: np.ndarray) -> int:
    """Sum the official IDA 2024 ordinal misclassification costs."""
    true = np.asarray(y_true, dtype=int)
    pred = np.asarray(y_pred, dtype=int)
    if true.shape != pred.shape:
        raise ValueError("y_true e y_pred devem ter o mesmo formato")
    if not np.isin(true, np.arange(5)).all() or not np.isin(pred, np.arange(5)).all():
        raise ValueError("y_true e y_pred devem conter classes entre 0 e 4")
    return int(ORDINAL_COST_MATRIX[true, pred].sum())


def mean_absolute_ordinal_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate mean absolute distance between ordinal class indices."""
    true = np.asarray(y_true, dtype=int)
    pred = np.asarray(y_pred, dtype=int)
    if true.shape != pred.shape:
        raise ValueError("y_true e y_pred devem ter o mesmo formato")
    return float(np.mean(np.abs(true - pred)))
