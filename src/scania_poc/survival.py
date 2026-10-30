"""Modelos de análise de sobrevivência para o dataset SCANIA Component X.

Usa a biblioteca lifelines. Implementa:
- KaplanMeierFitter como baseline não-paramétrico
- CoxPHFitter como modelo paramétrico principal
- Métricas: C-index, Integrated Brier Score, calibração
"""

from typing import Any

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter, KaplanMeierFitter
from lifelines.utils import concordance_index


def fit_kaplan_meier(
    durations: np.ndarray | pd.Series,
    events: np.ndarray | pd.Series,
    label: str = "KM",
) -> KaplanMeierFitter:
    """Ajusta o estimador de Kaplan-Meier e retorna o objeto fitter."""
    kmf = KaplanMeierFitter(label=label)
    kmf.fit(durations=durations, event_observed=events)
    return kmf


def fit_cox_ph(
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    penalizer: float = 0.1,
) -> CoxPHFitter:
    """Ajusta o modelo de Cox Proportional Hazards.

    Usa regularização L2 (penalizer) para lidar com multicolinearidade.
    """
    cph = CoxPHFitter(penalizer=penalizer)
    cph.fit(df, duration_col=duration_col, event_col=event_col)
    return cph


def compute_c_index(
    model: Any,
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
) -> float:
    """Calcula o C-index (concordance index) para um modelo de sobrevivência."""
    risk_scores = model.predict_partial_hazard(df)
    return concordance_index(df[duration_col], -risk_scores, df[event_col])


def compute_integrated_brier_score(
    model: Any,
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    times: np.ndarray | None = None,
) -> float:
    """Calcula o Integrated Brier Score (IBS) para um modelo de sobrevivência.

    Requer lifelines >= 0.27. Valores mais baixos indicam melhor calibração.
    """
    from lifelines.utils import survival_table_from_events  # noqa: PLC0415
    from lifelines import WeibullFitter  # noqa: PLC0415

    if times is None:
        t_max = df[duration_col].max()
        times = np.linspace(df[duration_col].min(), t_max, 50)

    # Calcular predições de sobrevivência em cada ponto de tempo
    sf_pred = model.predict_survival_function(df, times=times)

    brier_scores = []
    n = len(df)
    events = df[event_col].values
    durations = df[duration_col].values

    for t in times:
        sf_t = sf_pred.loc[t].values
        # IPCW simples (sem censura-ponderação para simplificar o PoC)
        bs = np.mean(
            (events * (durations <= t) * (1 - sf_t) ** 2)
            + ((1 - events * (durations <= t)) * sf_t**2)
        )
        brier_scores.append(bs)

    # Integração trapezoidal normalizada
    ibs = float(np.trapz(brier_scores, times) / (times[-1] - times[0]))
    return ibs


def survival_summary(model: Any, label: str = "") -> dict[str, Any]:
    """Retorna um dict de metadados do modelo para logging."""
    summary: dict[str, Any] = {"label": label, "type": type(model).__name__}
    if hasattr(model, "concordance_index_"):
        summary["train_c_index"] = float(model.concordance_index_)
    if hasattr(model, "AIC_"):
        summary["aic"] = float(model.AIC_)
    return summary
