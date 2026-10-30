"""Testes para src/scania_poc/evaluation.py."""

import numpy as np
import pytest

from src.scania_poc.evaluation import classification_cost, mean_absolute_ordinal_error


def test_cost_all_correct():
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 0, 1, 1])
    result = classification_cost(y_true, y_pred)
    assert result["false_positives"] == 0
    assert result["false_negatives"] == 0
    assert result["total_cost"] == 0


def test_cost_false_negative_weight():
    y_true = np.array([1])
    y_pred = np.array([0])
    result = classification_cost(y_true, y_pred)
    assert result["false_negatives"] == 1
    assert result["total_cost"] == 500


def test_cost_false_positive_weight():
    y_true = np.array([0])
    y_pred = np.array([1])
    result = classification_cost(y_true, y_pred)
    assert result["false_positives"] == 1
    assert result["total_cost"] == 10


def test_maoe_perfect():
    y_true = np.array([0, 1, 2, 3, 4])
    y_pred = np.array([0, 1, 2, 3, 4])
    assert mean_absolute_ordinal_error(y_true, y_pred) == pytest.approx(0.0)


def test_maoe_off_by_one():
    y_true = np.array([0, 1, 2])
    y_pred = np.array([1, 2, 3])
    assert mean_absolute_ordinal_error(y_true, y_pred) == pytest.approx(1.0)
