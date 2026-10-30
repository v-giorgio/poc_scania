"""Ordinal IDA 2024 benchmark using only labels known from residual time."""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score

from src.scania_poc.evaluation import mean_absolute_ordinal_error, ordinal_total_cost
from src.scania_poc.schema import (
    ORDINAL_CLASSES,
    ORDINAL_HORIZON,
    UNKNOWN_ORDINAL_CLASS,
)


def bin_tte_to_classes(
    residual_time: np.ndarray | pd.Series,
    events: np.ndarray | pd.Series,
    class_map: dict[int, tuple[float, float]] | None = None,
    horizon: float = ORDINAL_HORIZON,
) -> np.ndarray:
    """Map residual follow-up to official classes; unknown cases receive -1.

    ``residual_time`` is T - prediction_time, not absolute TTE. Classes 1–4
    require an observed event and an interior point in their time window.
    Class 0 requires no event within 48 units: an event after the horizon or
    censoring observed beyond the full horizon. Boundary inclusion is not
    stated in the challenge call, so exact boundaries remain unknown.
    """
    if class_map is None:
        class_map = ORDINAL_CLASSES

    residual = np.asarray(residual_time, dtype=float)
    event = np.asarray(events, dtype=int)
    if residual.shape != event.shape:
        raise ValueError("residual_time e events devem ter o mesmo formato")
    if not np.isin(event, [0, 1]).all():
        raise ValueError("events deve conter apenas 0 (censura) e 1 (evento)")

    result = np.full(residual.shape, UNKNOWN_ORDINAL_CLASS, dtype=int)
    result[(event == 1) & (residual > horizon)] = 0
    result[(event == 0) & (residual > horizon)] = 0
    for class_id, (lower, upper) in class_map.items():
        in_window = (event == 1) & (residual > lower) & (residual < upper)
        result[in_window] = class_id
    return result


def fit_ordinal_classifier(
    X_train: pd.DataFrame | np.ndarray,
    y_train: np.ndarray,
    n_estimators: int = 100,
    max_depth: int | None = 10,
    seed: int = 42,
) -> RandomForestClassifier:
    """Fit a class-balanced Random Forest benchmark."""
    known = np.asarray(y_train) >= 0
    if not known.any():
        raise ValueError("Nenhum rótulo ordinal conhecido para treino")
    x = X_train.loc[known] if isinstance(X_train, pd.DataFrame) else np.asarray(X_train)[known]
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(x, np.asarray(y_train)[known])
    return model


def evaluate_ordinal(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_classes: int = 5,
) -> dict[str, object]:
    """Return ordinal metrics and the official asymmetric total cost."""
    labels = list(range(n_classes))
    true = np.asarray(y_true, dtype=int)
    pred = np.asarray(y_pred, dtype=int)
    if true.shape != pred.shape or len(true) == 0:
        raise ValueError("y_true/y_pred devem ter mesmo formato não vazio")
    cm = confusion_matrix(true, pred, labels=labels)
    per_class_recall = np.divide(
        cm.diagonal(),
        cm.sum(axis=1),
        out=np.zeros(n_classes, dtype=float),
        where=cm.sum(axis=1) > 0,
    )
    return {
        "confusion_matrix": cm.tolist(),
        "balanced_accuracy": float(balanced_accuracy_score(true, pred)),
        "macro_f1": float(f1_score(true, pred, labels=labels, average="macro", zero_division=0)),
        "recall_by_class": per_class_recall.tolist(),
        "maoe": mean_absolute_ordinal_error(true, pred),
        "total_cost": ordinal_total_cost(true, pred),
        "n": int(len(true)),
    }
