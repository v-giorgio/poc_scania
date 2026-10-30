"""Tests for IPCW survival scoring."""

import numpy as np
import pandas as pd
import pytest

from src.scania_poc.survival import compute_integrated_brier_score, supported_brier_times


class FixedSurvivalModel:
    def predict_survival_function(self, df, times):
        values = np.full((len(times), len(df)), 0.5)
        return pd.DataFrame(values, index=times, columns=df.index)


def test_ipcw_brier_uses_training_censoring_reference():
    training = pd.DataFrame({"duration": [1.0, 2.0, 3.0, 4.0], "event": [1, 0, 1, 1]})
    evaluation = pd.DataFrame({"duration": [1.5, 2.5, 3.5], "event": [1, 0, 1]})
    score = compute_integrated_brier_score(
        FixedSurvivalModel(),
        evaluation,
        "duration",
        "event",
        times=np.array([1.0, 2.0, 3.0]),
        censoring_reference_df=training,
    )
    assert np.isfinite(score)
    assert 0.0 <= score <= 1.0


def test_ipcw_brier_requires_train_reference():
    data = pd.DataFrame({"duration": [1.0, 2.0], "event": [1, 0]})
    with pytest.raises(ValueError, match="conjunto de treino"):
        compute_integrated_brier_score(
            FixedSurvivalModel(), data, "duration", "event", times=np.array([1.0, 2.0])
        )


def test_ipcw_brier_stops_outside_censoring_support():
    training = pd.DataFrame({"duration": [1.0, 1.0], "event": [0, 0]})
    evaluation = pd.DataFrame({"duration": [1.0, 2.0], "event": [1, 0]})
    with pytest.raises(ValueError, match="fora do suporte"):
        compute_integrated_brier_score(
            FixedSurvivalModel(),
            evaluation,
            "duration",
            "event",
            times=np.array([1.0, 2.0]),
            censoring_reference_df=training,
        )


def test_supported_brier_times_are_selected_from_train_support():
    training = pd.DataFrame({"duration": [1.0, 2.0, 3.0, 4.0], "event": [1, 0, 1, 1]})
    times = supported_brier_times(training, "duration", "event")
    assert len(times) >= 2
    assert np.all(np.diff(times) > 0)


def test_supported_brier_times_fail_when_support_is_insufficient():
    training = pd.DataFrame({"duration": [1.0, 1.0], "event": [0, 0]})
    with pytest.raises(ValueError, match="Menos de dois horizontes"):
        supported_brier_times(training, "duration", "event")
