"""Testes para survival.py, rul.py e ordinal.py (sem dados reais)."""

import numpy as np
import pytest

from src.scania_poc.features import select_snapshot_records
from src.scania_poc.ordinal import (
    bin_tte_to_classes,
    evaluate_ordinal,
    fit_ordinal_classifier,
)
from src.scania_poc.rul import evaluate_rul, fit_rul_regressor
from src.scania_poc.schema import UNKNOWN_ORDINAL_CLASS
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


def test_bin_residual_time_classes_follow_official_order():
    residual = np.array([60.0, 36.0, 18.0, 9.0, 3.0])
    events = np.ones(5, dtype=int)
    assert bin_tte_to_classes(residual, events).tolist() == [0, 1, 2, 3, 4]


def test_ordinal_censoring_requires_full_horizon():
    residual = np.array([50.0, 48.0, 47.0, 47.0])
    events = np.array([0, 0, 0, 1])
    classes = bin_tte_to_classes(residual, events)
    assert classes.tolist() == [0, UNKNOWN_ORDINAL_CLASS, UNKNOWN_ORDINAL_CLASS, 1]


def test_ordinal_exact_boundaries_remain_unknown():
    residual = np.array([48.0, 24.0, 12.0, 6.0, 0.0])
    events = np.ones(5, dtype=int)
    assert (bin_tte_to_classes(residual, events) == UNKNOWN_ORDINAL_CLASS).all()


def test_ordinal_rejects_mismatched_arrays():
    with pytest.raises(ValueError, match="mesmo formato"):
        bin_tte_to_classes(np.array([2.0]), np.array([1, 0]))


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


def test_snapshot_selection_is_deterministic_and_excludes_post_event_rows():
    readouts = [
        {"vehicle_id": 1, "time_step": 1.0, "feature": 10},
        {"vehicle_id": 1, "time_step": 2.0, "feature": 20},
        {"vehicle_id": 1, "time_step": 3.0, "feature": 30},
        {"vehicle_id": 2, "time_step": 1.0, "feature": 40},
        {"vehicle_id": 2, "time_step": 4.0, "feature": 50},
    ]
    follow_up = {1: (3.0, 1), 2: (4.0, 0)}
    first = select_snapshot_records(readouts, follow_up, seed=91)
    reordered = select_snapshot_records(reversed(readouts), follow_up, seed=91)
    with_post_event_perturbation = select_snapshot_records(
        readouts + [{"vehicle_id": 1, "time_step": 100.0, "feature": -999}],
        follow_up,
        seed=91,
    )
    assert first == reordered
    assert first == with_post_event_perturbation
    assert {row["vehicle_id"] for row in first} == {1, 2}
    assert all(row["time_step"] < follow_up[row["vehicle_id"]][0] for row in first)
    assert all("residual_time" in row and "event_observed" in row for row in first)


def test_snapshot_selection_counts_vehicles_without_eligible_readouts_by_exclusion():
    selected = select_snapshot_records(
        [{"vehicle_id": 1, "time_step": 5.0}],
        {1: (5.0, 1), 2: (10.0, 0)},
    )
    assert selected == []


def test_snapshot_selection_rejects_duplicate_vehicle_time_keys():
    rows = [
        {"vehicle_id": 1, "time_step": 1.0},
        {"vehicle_id": 1, "time_step": 1.0},
    ]
    with pytest.raises(ValueError, match="Leitura duplicada"):
        select_snapshot_records(rows, {1: (3.0, 1)})
