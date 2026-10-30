"""Split de veículos para treino/validação/teste.

Regra fundamental (SPEC.md §5): nenhum vehicle_id pode aparecer em mais
de uma partição. O split é feito por veículo, nunca por linha de readout.
"""

import random
from collections import defaultdict


def split_by_vehicle(
    vehicle_ids: list[int],
    event_flags: list[int],
    ratios: tuple[float, float, float] = (0.70, 0.15, 0.15),
    seed: int = 42,
) -> tuple[list[int], list[int], list[int]]:
    """Divide vehicle_ids em train/val/test estratificado por event_flag.

    Retorna três listas disjuntas de vehicle_ids.
    Garante que len(train) + len(val) + len(test) == len(vehicle_ids).
    """
    if abs(sum(ratios) - 1.0) > 1e-9:
        raise ValueError(f"Ratios devem somar 1.0, mas somam {sum(ratios)}")
    if len(vehicle_ids) != len(event_flags):
        raise ValueError("vehicle_ids e event_flags devem ter o mesmo tamanho")
    if len(vehicle_ids) != len(set(vehicle_ids)):
        raise ValueError("vehicle_ids deve conter somente identificadores únicos")
    if any(flag not in (0, 1) for flag in event_flags):
        raise ValueError("event_flags deve conter somente 0 e 1")

    rng = random.Random(seed)

    strata: dict[int, list[int]] = defaultdict(list)
    for vid, flag in zip(vehicle_ids, event_flags):
        strata[flag].append(vid)

    train_ids: list[int] = []
    val_ids: list[int] = []
    test_ids: list[int] = []

    for flag, ids in strata.items():
        ids_shuffled = sorted(ids)
        rng.shuffle(ids_shuffled)
        n = len(ids_shuffled)
        n_train = round(n * ratios[0])
        n_val = round(n * ratios[1])

        train_ids.extend(ids_shuffled[:n_train])
        val_ids.extend(ids_shuffled[n_train : n_train + n_val])
        test_ids.extend(ids_shuffled[n_train + n_val :])

    _assert_no_overlap(train_ids, val_ids, test_ids)
    return train_ids, val_ids, test_ids


def _assert_no_overlap(train_ids: list[int], val_ids: list[int], test_ids: list[int]) -> None:
    """Levanta AssertionError se qualquer vehicle_id aparecer em múltiplos splits."""
    train_set = set(train_ids)
    val_set = set(val_ids)
    test_set = set(test_ids)
    overlap_tv = train_set & val_set
    overlap_tt = train_set & test_set
    overlap_vt = val_set & test_set
    assert not overlap_tv, f"Sobreposição train/val: {overlap_tv}"
    assert not overlap_tt, f"Sobreposição train/test: {overlap_tt}"
    assert not overlap_vt, f"Sobreposição val/test: {overlap_vt}"
