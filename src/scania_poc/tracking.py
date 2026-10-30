"""Utilitários de tracking MLflow para o PoC SCANIA Component X."""

from typing import Any

import mlflow.sklearn

import mlflow


def log_survival_model(
    model: Any,
    metrics: dict[str, float],
    params: dict[str, Any],
    run_name: str,
    experiment_name: str = "/poc_scania/survival",
) -> str:
    """Loga um modelo de sobrevivência e suas métricas no MLflow.

    Retorna o run_id do experimento criado.
    """
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        model_type = type(model).__name__
        mlflow.set_tag("model_type", model_type)
        mlflow.set_tag("framework", "lifelines")
        return run.info.run_id


def log_sklearn_model(
    model: Any,
    metrics: dict[str, float],
    params: dict[str, Any],
    run_name: str,
    experiment_name: str = "/poc_scania/benchmarks",
    artifact_path: str = "model",
) -> str:
    """Loga um modelo scikit-learn e suas métricas no MLflow.

    Registra o modelo como artefato para possível re-uso em batch scoring.
    Retorna o run_id.
    """
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        mlflow.set_tag("model_type", type(model).__name__)
        mlflow.sklearn.log_model(model, artifact_path)
        return run.info.run_id


def log_evaluation_results(
    results: dict[str, dict[str, float]],
    run_name: str = "evaluation_comparison",
    experiment_name: str = "/poc_scania/evaluation",
) -> str:
    """Loga uma comparação entre múltiplos modelos como métricas prefixadas.

    results: {model_name: {metric_name: value}}
    Cada métrica é logada como '<model_name>/<metric_name>'.
    """
    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=run_name) as run:
        flat_metrics: dict[str, float] = {}
        for model_name, model_metrics in results.items():
            for metric_name, value in model_metrics.items():
                key = f"{model_name}/{metric_name}"
                flat_metrics[key] = float(value)
        mlflow.log_metrics(flat_metrics)
        return run.info.run_id
