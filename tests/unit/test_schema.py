"""Testes para src/scania_poc/schema.py."""

from src.scania_poc.schema import (
    EVENT_COL,
    FEATURE_COLS,
    N_FEATURE_COLS,
    N_ORDINAL_CLASSES,
    ORDINAL_CLASSES,
    SPEC_COLS,
    TTE_COL,
    VEHICLE_ID_COL,
)


def test_feature_cols_count():
    assert len(FEATURE_COLS) == N_FEATURE_COLS


def test_feature_cols_no_duplicates():
    assert len(FEATURE_COLS) == len(set(FEATURE_COLS))


def test_ordinal_classes_count():
    assert len(ORDINAL_CLASSES) == N_ORDINAL_CLASSES


def test_ordinal_classes_contiguous():
    for i in range(len(ORDINAL_CLASSES) - 1):
        assert ORDINAL_CLASSES[i][1] == ORDINAL_CLASSES[i + 1][0]


def test_spec_cols_count():
    assert len(SPEC_COLS) == 8


def test_key_cols_defined():
    assert VEHICLE_ID_COL == "vehicle_id"
    assert TTE_COL == "length_of_study_time_step"
    assert EVENT_COL == "in_study_repair"
