"""Tests for train-only feature encoding and leakage-safe alignment."""

import numpy as np
import pandas as pd
import pytest

from src.scania_poc.modeling import prepare_design_matrices


def test_one_hot_vocabulary_is_learned_from_training_only():
    train = pd.DataFrame({"reading": [1.0, 2.0], "spec_idx": [0.0, 1.0]})
    evaluation = pd.DataFrame({"reading": [3.0], "spec_idx": [2.0]})
    train_x, evaluation_x = prepare_design_matrices([train, evaluation], ["reading"], ["spec_idx"])
    assert list(train_x.columns) == list(evaluation_x.columns)
    assert not any("2.0" in col for col in train_x.columns)
    assert evaluation_x.filter(like="spec_idx").to_numpy().sum() == 0


def test_design_matrix_rejects_unimputed_nonfinite_numeric_values():
    train = pd.DataFrame({"reading": [1.0, np.nan], "spec_idx": [0.0, 1.0]})
    with pytest.raises(ValueError, match="imputadas e finitas"):
        prepare_design_matrices([train], ["reading"], ["spec_idx"])


def test_design_matrix_requires_all_columns():
    train = pd.DataFrame({"reading": [1.0]})
    with pytest.raises(ValueError, match="colunas de features ausentes"):
        prepare_design_matrices([train], ["reading"], ["spec_idx"])
