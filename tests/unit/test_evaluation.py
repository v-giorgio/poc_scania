"""Tests for official ordinal and regression evaluation metrics."""

import numpy as np
import pytest

from src.scania_poc.evaluation import mean_absolute_ordinal_error, ordinal_total_cost


def test_official_cost_perfect_predictions():
    y = np.arange(5)
    assert ordinal_total_cost(y, y) == 0


@pytest.mark.parametrize(
    ("actual", "predicted", "expected"),
    [(0, 4, 10), (1, 0, 200), (2, 1, 200), (3, 2, 200), (4, 0, 500)],
)
def test_official_cost_matrix(actual, predicted, expected):
    assert ordinal_total_cost(np.array([actual]), np.array([predicted])) == expected


def test_official_cost_sums_multiple_predictions():
    assert ordinal_total_cost(np.array([0, 4]), np.array([1, 3])) == 207


def test_ordinal_cost_rejects_invalid_labels_and_shapes():
    with pytest.raises(ValueError, match="classes entre 0 e 4"):
        ordinal_total_cost(np.array([5]), np.array([0]))
    with pytest.raises(ValueError, match="mesmo formato"):
        ordinal_total_cost(np.array([0, 1]), np.array([0]))


def test_maoe_perfect():
    y = np.arange(5)
    assert mean_absolute_ordinal_error(y, y) == pytest.approx(0.0)


def test_maoe_off_by_one():
    assert mean_absolute_ordinal_error(np.array([0, 1, 2]), np.array([1, 2, 3])) == 1.0
