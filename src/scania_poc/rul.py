"""Benchmark de Regressão RUL (Remaining Useful Life).

Usa RandomForestRegressor do scikit-learn como modelo benchmark.
Métricas: MAE, Median AE, RMSE — calculadas apenas sobre veículos com evento.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor


def fit_rul_regressor(
    X_train: pd.DataFrame | np.ndarray,
    y_train: np.ndarray,
    n_estimators: int = 100,
    max_depth: int | None = 10,
    seed: int = 42,
) -> RandomForestRegressor:
    """Ajusta RandomForestRegressor como benchmark de regressão de RUL."""
    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def evaluate_rul(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    events: np.ndarray | None = None,
) -> dict[str, float]:
    """Calcula métricas de RUL, condicionalmente sobre veículos com evento.

    Se events for fornecido (array de 0/1), as métricas são calculadas
    apenas sobre as observações onde events == 1 (reparo observado).
    Isso evita penalizar o modelo por erros em censurados.
    """
    if events is not None:
        mask = events.astype(bool)
        y_true = y_true[mask]
        y_pred = y_pred[mask]

    if len(y_true) == 0:
        return {"mae": float("nan"), "median_ae": float("nan"), "rmse": float("nan"), "n": 0}

    errors = np.abs(y_true - y_pred)
    return {
        "mae": float(np.mean(errors)),
        "median_ae": float(np.median(errors)),
        "rmse": float(np.sqrt(np.mean((y_true - y_pred) ** 2))),
        "n": int(len(y_true)),
    }
