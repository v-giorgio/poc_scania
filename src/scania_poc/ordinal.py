"""Benchmark de Classificação Ordinal — SCANIA Component X (IDA 2024).

Mapeia TTE para classes ordinais e treina um classificador.
Métricas: confusion matrix, balanced accuracy, macro-F1, MAOE.

HIPÓTESE sobre as classes (confirmar com paper):
  0 = TTE > 48  (sem reparo iminente)
  1 = 24–48
  2 = 12–24
  3 = 6–12
  4 = 0–6 (reparo iminente)
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, f1_score

from src.scania_poc.evaluation import mean_absolute_ordinal_error
from src.scania_poc.schema import ORDINAL_CLASSES


def bin_tte_to_classes(
    tte: np.ndarray | pd.Series,
    events: np.ndarray | pd.Series,
    class_map: dict[int, tuple[float, float]] | None = None,
) -> np.ndarray:
    """Converte TTE em classes ordinais.

    Veículos censurados (events == 0) ou com TTE além do maior bucket
    recebem a classe mais alta (sem urgência).

    class_map: dict {class_int: (lower_inclusive, upper_exclusive)}.
    Se None, usa ORDINAL_CLASSES de schema.py.

    ATENÇÃO: Mapeamento hipotético — confirmar com paper antes de usar
    em avaliação oficial do desafio IDA 2024.
    """
    if class_map is None:
        class_map = ORDINAL_CLASSES

    tte_arr = np.asarray(tte, dtype=float)
    events_arr = np.asarray(events, dtype=int)
    n_classes = len(class_map)
    result = np.full(len(tte_arr), n_classes - 1, dtype=int)

    for cls, (lo, hi) in sorted(class_map.items()):
        in_bucket = (tte_arr >= lo) & (tte_arr < hi) & (events_arr == 1)
        result[in_bucket] = cls

    return result


def fit_ordinal_classifier(
    X_train: pd.DataFrame | np.ndarray,
    y_train: np.ndarray,
    n_estimators: int = 100,
    max_depth: int | None = 10,
    seed: int = 42,
) -> RandomForestClassifier:
    """Ajusta RandomForestClassifier como benchmark ordinal."""
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    return model


def evaluate_ordinal(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_classes: int = 5,
) -> dict[str, object]:
    """Calcula métricas de avaliação para o classificador ordinal.

    Retorna: confusion_matrix, balanced_accuracy, macro_f1, maoe.
    """
    labels = list(range(n_classes))
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return {
        "confusion_matrix": cm.tolist(),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "maoe": float(mean_absolute_ordinal_error(np.asarray(y_true), np.asarray(y_pred))),
        "n": int(len(y_true)),
    }
