"""Testes para survival.py, rul.py e ordinal.py (sem dados reais)."""

import numpy as np
import pytest

from src.scania_poc.rul import evaluate_rul, fit_rul_regressor
from src.scania_poc.ordinal import (
    bin_tte_to_classes,
    evaluate_ordinal,
    fit_ordinal_classifier,
)
from src.scania_poc.survival import fit_kaplan_meier


# --- RUL ---


def test_evaluate_rul_perfect():
    y = np.array([10.0, 20.0, 30.0])
    result = evaluate_rul(y, y)
    assert result["mae"] == pytest.approx(0.0)
    assert result["rmse"] == pytest.approx(0.0)


def test_evaluate_rul_with_events():
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([15.0, 20.0, 35.0])
    events = np.array([1, 0, 1])
    result = evaluate_rul(y_true, y_pred, events=events)
    # Apenas eventos 0 e 2 contribuem: |10-15|=5, |30-35|=5
    assert result["mae"] == pytest.approx(5.0)
    assert result["n"] == 2


def test_evaluate_rul_no_events():
    y_true = np.array([10.0, 20.0])
    y_pred = np.array([12.0, 22.0])
    events = np.array([0, 0])
    result = evaluate_rul(y_true, y_pred, events=events)
    assert np.isnan(result["mae"])
    assert result["n"] == 0


def test_fit_rul_regressor_basic():
    X = np.random.default_rng(42).normal(size=(100, 10))
    y = np.random.default_rng(42).uniform(50, 300, size=100)
    model = fit_rul_regressor(X, y, n_estimators=10)
    preds = model.predict(X[:5])
    assert len(preds) == 5


# --- Ordinal ---


def test_bin_tte_to_classes_all_censored():
    tte = np.array([100.0, 200.0, 300.0])
    events = np.array([0, 0, 0])
    classes = bin_tte_to_classes(tte, events)
    # Todos censurados → classe máxima (4)
    assert all(classes == 4)


def test_bin_tte_to_classes_event_large_tte():
    tte = np.array([200.0])
    events = np.array([1])
    classes = bin_tte_to_classes(tte, events)
    assert classes[0] == 4  # 200 > 48 → classe 4 (conforme hipótese)


def test_evaluate_ordinal_perfect():
    y = np.array([0, 1, 2, 3, 4])
    result = evaluate_ordinal(y, y)
    assert result["balanced_accuracy"] == pytest.approx(1.0)
    assert result["maoe"] == pytest.approx(0.0)
    assert result["macro_f1"] == pytest.approx(1.0)


def test_evaluate_ordinal_off_by_one():
    y_true = np.array([0, 1, 2, 3])
    y_pred = np.array([1, 2, 3, 4])
    result = evaluate_ordinal(y_true, y_pred)
    assert result["maoe"] == pytest.approx(1.0)


def test_fit_ordinal_classifier_basic():
    rng = np.random.default_rng(42)
    X = rng.normal(size=(200, 10))
    y = rng.integers(0, 5, size=200)
    model = fit_ordinal_classifier(X, y, n_estimators=10)
    preds = model.predict(X[:10])
    assert len(preds) == 10
    assert all(0 <= p <= 4 for p in preds)


# --- Survival (KM básico) ---


def test_kaplan_meier_fit():
    durations = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
    events = np.array([1, 0, 1, 0, 1, 1, 0, 1, 0, 1])
    kmf = fit_kaplan_meier(durations, events)
    sf = kmf.survival_function_
    assert sf is not None
    assert sf.iloc[0, 0] == pytest.approx(1.0)
    assert sf.iloc[-1, 0] >= 0.0
