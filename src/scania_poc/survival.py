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


def _model_covariates(
    model: Any, df: pd.DataFrame, duration_col: str, event_col: str
) -> pd.DataFrame:
    """Remove outcome columns before asking a fitted model for predictions."""
    if hasattr(model, "params_"):
        columns = list(model.params_.index)
        return df[columns]
    return df.drop(columns=[duration_col, event_col], errors="ignore")


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
    risk_scores = model.predict_partial_hazard(
        _model_covariates(model, df, duration_col, event_col)
    )
    return concordance_index(df[duration_col], -risk_scores, df[event_col])


def compute_integrated_brier_score(
    model: Any,
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    times: np.ndarray | None = None,
    censoring_reference_df: pd.DataFrame | None = None,
) -> float:
    """Calculate IPCW Integrated Brier Score using train-only censoring KM.

    ``censoring_reference_df`` must be the training partition, not the
    evaluation cohort. Evaluation times outside its censoring support raise
    rather than silently producing biased scores.
    """
    if censoring_reference_df is None:
        raise ValueError("Passe censoring_reference_df do conjunto de treino")
    if len(df) == 0:
        raise ValueError("O conjunto de avaliação está vazio")
    if times is None:
        low = max(0.0, float(df[duration_col].min()))
        high = float(df[duration_col].max())
        times = np.linspace(low, high, 50)
    times = np.asarray(times, dtype=float)
    if len(times) < 2 or not np.isfinite(times).all() or (np.diff(times) <= 0).any():
        raise ValueError("times deve conter ao menos dois tempos finitos e crescentes")

    ref_events = censoring_reference_df[event_col].to_numpy(dtype=int)
    if not np.isin(ref_events, [0, 1]).all():
        raise ValueError("event_col deve conter somente 0 e 1")
    censoring_kmf = KaplanMeierFitter(label="censoring_survival")
    censoring_kmf.fit(
        durations=censoring_reference_df[duration_col].to_numpy(dtype=float),
        event_observed=1 - ref_events,
    )

    sf_pred = model.predict_survival_function(
        _model_covariates(model, df, duration_col, event_col), times=times
    )
    brier_scores = []
    events = df[event_col].to_numpy(dtype=int)
    durations = df[duration_col].to_numpy(dtype=float)
    if not np.isin(events, [0, 1]).all():
        raise ValueError("event_col deve conter somente 0 e 1")

    event_before_censoring = np.ones(len(df), dtype=float)
    event_rows = np.flatnonzero(events == 1)
    if len(event_rows):
        left_limits = np.nextafter(durations[event_rows], -np.inf)
        event_before_censoring[event_rows] = np.asarray(
            censoring_kmf.predict(left_limits), dtype=float
        )
    if (event_before_censoring[event_rows] <= 0).any():
        raise ValueError("Censura KM sem suporte antes de um evento avaliado")

    for t in times:
        censor_survival_at_t = float(censoring_kmf.predict(float(t)))
        if censor_survival_at_t <= 0:
            raise ValueError(f"Tempo {t:g} fora do suporte observado da censura")
        sf_t = sf_pred.loc[t].to_numpy(dtype=float)
        event_by_t = (events == 1) & (durations <= t)
        known_survival_at_t = durations > t
        weighted_error = np.zeros(len(df), dtype=float)
        weighted_error[event_by_t] = sf_t[event_by_t] ** 2 / event_before_censoring[event_by_t]
        weighted_error[known_survival_at_t] = (
            1.0 - sf_t[known_survival_at_t]
        ) ** 2 / censor_survival_at_t
        brier_scores.append(float(weighted_error.mean()))

    return float(np.trapezoid(brier_scores, times) / (times[-1] - times[0]))


def supported_brier_times(
    train_df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    quantiles: np.ndarray | None = None,
) -> np.ndarray:
    """Choose train-only quantile horizons with positive censoring support."""
    if quantiles is None:
        quantiles = np.linspace(0.1, 0.8, 8)
    durations = train_df[duration_col].to_numpy(dtype=float)
    events = train_df[event_col].to_numpy(dtype=int)
    if len(durations) == 0 or not np.isin(events, [0, 1]).all():
        raise ValueError("Treino vazio ou indicador de evento inválido")
    candidates = np.unique(np.quantile(durations, quantiles))
    censoring_kmf = KaplanMeierFitter().fit(durations, event_observed=1 - events)
    supported = np.asarray(
        [time for time in candidates if float(censoring_kmf.predict(float(time))) > 0],
        dtype=float,
    )
    if len(supported) < 2:
        raise ValueError("Menos de dois horizontes de Brier possuem suporte de censura")
    return supported


def survival_calibration(
    model: Any,
    df: pd.DataFrame,
    duration_col: str,
    event_col: str,
    times: np.ndarray,
) -> list[dict[str, float | int]]:
    """Compare mean predicted survival with Kaplan-Meier at fixed horizons.

    This is a compact calibration diagnostic, not an uncertainty interval.
    Horizons and remaining at-risk counts must accompany its interpretation.
    """
    times = np.asarray(times, dtype=float)
    if len(df) == 0 or len(times) == 0 or not np.isfinite(times).all():
        raise ValueError("df e times devem ser não vazios e finitos")
    observed = KaplanMeierFitter(label="observed").fit(
        durations=df[duration_col].to_numpy(dtype=float),
        event_observed=df[event_col].to_numpy(dtype=int),
    )
    predicted = model.predict_survival_function(
        _model_covariates(model, df, duration_col, event_col), times=times
    )
    result = []
    for time in times:
        result.append(
            {
                "time": float(time),
                "predicted_survival": float(predicted.loc[time].mean()),
                "observed_km_survival": float(observed.predict(float(time))),
                "at_risk": int((df[duration_col].to_numpy(dtype=float) >= time).sum()),
            }
        )
    return result


def survival_summary(model: Any, label: str = "") -> dict[str, Any]:
    """Retorna um dict de metadados do modelo para logging."""
    summary: dict[str, Any] = {"label": label, "type": type(model).__name__}
    if hasattr(model, "concordance_index_"):
        summary["train_c_index"] = float(model.concordance_index_)
    if hasattr(model, "AIC_"):
        summary["aic"] = float(model.AIC_)
    return summary
