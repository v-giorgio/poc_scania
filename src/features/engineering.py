"""Funções de engenharia de features."""


def compute_total_cost(false_positives: int, false_negatives: int) -> int:
    """Calcula o custo total de classificação com os pesos do dataset SCANIA."""
    return 10 * false_positives + 500 * false_negatives
