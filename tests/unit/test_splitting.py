"""Testes para src/scania_poc/splitting.py."""

import pytest

from src.scania_poc.splitting import _assert_no_overlap, split_by_vehicle


def _make_ids(n: int) -> tuple[list[int], list[int]]:
    ids = list(range(n))
    flags = [i % 2 for i in ids]
    return ids, flags


def test_split_no_overlap_small():
    ids, flags = _make_ids(100)
    train, val, test = split_by_vehicle(ids, flags)
    _assert_no_overlap(train, val, test)


def test_split_covers_all_vehicles():
    ids, flags = _make_ids(200)
    train, val, test = split_by_vehicle(ids, flags)
    assert set(train) | set(val) | set(test) == set(ids)


def test_split_ratios_approximate():
    ids, flags = _make_ids(1000)
    train, val, test = split_by_vehicle(ids, flags, ratios=(0.70, 0.15, 0.15))
    assert 0.65 <= len(train) / len(ids) <= 0.75
    assert 0.10 <= len(val) / len(ids) <= 0.20
    assert 0.10 <= len(test) / len(ids) <= 0.20


def test_split_reproducible():
    ids, flags = _make_ids(500)
    train1, val1, test1 = split_by_vehicle(ids, flags, seed=42)
    train2, val2, test2 = split_by_vehicle(ids, flags, seed=42)
    assert train1 == train2
    assert val1 == val2
    assert test1 == test2


def test_split_different_seeds():
    ids, flags = _make_ids(500)
    train1, _, _ = split_by_vehicle(ids, flags, seed=1)
    train2, _, _ = split_by_vehicle(ids, flags, seed=2)
    assert train1 != train2


def test_split_invalid_ratios():
    ids, flags = _make_ids(100)
    with pytest.raises(ValueError, match="Ratios devem somar"):
        split_by_vehicle(ids, flags, ratios=(0.5, 0.5, 0.5))


def test_split_mismatched_lengths():
    with pytest.raises(ValueError, match="mesmo tamanho"):
        split_by_vehicle([1, 2, 3], [0, 1])


def test_assert_no_overlap_raises():
    with pytest.raises(AssertionError, match="train/val"):
        _assert_no_overlap([1, 2], [2, 3], [4, 5])


def test_assert_no_overlap_ok():
    _assert_no_overlap([1, 2], [3, 4], [5, 6])
