"""Managed-volume source identity and idempotent CSV-to-Bronze ingestion."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from src.scania_poc.config import build_volume_raw_path, qualified_table_name


def sha256_file(source_path: str | Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    """Hash a source file in bounded memory, raising if it is missing or invalid."""
    path = Path(source_path)
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo Raw não encontrado: {path}")
    if chunk_size < 1:
        raise ValueError("chunk_size deve ser positivo")

    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ingest_volume_csv_to_bronze(
    spark: Any,
    raw_volume_path: str,
    filename: str,
    data_schema: str,
    *,
    header: bool = True,
    delimiter: str = ",",
) -> tuple[int, str, str]:
    """Read one official CSV from a managed volume and overwrite its Bronze table.

    The raw file remains untouched. Source SHA-256 is calculated in chunks so
    it can be used as a content identity without loading the file into memory.
    """
    source_uri = build_volume_raw_path(raw_volume_path, filename)
    version = sha256_file(source_uri)
    table_name = qualified_table_name(data_schema, "bronze", Path(filename).stem)

    import pyspark.sql.functions as F  # noqa: PLC0415

    source = spark.read.csv(
        source_uri,
        header=header,
        sep=delimiter,
        inferSchema=False,
    )
    bronze = (
        source.withColumn("_source_uri", F.lit(source_uri))
        .withColumn("_source_version", F.lit(version))
        .withColumn("_source_size_bytes", F.lit(Path(source_uri).stat().st_size))
        .withColumn("_ingested_at", F.current_timestamp())
    )
    (
        bronze.write.format("delta")
        .mode("overwrite")
        .option("overwriteSchema", "true")
        .saveAsTable(table_name)
    )
    row_count = spark.read.table(table_name).count()
    if row_count == 0:
        raise ValueError(f"Arquivo Raw não produziu linhas Bronze: {source_uri}")
    return row_count, table_name, version
