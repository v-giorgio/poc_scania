"""Testes para src/scania_poc/validators.py."""

import pytest

from src.scania_poc.validators import missing_rate, validate_event_col, validate_values


def test_validate_values_valid():
    assert validate_values({"pos", "neg"}, {"pos", "neg"}) is True


def test_validate_values_invalid():
    assert validate_values({"pos", "neg", "unknown"}, {"pos", "neg"}) is False


def test_missing_rate_zero_total():
    assert missing_rate(0, 0) == 0.0


def test_missing_rate_normal():
    assert missing_rate(10, 100) == pytest.approx(0.1)


def test_validate_event_col_valid():
    assert validate_event_col({0, 1}) is True


def test_validate_event_col_invalid():
    assert validate_event_col({0, 1, 2}) is False
