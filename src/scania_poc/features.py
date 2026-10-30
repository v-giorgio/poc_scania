"""Engenharia de features e geração de snapshots de predição."""

from typing import Any


def compute_total_cost(false_positives: int, false_negatives: int) -> int:
    """Calcula o custo total de classificação com os pesos IDA 2024."""
    return 10 * false_positives + 500 * false_negatives


def generate_snapshots(
    readouts_df: Any,
    vehicle_id_col: str,
    time_step_col: str,
    cutoff_col: str | None = None,
) -> Any:
    """Gera um snapshot por veículo usando apenas o último time_step observado.

    Se cutoff_col for fornecido, filtra readouts anteriores ao cutoff antes
    de selecionar o último time_step (evita vazamento de informação futura).
    Requer PySpark — importado lazily.
    """
    import pyspark.sql.functions as F  # noqa: PLC0415
    from pyspark.sql.window import Window  # noqa: PLC0415

    df = readouts_df
    if cutoff_col is not None:
        df = df.filter(F.col(time_step_col) <= F.col(cutoff_col))

    w = Window.partitionBy(vehicle_id_col).orderBy(F.desc(time_step_col))
    return df.withColumn("_rank", F.rank().over(w)).filter(F.col("_rank") == 1).drop("_rank")
