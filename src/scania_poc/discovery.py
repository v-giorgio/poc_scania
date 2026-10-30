"""Funções de inspeção e discovery do dataset SCANIA Component X.

Projetadas para rodar em PySpark (Databricks). Cada função retorna
estruturas simples para que os resultados sejam facilmente logados
ou convertidos em documentação.
"""

import pyspark.sql.functions as F
from pyspark.sql import DataFrame


def compute_null_rates(df: DataFrame) -> dict[str, float]:
    """Retorna taxa de nulos por coluna (0.0 a 1.0)."""
    n = df.count()
    if n == 0:
        return {c: 0.0 for c in df.columns}
    agg_exprs = [F.sum(F.col(c).isNull().cast("int")).alias(c) for c in df.columns]
    row = df.select(agg_exprs).collect()[0]
    return {c: row[c] / n for c in df.columns}


def describe_event_distribution(tte_df: DataFrame, event_col: str, tte_col: str) -> dict:
    """Retorna distribuição de eventos e censuras, mais estatísticas de TTE."""
    total = tte_df.count()
    events = tte_df.filter(F.col(event_col) == 1).count()
    censored = total - events

    tte_stats = tte_df.select(
        F.min(tte_col).alias("min"),
        F.expr(f"percentile({tte_col}, 0.25)").alias("p25"),
        F.median(tte_col).alias("median"),
        F.expr(f"percentile({tte_col}, 0.75)").alias("p75"),
        F.max(tte_col).alias("max"),
    ).collect()[0]

    return {
        "total_vehicles": total,
        "n_events": events,
        "n_censored": censored,
        "event_rate": events / total if total > 0 else 0.0,
        "tte_min": float(tte_stats["min"]),
        "tte_p25": float(tte_stats["p25"]),
        "tte_median": float(tte_stats["median"]),
        "tte_p75": float(tte_stats["p75"]),
        "tte_max": float(tte_stats["max"]),
    }


def describe_readouts_structure(readouts_df: DataFrame, vehicle_col: str, time_col: str) -> dict:
    """Descreve estrutura temporal do dataset de leituras operacionais."""
    total_rows = readouts_df.count()
    n_vehicles = readouts_df.select(vehicle_col).distinct().count()

    per_vehicle = readouts_df.groupBy(vehicle_col).agg(
        F.count("*").alias("n_readouts"),
        F.min(time_col).alias("t_min"),
        F.max(time_col).alias("t_max"),
    )

    stats = per_vehicle.select(
        F.min("n_readouts").alias("readouts_min"),
        F.expr("percentile(n_readouts, 0.5)").alias("readouts_median"),
        F.max("n_readouts").alias("readouts_max"),
        F.min("t_min").alias("ts_global_min"),
        F.max("t_max").alias("ts_global_max"),
    ).collect()[0]

    return {
        "total_rows": total_rows,
        "n_vehicles": n_vehicles,
        "readouts_per_vehicle_min": int(stats["readouts_min"]),
        "readouts_per_vehicle_median": float(stats["readouts_median"]),
        "readouts_per_vehicle_max": int(stats["readouts_max"]),
        "time_step_global_min": float(stats["ts_global_min"]),
        "time_step_global_max": float(stats["ts_global_max"]),
    }


def describe_class_distribution(labels_df: DataFrame, class_col: str) -> dict[int, dict]:
    """Retorna contagem e percentual por classe ordinal."""
    total = labels_df.count()
    counts = labels_df.groupBy(class_col).count().collect()
    result = {}
    for row in sorted(counts, key=lambda r: r[class_col]):
        cls = int(row[class_col])
        n = int(row["count"])
        result[cls] = {"count": n, "pct": round(n / total * 100, 2)}
    return result


def find_vehicles_in_multiple_splits(
    train_ids: list[int], val_ids: list[int], test_ids: list[int]
) -> dict[str, int]:
    """Verifica sobreposição entre splits. Deve retornar zeros."""
    train_set, val_set, test_set = set(train_ids), set(val_ids), set(test_ids)
    return {
        "train_val_overlap": len(train_set & val_set),
        "train_test_overlap": len(train_set & test_set),
        "val_test_overlap": len(val_set & test_set),
    }
