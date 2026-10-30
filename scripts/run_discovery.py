"""Stream official CSV files and write aggregate-only discovery Markdown."""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter
from datetime import date
from pathlib import Path

OFFICIAL_FILES = (
    "train_tte.csv",
    "train_operational_readouts.csv",
    "train_specifications.csv",
    "validation_labels.csv",
    "validation_operational_readouts.csv",
    "validation_specifications.csv",
    "test_operational_readouts.csv",
    "test_specifications.csv",
)
NULL_TOKENS = {"", "na", "nan", "null", "none"}


def percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * quantile
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return ordered[low]
    return ordered[low] + (ordered[high] - ordered[low]) * (index - low)


def profile_csv(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Arquivo obrigatório ausente: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        row_count = 0
        nulls = Counter()
        identifiers: set[str] = set()
        duplicate_ids = 0
        class_counts = Counter()
        events = Counter()
        durations: list[float] = []
        spec_values: dict[str, set[str]] = {col: set() for col in columns if col.startswith("Spec_")}
        per_vehicle: dict[str, list[float]] = {}
        seen_readout_keys: set[tuple[str, str]] = set()
        duplicate_readout_keys = 0
        global_time_min = math.inf
        global_time_max = -math.inf

        for row in reader:
            row_count += 1
            for column in columns:
                value = (row.get(column) or "").strip()
                if value.casefold() in NULL_TOKENS:
                    nulls[column] += 1
                if column.startswith("Spec_") and value:
                    spec_values[column].add(value)

            vehicle_id = (row.get("vehicle_id") or "").strip()
            if vehicle_id and "vehicle_id" in columns:
                if "time_step" not in columns and vehicle_id in identifiers:
                    duplicate_ids += 1
                identifiers.add(vehicle_id)

            if "class_label" in columns:
                class_counts[(row.get("class_label") or "").strip()] += 1
            if "in_study_repair" in columns:
                events[(row.get("in_study_repair") or "").strip()] += 1
            if "length_of_study_time_step" in columns:
                try:
                    durations.append(float(row["length_of_study_time_step"]))
                except (TypeError, ValueError):
                    pass
            if "time_step" in columns:
                try:
                    time_step = float(row["time_step"])
                    global_time_min = min(global_time_min, time_step)
                    global_time_max = max(global_time_max, time_step)
                    stats = per_vehicle.setdefault(vehicle_id, [0.0, math.inf, -math.inf])
                    stats[0] += 1
                    stats[1] = min(stats[1], time_step)
                    stats[2] = max(stats[2], time_step)
                    key = (vehicle_id, row["time_step"])
                    if key in seen_readout_keys:
                        duplicate_readout_keys += 1
                    seen_readout_keys.add(key)
                except (TypeError, ValueError):
                    pass

    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "rows": row_count,
        "columns": columns,
        "null_cells": sum(nulls.values()),
        "null_by_column": dict(nulls),
        "unique_vehicles": len(identifiers),
        "_vehicle_ids": identifiers,
        "duplicate_vehicle_ids": duplicate_ids,
        "duplicate_readout_keys": duplicate_readout_keys,
        "class_counts": dict(class_counts),
        "event_counts": dict(events),
        "durations": durations,
        "spec_values": {col: sorted(values) for col, values in spec_values.items()},
        "readouts_per_vehicle": [int(values[0]) for values in per_vehicle.values()],
        "time_min": None if global_time_min == math.inf else global_time_min,
        "time_max": None if global_time_max == -math.inf else global_time_max,
    }


def render_report(profiles: list[dict], data_dir: Path) -> str:
    lines = [
        "# Data Discovery — SCANIA Component X (IDA 2024)",
        "",
        f"> Relatório agregado recalculado em {date.today().isoformat()} por `scripts/run_discovery.py`.",
        "> Nenhum registro bruto é escrito no relatório. Tipos são os nomes originais do CSV; parsing validado separadamente.",
        "",
        "## Inventário oficial",
        "",
        "| Arquivo | Linhas | Colunas | Veículos | Células ausentes | Bytes | Chaves duplicadas |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for item in profiles:
        lines.append(
            f"| `{item['file']}` | {item['rows']:,} | {len(item['columns'])} | "
            f"{item['unique_vehicles']:,} | {item['null_cells']:,} | {item['bytes']:,} | "
            f"{item['duplicate_readout_keys'] if item['columns'] and 'time_step' in item['columns'] else item['duplicate_vehicle_ids']:,} |"
        )

    profile_by_name = {item["file"]: item for item in profiles}
    train_ids = profile_by_name["train_tte.csv"]["_vehicle_ids"]
    validation_ids = profile_by_name["validation_labels.csv"]["_vehicle_ids"]
    test_ids = profile_by_name["test_specifications.csv"]["_vehicle_ids"]
    overlaps = {
        "train/validation": train_ids & validation_ids,
        "train/test": train_ids & test_ids,
        "validation/test": validation_ids & test_ids,
    }
    for label, ids in overlaps.items():
        if ids:
            raise ValueError(f"Sobreposição de vehicle_id {label}: {len(ids)}")
    for split, anchor in (
        ("train", train_ids),
        ("validation", validation_ids),
        ("test", test_ids),
    ):
        candidates = [item for item in profiles if item["file"].startswith(f"{split}_")]
        if any(item["_vehicle_ids"] != anchor for item in candidates):
            raise ValueError(f"vehicle_id divergente entre arquivos de {split}")
    lines += [
        "",
        "## Integridade de chaves",
        "",
        "- IDs por veículo coincidem entre os arquivos de cada partição.",
        "- Sobreposição train/validation, train/test e validation/test: 0.",
        "- Leituras operacionais verificadas por chave composta `(vehicle_id, time_step)`.",
    ]

    tte = next(item for item in profiles if item["file"] == "train_tte.csv")
    durations = tte["durations"]
    events = int(tte["event_counts"].get("1", 0))
    censored = int(tte["event_counts"].get("0", 0))
    lines += [
        "",
        "## TTE de treino",
        "",
        f"- Eventos observados: {events:,}; censurados: {censored:,}; taxa de evento: {events / max(1, len(durations)):.2%}.",
        f"- Duração observada: min={min(durations):.3f}, P25={percentile(durations, .25):.3f}, "
        f"mediana={percentile(durations, .5):.3f}, P75={percentile(durations, .75):.3f}, max={max(durations):.3f}.",
        "- Unidade: `time_step` anonimizado; não converter para calendário ou distância.",
    ]

    for name in ("train_operational_readouts.csv", "validation_operational_readouts.csv", "test_operational_readouts.csv"):
        item = next(profile for profile in profiles if profile["file"] == name)
        counts = item["readouts_per_vehicle"]
        lines += [
            "",
            f"## `{name}`",
            "",
            f"- Veículos: {item['unique_vehicles']:,}; time_step observado: {item['time_min']}–{item['time_max']}.",
            f"- Leituras por veículo: min={min(counts)}, mediana={percentile([float(x) for x in counts], .5):.1f}, max={max(counts)}.",
            f"- Chaves duplicadas `(vehicle_id, time_step)`: {item['duplicate_readout_keys']:,}.",
            f"- Features com ausências: {sum(1 for col in item['columns'] if item['null_by_column'].get(col, 0) > 0)}.",
        ]

    validation = next(item for item in profiles if item["file"] == "validation_labels.csv")
    lines += ["", "## Rótulos oficiais de validação", ""]
    for label, count in sorted(validation["class_counts"].items()):
        lines.append(f"- Classe {label}: {count:,} ({count / max(1, validation['rows']):.2%}).")
    lines += [
        "",
        "O pacote oficial não contém `test_labels.csv`; arquivos locais com esse nome não são lidos por este relatório nem pelo pipeline.",
        "A semântica de evento e das janelas ordinais está documentada em `docs/data-dictionary.md`; inclusão das fronteiras continua não especificada e os rótulos derivados nesses pontos ficam desconhecidos.",
        "",
        f"Diretório inspecionado: `{data_dir}` (somente leitura).",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("dataset_local"))
    parser.add_argument("--output", type=Path, default=Path("docs/data-discovery.md"))
    args = parser.parse_args()
    profiles = [profile_csv(args.data_dir / filename) for filename in OFFICIAL_FILES]
    args.output.write_text(render_report(profiles, args.data_dir), encoding="utf-8")
    print(f"Discovery agregada gravada em {args.output}; {len(profiles)} arquivos oficiais perfilados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
