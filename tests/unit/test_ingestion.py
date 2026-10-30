"""Tests for managed-volume paths and source identity."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.scania_poc.config import (
    OFFICIAL_RAW_FILES,
    build_volume_raw_path,
    qualified_table_name,
    select_raw_files,
    validate_data_schema,
    validate_raw_volume_path,
)
from src.scania_poc.ingestion import sha256_file


@pytest.fixture
def workspace_tmp_path():
    """Create a temporary directory under the writable project workspace."""
    with TemporaryDirectory(
        prefix=".test-ingestion-", dir=Path(__file__).resolve().parents[2]
    ) as directory:
        yield Path(directory)


def test_validate_raw_volume_path_normalizes_trailing_slash():
    assert validate_raw_volume_path("/Volumes/main/default/component_x/raw/") == (
        "/Volumes/main/default/component_x/raw"
    )


@pytest.mark.parametrize(
    "path",
    [
        "",
        "s3://bucket/raw",
        "/Volumes/main/default/raw",
        "/Volumes/main/default/component_x",
        "/Volumes/main/default/component_x/raw/nested",
    ],
)
def test_validate_raw_volume_path_rejects_invalid_paths(path):
    with pytest.raises(ValueError, match="RAW_VOLUME_PATH"):
        validate_raw_volume_path(path)


def test_build_volume_raw_path_accepts_only_official_files():
    path = build_volume_raw_path("/Volumes/main/default/component_x/raw", "train_tte.csv")
    assert path == "/Volumes/main/default/component_x/raw/train_tte.csv"
    assert len(OFFICIAL_RAW_FILES) == 8


def test_select_raw_files_defaults_to_the_eight_official_sources():
    assert select_raw_files() == list(OFFICIAL_RAW_FILES)
    assert select_raw_files("") == list(OFFICIAL_RAW_FILES)


def test_select_raw_files_supports_single_file_smoke_test():
    assert select_raw_files("train_tte.csv") == ["train_tte.csv"]


def test_select_raw_files_rejects_unknown_file():
    with pytest.raises(ValueError, match="conjunto oficial"):
        select_raw_files("test_labels.csv")


@pytest.mark.parametrize("filename", ["test_labels.csv", "../train_tte.csv", "notes.txt"])
def test_build_volume_raw_path_rejects_non_official_files(filename):
    with pytest.raises(ValueError, match="conjunto oficial"):
        build_volume_raw_path("/Volumes/main/default/component_x/raw", filename)


def test_validate_data_schema_and_qualified_table_name():
    assert validate_data_schema("main.default") == "main.default"
    assert qualified_table_name("main.default", "gold", "train_fit") == (
        "main.default.gold_train_fit"
    )


@pytest.mark.parametrize("schema", ["", "main", "main.default.extra", "bad-name.schema"])
def test_validate_data_schema_rejects_unsafe_names(schema):
    with pytest.raises(ValueError, match="DATA_SCHEMA"):
        validate_data_schema(schema)


def test_sha256_file_is_deterministic_and_detects_changed_content(
    workspace_tmp_path: Path,
):
    source = workspace_tmp_path / "small.csv"
    source.write_bytes(b"vehicle_id,time_step\n1,0.0\n")
    first = sha256_file(source, chunk_size=4)
    assert first == sha256_file(source, chunk_size=7)
    source.write_bytes(b"vehicle_id,time_step\n1,1.0\n")
    assert sha256_file(source) != first


def test_sha256_file_errors_for_missing_source(workspace_tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="não encontrado"):
        sha256_file(workspace_tmp_path / "missing.csv")


def test_sha256_file_rejects_nonpositive_chunk_size(workspace_tmp_path: Path):
    source = workspace_tmp_path / "small.csv"
    source.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="chunk_size"):
        sha256_file(source, chunk_size=0)
