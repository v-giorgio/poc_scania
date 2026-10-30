# Databricks notebook source
# MAGIC %md
# MAGIC # 4.1 Baselines de sobrevivência e classificação ordinal
# MAGIC
# MAGIC Ajusta estatísticas e modelos somente em `train_fit`; usa `internal_validation`
# MAGIC para selecionar/relatar os benchmarks. `internal_test` e a validação oficial
# MAGIC permanecem reservados para a etapa final. O Cox usa a tabela compacta (um
# MAGIC snapshot por veículo), não coleta a série bruta para o driver.

# COMMAND ----------

import importlib.metadata
import os
import pickle
import platform
import tempfile

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd

from src.scania_poc.config import qualified_table_name, validate_data_schema
from src.scania_poc.modeling import prepare_design_matrices
from src.scania_poc.ordinal import (
    evaluate_ordinal,
    fit_ordinal_classifier,
)
from src.scania_poc.rul import evaluate_rul, fit_rul_regressor
from src.scania_poc.schema import FEATURE_COLS, SPEC_COLS
from src.scania_poc.survival import (
    compute_c_index,
    compute_integrated_brier_score,
    fit_cox_ph,
    fit_kaplan_meier,
    supported_brier_times,
    survival_calibration,
)
from src.scania_poc.tracking import personal_experiment_path

dbutils.widgets.text("DATA_SCHEMA", "", "Schema UC das tabelas gerenciadas")
dbutils.widgets.text("SEED", "42", "Seed usada no split/snapshot")
dbutils.widgets.text("GIT_REVISION", "unknown", "Commit/revisão do código")
DATA_SCHEMA = validate_data_schema(dbutils.widgets.get("DATA_SCHEMA").strip())
SEED = int(dbutils.widgets.get("SEED"))
GIT_REVISION = dbutils.widgets.get("GIT_REVISION").strip() or "unknown"
EXPERIMENT_NAME = personal_experiment_path(spark)
mlflow.set_experiment(EXPERIMENT_NAME)

FEATURE_MODEL_COLS = [f"{col}_imputed" for col in FEATURE_COLS]
SPEC_MODEL_COLS = [f"{col}_idx" for col in SPEC_COLS]
NUMERIC_MODEL_COLS = FEATURE_MODEL_COLS


def load_gold(name):
    table = qualified_table_name(DATA_SCHEMA, "gold", name)
    return spark.read.table(table).toPandas()


train = load_gold("train_fit")
validation = load_gold("internal_validation")
X_train, X_validation = prepare_design_matrices(
    [train, validation], NUMERIC_MODEL_COLS, SPEC_MODEL_COLS
)

source_hashes = sorted(
    {
        str(value)
        for col in (
            "_readouts_source_version",
            "_tte_source_version",
            "_specs_source_version",
        )
        for value in train[col].dropna().unique().tolist()
    }
)
tracking_context = {
    "seed": SEED,
    "split": "70/15/15 stratified by vehicle and event",
    "snapshot_policy": "one deterministic hashed readout strictly before follow-up end",
    "source_sha256": ",".join(source_hashes),
    "git_revision": GIT_REVISION,
    "python_version": platform.python_version(),
    "lifelines_version": importlib.metadata.version("lifelines"),
    "scikit_learn_version": importlib.metadata.version("scikit-learn"),
    "mlflow_version": importlib.metadata.version("mlflow"),
}


def log_context():
    mlflow.log_params(tracking_context)
    mlflow.set_tag("target", "residual time to first observed Component X repair")
    mlflow.set_tag("validation_policy", "internal vehicle holdout; official labels not used for tuning")


# COMMAND ----------

# Baseline KM e Cox regularizado. Horizontes do IBS são calculados apenas no treino.
duration_col = "residual_time"
event_col = "event_observed"
train_survival = X_train.copy()
train_survival[duration_col] = train[duration_col].to_numpy()
train_survival[event_col] = train[event_col].to_numpy()
validation_survival = X_validation.copy()
validation_survival[duration_col] = validation[duration_col].to_numpy()
validation_survival[event_col] = validation[event_col].to_numpy()
km = fit_kaplan_meier(train[duration_col].to_numpy(), train[event_col].to_numpy())


class KaplanMeierAdapter:
    def predict_survival_function(self, frame, times):
        values = [[float(km.predict(float(t)))] * len(frame) for t in times]
        return pd.DataFrame(values, index=times, columns=frame.index)


km_adapter = KaplanMeierAdapter()
duration_quantiles = supported_brier_times(train_survival, duration_col, event_col)

with mlflow.start_run(run_name="kaplan_meier_baseline") as run:
    log_context()
    metrics = {
        "validation/c_index": 0.5,
        "validation/ibs_ipcw": compute_integrated_brier_score(
            km_adapter,
            validation_survival,
            duration_col,
            event_col,
            duration_quantiles,
            censoring_reference_df=train_survival,
        ),
    }
    mlflow.log_metrics(metrics)
    mlflow.set_tag("model_type", "KaplanMeier")
    mlflow.set_tag("interpretation", "marginal survival baseline; no feature discrimination")
    mlflow.log_dict(
        survival_calibration(km_adapter, validation_survival, duration_col, event_col, duration_quantiles),
        "calibration.json",
    )
    print(f"KM run_id={run.info.run_id}; metrics={metrics}")

cox = fit_cox_ph(train_survival, duration_col, event_col, penalizer=0.1)
with mlflow.start_run(run_name="cox_ph_regularized") as run:
    log_context()
    metrics = {
        "validation/c_index": compute_c_index(cox, validation_survival, duration_col, event_col),
        "validation/ibs_ipcw": compute_integrated_brier_score(
            cox,
            validation_survival,
            duration_col,
            event_col,
            duration_quantiles,
            censoring_reference_df=train_survival,
        ),
    }
    mlflow.log_params({"penalizer_l2": 0.1, "n_features": len(X_train.columns)})
    mlflow.log_metrics(metrics)
    mlflow.set_tag("model_type", "CoxPHFitter")
    mlflow.set_tag("limitation", "proportional hazards assumption must be reviewed")
    mlflow.log_dict(
        survival_calibration(cox, validation_survival, duration_col, event_col, duration_quantiles),
        "calibration.json",
    )
    with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as artifact:
        pickle.dump(cox, artifact)
        model_path = artifact.name
    mlflow.log_artifact(model_path, artifact_path="lifelines_model")
    os.unlink(model_path)
    COXPH_RUN_ID = run.info.run_id
    print(f"Cox run_id={COXPH_RUN_ID}; metrics={metrics}")

# COMMAND ----------

# Benchmarks condicionais: regressão usa eventos observados; ordinal usa apenas
# classes derivadas conhecidas (sem censurados abaixo de 48 ou fronteiras).
train_events = train[event_col].to_numpy(dtype=int) == 1
validation_events = validation[event_col].to_numpy(dtype=int) == 1
rul = fit_rul_regressor(X_train.loc[train_events], train.loc[train_events, duration_col].to_numpy(), seed=SEED)
rul_metrics = evaluate_rul(
    validation.loc[validation_events, duration_col].to_numpy(),
    rul.predict(X_validation.loc[validation_events]),
)
with mlflow.start_run(run_name="rul_events_only_benchmark") as run:
    log_context()
    mlflow.log_metrics({f"validation/events_only_{k}": float(v) for k, v in rul_metrics.items() if k != "n"})
    mlflow.log_metric("validation/events_only_n", int(rul_metrics["n"]))
    mlflow.set_tag("model_type", "RandomForestRegressor")
    mlflow.set_tag("limitation", "complete-case metrics on observed first repairs only")
    mlflow.sklearn.log_model(rul, artifact_path="model")
    mlflow.log_dict({"metrics": rul_metrics, "population": "validation vehicles with observed repair"}, "benchmark.json")
    RUL_RUN_ID = run.info.run_id
    print(f"RUL run_id={run.info.run_id}; metrics={rul_metrics}")

train_labels = train["class_label_derived"].fillna(-1).to_numpy(dtype=int)
validation_labels = validation["class_label_derived"].fillna(-1).to_numpy(dtype=int)
ordinal = fit_ordinal_classifier(X_train, train_labels, seed=SEED)
known_validation = validation_labels >= 0
majority_class = int(pd.Series(train_labels[train_labels >= 0]).mode().iloc[0])
majority_metrics = evaluate_ordinal(
    validation_labels[known_validation],
    np.full(known_validation.sum(), majority_class, dtype=int),
)
ordinal_metrics = evaluate_ordinal(
    validation_labels[known_validation],
    ordinal.predict(X_validation.loc[known_validation]),
)
with mlflow.start_run(run_name="ordinal_majority_baseline") as run:
    log_context()
    mlflow.log_param("majority_class_from_train_fit", majority_class)
    mlflow.log_metrics(
        {
            "validation/balanced_accuracy": majority_metrics["balanced_accuracy"],
            "validation/macro_f1": majority_metrics["macro_f1"],
            "validation/maoe": majority_metrics["maoe"],
            "validation/total_cost": majority_metrics["total_cost"],
            "validation/known_labels_n": majority_metrics["n"],
        }
    )
    mlflow.set_tag("model_type", "majority_class_baseline")
    mlflow.set_tag("class_mapping", "IDA 2024; exact boundaries excluded")
    print(f"Majority ordinal baseline run_id={run.info.run_id}; metrics={majority_metrics}")

with mlflow.start_run(run_name="ordinal_random_forest") as run:
    log_context()
    mlflow.log_params({"n_estimators": 100, "max_depth": 10, "class_weight": "balanced"})
    mlflow.log_metrics(
        {
            "validation/balanced_accuracy": ordinal_metrics["balanced_accuracy"],
            "validation/macro_f1": ordinal_metrics["macro_f1"],
            "validation/maoe": ordinal_metrics["maoe"],
            "validation/total_cost": ordinal_metrics["total_cost"],
            "validation/known_labels_n": ordinal_metrics["n"],
        }
    )
    mlflow.set_tag("model_type", "RandomForestClassifier")
    mlflow.set_tag("class_mapping", "IDA 2024; exact boundaries excluded")
    mlflow.sklearn.log_model(ordinal, artifact_path="model")
    mlflow.log_dict(ordinal_metrics, "validation_metrics.json")
    ORDINAL_RUN_ID = run.info.run_id
    print(f"Ordinal run_id={ORDINAL_RUN_ID}; metrics={ordinal_metrics}")

print("Registre COXPH_RUN_ID e ORDINAL_RUN_ID para avaliação final; revisão:", GIT_REVISION)
print("Registre estes três run IDs para avaliação final:", COXPH_RUN_ID, RUL_RUN_ID, ORDINAL_RUN_ID)
