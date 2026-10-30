"""Leakage-safe snapshot selection and residual target construction."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Iterable, Mapping
from typing import Any


def select_snapshot_records(
    readouts: Iterable[Mapping[str, Any]],
    follow_up: Mapping[Any, tuple[float, int]],
    *,
    vehicle_id_col: str = "vehicle_id",
    time_step_col: str = "time_step",
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Select one deterministic uniformly hashed eligible readout per vehicle.

    ``follow_up`` maps vehicle IDs to (end_time, event_observed). Readouts at
    or after the event/censor boundary are excluded. Hash ordering makes the
    selected observation independent of input row order and partitioning.
    """
    candidates: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    seen_keys: set[tuple[Any, float]] = set()
    for source_row in readouts:
        row = dict(source_row)
        vehicle_id = row[vehicle_id_col]
        if vehicle_id not in follow_up:
            continue
        end_time, event_observed = follow_up[vehicle_id]
        time_step = float(row[time_step_col])
        if event_observed not in (0, 1):
            raise ValueError(f"event_observed inválido para veículo {vehicle_id}")
        key = (vehicle_id, time_step)
        if key in seen_keys:
            raise ValueError(f"Leitura duplicada para vehicle_id/time_step: {key}")
        seen_keys.add(key)
        if time_step < float(end_time):
            candidates[vehicle_id].append(row)

    selected = []
    for vehicle_id, rows in candidates.items():
        rows.sort(
            key=lambda row: hashlib.blake2b(
                f"{seed}:{vehicle_id}:{float(row[time_step_col]):.17g}".encode(),
                digest_size=16,
            ).digest()
        )
        end_time, event_observed = follow_up[vehicle_id]
        row = rows[0]
        prediction_time = float(row[time_step_col])
        row["prediction_time"] = prediction_time
        row["residual_time"] = float(end_time) - prediction_time
        row["event_observed"] = int(event_observed)
        selected.append(row)
    selected.sort(key=lambda row: str(row[vehicle_id_col]))
    return selected


def build_survival_snapshots(
    readouts_df: Any,
    tte_df: Any,
    *,
    vehicle_id_col: str = "vehicle_id",
    time_step_col: str = "time_step",
    tte_col: str = "length_of_study_time_step",
    event_col: str = "in_study_repair",
    seed: int = 42,
) -> Any:
    """Spark implementation of one leakage-safe snapshot per training vehicle."""
    import pyspark.sql.functions as F  # noqa: PLC0415
    from pyspark.sql.window import Window  # noqa: PLC0415

    target_metadata = [
        col for col in ("_tte_source_uri", "_tte_source_version") if col in tte_df.columns
    ]
    targets = tte_df.select(
        vehicle_id_col,
        F.col(tte_col).cast("double").alias("_follow_up_end"),
        F.col(event_col).cast("int").alias("event_observed"),
        *target_metadata,
    )
    if targets.groupBy(vehicle_id_col).count().filter(F.col("count") != 1).limit(1).count():
        raise ValueError("TTE deve conter exatamente uma linha por veículo")

    joined = readouts_df.join(targets, on=vehicle_id_col, how="inner").filter(
        F.col(time_step_col) < F.col("_follow_up_end")
    )
    if joined.filter(~F.col("event_observed").isin(0, 1)).limit(1).count():
        raise ValueError("in_study_repair deve conter somente 0 ou 1")

    ordering = F.xxhash64(F.col(vehicle_id_col), F.lit(seed), F.col(time_step_col))
    window = Window.partitionBy(vehicle_id_col).orderBy(ordering, F.col(time_step_col))
    selected = (
        joined.withColumn("_snapshot_rank", F.row_number().over(window))
        .filter(F.col("_snapshot_rank") == 1)
        .withColumnRenamed(time_step_col, "prediction_time")
        .withColumn("residual_time", F.col("_follow_up_end") - F.col("prediction_time"))
        .drop("_snapshot_rank", "_follow_up_end")
    )
    return selected
