"""Path and identifier helpers for Databricks Free Edition workspaces."""

from __future__ import annotations

import re

OFFICIAL_RAW_FILES = (
    "train_tte.csv",
    "train_operational_readouts.csv",
    "train_specifications.csv",
    "validation_labels.csv",
    "validation_operational_readouts.csv",
    "validation_specifications.csv",
    "test_operational_readouts.csv",
    "test_specifications.csv",
)

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_raw_volume_path(path: str) -> str:
    """Validate an absolute UC volume path ending in the raw input directory."""
    normalized = path.rstrip("/")
    parts = normalized.split("/")
    if (
        len(parts) != 6
        or parts[0] != ""
        or parts[1] != "Volumes"
        or any(not _IDENTIFIER.fullmatch(part) for part in parts[2:5])
        or parts[5] != "raw"
    ):
        raise ValueError(
            "RAW_VOLUME_PATH deve ter o formato /Volumes/<catalog>/<schema>/<volume>/raw"
        )
    return normalized


def validate_data_schema(data_schema: str) -> str:
    """Validate a two-part Unity Catalog schema identifier."""
    parts = data_schema.split(".")
    if len(parts) != 2 or any(not _IDENTIFIER.fullmatch(part) for part in parts):
        raise ValueError("DATA_SCHEMA deve ter o formato <catalog>.<schema>")
    return data_schema


def build_volume_raw_path(raw_volume_path: str, filename: str) -> str:
    """Resolve one of the eight official source files under the raw volume path."""
    root = validate_raw_volume_path(raw_volume_path)
    if filename not in OFFICIAL_RAW_FILES:
        raise ValueError(f"Arquivo fora do conjunto oficial: {filename}")
    return f"{root}/{filename}"


def select_raw_files(source_file: str | None = None) -> list[str]:
    """Select all official inputs or one official file for an ingestion smoke test."""
    if source_file is None or not source_file.strip():
        return list(OFFICIAL_RAW_FILES)
    if source_file not in OFFICIAL_RAW_FILES:
        raise ValueError(f"Arquivo fora do conjunto oficial: {source_file}")
    return [source_file]


def qualified_table_name(data_schema: str, layer: str, artifact: str) -> str:
    """Build a safe three-part Unity Catalog table identifier."""
    schema = validate_data_schema(data_schema)
    if layer not in {"bronze", "silver", "gold"}:
        raise ValueError(f"Camada desconhecida: {layer}")
    if not _IDENTIFIER.fullmatch(artifact):
        raise ValueError(f"Nome de artefato inválido: {artifact}")
    return f"{schema}.{layer}_{artifact}"
