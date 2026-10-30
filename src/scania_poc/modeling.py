"""Small modeling helpers shared by Databricks notebooks and local tests."""

from collections.abc import Sequence

import numpy as np
import pandas as pd


def prepare_design_matrices(
    frames: Sequence[pd.DataFrame],
    numeric_columns: Sequence[str],
    categorical_columns: Sequence[str],
) -> list[pd.DataFrame]:
    """One-hot encode using training categories and align every later frame.

    ``frames[0]`` is the training partition. Categorical vocabulary and final
    design columns are learned only from it; unseen categories map to all-zero
    columns. Numeric values must already have been imputed using train-only
    statistics.
    """
    if not frames:
        raise ValueError("Passe primeiro o DataFrame de treino")
    required = set(numeric_columns) | set(categorical_columns)
    if any(not required.issubset(frame.columns) for frame in frames):
        raise ValueError("Há colunas de features ausentes em uma partição")

    def encode(frame: pd.DataFrame) -> pd.DataFrame:
        numeric = frame[list(numeric_columns)].astype(float).reset_index(drop=True)
        if not np.isfinite(numeric.to_numpy()).all():
            raise ValueError("Features numéricas devem estar imputadas e finitas")
        categorical = frame[list(categorical_columns)].astype("string").fillna("<NULL>")
        encoded = pd.get_dummies(
            categorical.reset_index(drop=True),
            columns=list(categorical_columns),
            dtype=float,
        )
        return pd.concat([numeric, encoded], axis=1)

    train = encode(frames[0])
    columns = list(train.columns)
    aligned = [train]
    for frame in frames[1:]:
        aligned.append(encode(frame).reindex(columns=columns, fill_value=0.0))
    return aligned
