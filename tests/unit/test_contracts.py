"""Testes para src/scania_poc/contracts.py — validações sem Spark (pure Python)."""

from pathlib import Path

from src.scania_poc.contracts import load_contract, validate_required_columns

CONTRACT_PATH = Path("config/data_contract.yaml")


def test_load_contract_exists():
    contract = load_contract(CONTRACT_PATH)
    assert "files" in contract
    assert "train_tte" in contract["files"]
    assert "train_operational_readouts" in contract["files"]


def test_contract_train_tte_required_cols():
    contract = load_contract(CONTRACT_PATH)
    cols = list(contract["files"]["train_tte"]["required_columns"].keys())
    assert "vehicle_id" in cols
    assert "length_of_study_time_step" in cols
    assert "in_study_repair" in cols


def test_contract_allowed_values_in_study_repair():
    contract = load_contract(CONTRACT_PATH)
    spec = contract["files"]["train_tte"]["required_columns"]["in_study_repair"]
    assert set(spec["allowed_values"]) == {0, 1}


def test_contract_class_label_allowed_values():
    contract = load_contract(CONTRACT_PATH)
    spec = contract["files"]["validation_labels"]["required_columns"]["class_label"]
    assert set(spec["allowed_values"]) == {0, 1, 2, 3, 4}


class MockDF:
    """Imitação mínima de DataFrame para testar validações puras."""

    def __init__(self, columns: list[str]):
        self.columns = columns


def test_validate_required_columns_all_present():
    df = MockDF(["vehicle_id", "length_of_study_time_step", "in_study_repair"])
    missing = validate_required_columns(df, ["vehicle_id", "in_study_repair"])
    assert missing == []


def test_validate_required_columns_missing():
    df = MockDF(["vehicle_id"])
    missing = validate_required_columns(df, ["vehicle_id", "in_study_repair"])
    assert "in_study_repair" in missing
