# Databricks notebook source
# MAGIC %md
# MAGIC # 5.1 Avaliação final
# MAGIC
# MAGIC Avalia uma vez os modelos já selecionados na validação interna. Calcula
# MAGIC sobrevivência/RUL/ordinal no teste interno e custo ordinal nos rótulos da
# MAGIC validação oficial. Não usa nem espera rótulos oficiais de teste.

# COMMAND ----------

import pickle
from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd

from src.scania_poc.evaluation import ordinal_total_cost
from src.scania_poc.config import qualified_table_name, validate_data_schema
from src.scania_poc.modeling import prepare_design_matrices
from src.scania_poc.ordinal import evaluate_ordinal
from src.scania_poc.rul import evaluate_rul
from src.scania_poc.schema import FEATURE_COLS, SPEC_COLS, VEHICLE_ID_COL
from src.scania_poc.survival import (
    compute_c_index,
    compute_integrated_brier_score,
    fit_kaplan_meier,
    supported_brier_times,
    survival_calibration,
)

dbutils.widgets.text("DATA_SCHEMA", "", "Schema UC das tabelas gerenciadas")
dbutils.widgets.text("COXPH_RUN_ID", "", "Run CoxPH previamente selecionado")
dbutils.widgets.text("RUL_RUN_ID", "", "Run RUL previamente selecionado")
dbutils.widgets.text("ORDINAL_RUN_ID", "", "Run ordinal previamente selecionado")
DATA_SCHEMA = validate_data_schema(dbutils.widgets.get("DATA_SCHEMA").strip())
COXPH_RUN_ID = dbutils.widgets.get("COXPH_RUN_ID").strip()
RUL_RUN_ID = dbutils.widgets.get("RUL_RUN_ID").strip()
ORDINAL_RUN_ID = dbutils.widgets.get("ORDINAL_RUN_ID").strip()
assert all([COXPH_RUN_ID, RUL_RUN_ID, ORDINAL_RUN_ID]), "Informe os três run IDs"
FEATURE_COLS_MODEL = [f"{col}_imputed" for col in FEATURE_COLS]
SPEC_COLS_MODEL = [f"{col}_idx" for col in SPEC_COLS]


def load_gold(name):
    table = qualified_table_name(DATA_SCHEMA, "gold", name)
    return spark.read.table(table).toPandas()


train = load_gold("train_fit")
internal_test = load_gold("internal_test")
challenge_validation = load_gold("challenge_validation")
labels_table = qualified_table_name(DATA_SCHEMA, "silver", "validation_labels")
labels_silver = spark.read.table(labels_table)
official_label_sha256 = sorted(
    row["_labels_source_version"]
    for row in labels_silver.select("_labels_source_version").distinct().collect()
)
official_labels = labels_silver.select(VEHICLE_ID_COL, "class_label").toPandas()
challenge_validation = challenge_validation.merge(
    official_labels, on=VEHICLE_ID_COL, how="inner", validate="one_to_one"
)
if len(challenge_validation) != len(official_labels):
    raise ValueError("Join dos rótulos oficiais perdeu veículos")
challenge_source_sha256 = sorted(
    {
        str(value)
        for col in (
            "_readouts_source_version",
            "_specs_source_version",
        )
        for value in challenge_validation[col].dropna().unique().tolist()
    }
)

X_train, X_internal_test, X_challenge_validation = prepare_design_matrices(
    [train, internal_test, challenge_validation],
    FEATURE_COLS_MODEL,
    SPEC_COLS_MODEL,
)

cox_artifact_dir = mlflow.artifacts.download_artifacts(
    run_id=COXPH_RUN_ID, artifact_path="lifelines_model"
)
cox_files = list(Path(cox_artifact_dir).glob("*.pkl"))
if len(cox_files) != 1:
    raise ValueError(f"Esperado um arquivo .pkl no artefato CoxPH; encontrados {len(cox_files)}")
cox_model_path = cox_files[0]
with open(cox_model_path, "rb") as model_file:
    cox = pickle.load(model_file)
rul = mlflow.sklearn.load_model(f"runs:/{RUL_RUN_ID}/model")
ordinal = mlflow.sklearn.load_model(f"runs:/{ORDINAL_RUN_ID}/model")

# COMMAND ----------

# Desempenho final no teste interno reservado por vehicle_id.
duration_col = "residual_time"
event_col = "event_observed"
train_survival = train[[*X_train.columns, duration_col, event_col]].copy()
test_survival = internal_test[[*X_train.columns, duration_col, event_col]].copy()
times = supported_brier_times(train_survival, duration_col, event_col)

km = fit_kaplan_meier(train[duration_col].to_numpy(), train[event_col].to_numpy())


class KaplanMeierAdapter:
    def predict_survival_function(self, frame, horizons):
        return pd.DataFrame(
            [[float(km.predict(float(horizon)))] * len(frame) for horizon in horizons],
            index=horizons,
            columns=frame.index,
        )


km_adapter = KaplanMeierAdapter()
baseline_survival_metrics = {
    "c_index": 0.5,
    "ibs_ipcw": compute_integrated_brier_score(
        km_adapter,
        test_survival,
        duration_col,
        event_col,
        times,
        censoring_reference_df=train_survival,
    ),
}
survival_metrics = {
    "c_index": compute_c_index(cox, test_survival, duration_col, event_col),
    "ibs_ipcw": compute_integrated_brier_score(
        cox,
        test_survival,
        duration_col,
        event_col,
        times,
        censoring_reference_df=train_survival,
    ),
}
test_rul_events = internal_test[event_col].to_numpy(dtype=int) == 1
rul_metrics = evaluate_rul(
    internal_test.loc[test_rul_events, duration_col].to_numpy(),
    rul.predict(X_internal_test.loc[test_rul_events]),
)
test_classes = internal_test["class_label_derived"].fillna(-1).to_numpy(dtype=int)
known_test_classes = test_classes >= 0
ordinal_internal_metrics = evaluate_ordinal(
    test_classes[known_test_classes],
    ordinal.predict(X_internal_test.loc[known_test_classes]),
)
train_known_classes = train["class_label_derived"].dropna().astype(int)
majority_class = int(train_known_classes.mode().iloc[0])
internal_majority_metrics = evaluate_ordinal(
    test_classes[known_test_classes],
    np.full(known_test_classes.sum(), majority_class, dtype=int),
)

# Os rótulos oficiais aparecem somente neste bloco de avaliação final.
official_predictions = ordinal.predict(X_challenge_validation)
official_metrics = evaluate_ordinal(
    challenge_validation["class_label"].to_numpy(dtype=int),
    official_predictions,
)
official_metrics["baseline_majority_cost"] = ordinal_total_cost(
    challenge_validation["class_label"].to_numpy(dtype=int),
    np.full(len(challenge_validation), majority_class, dtype=int),
)
official_metrics["baseline_majority_class"] = majority_class

print("Internal test survival baseline KM:", baseline_survival_metrics)
print("Internal test survival CoxPH:", survival_metrics)
print("Internal test RUL (observed repairs only):", rul_metrics)
print("Internal test ordinal (known derived labels only):", ordinal_internal_metrics)
print("Internal test ordinal majority baseline:", internal_majority_metrics)
print("Official validation ordinal evaluation:", official_metrics)
print(
    "Survival calibration on internal test:",
    survival_calibration(cox, test_survival, duration_col, event_col, times),
)
print("Official test labels unavailable; no supervised test metrics were computed.")

# COMMAND ----------

mlflow.set_experiment("/poc_scania/component_x")
with mlflow.start_run(run_name="final_reserved_evaluation"):
    mlflow.set_tag("evaluation_policy", "one-time internal test and official validation; no tuning")
    mlflow.log_params(
        {
            "coxph_run_id": COXPH_RUN_ID,
            "rul_run_id": RUL_RUN_ID,
            "ordinal_run_id": ORDINAL_RUN_ID,
            "official_labels_used": "validation_only",
            "test_labels_available": "false",
            "official_label_sha256": ",".join(official_label_sha256),
            "challenge_feature_source_sha256": ",".join(challenge_source_sha256),
        }
    )
    mlflow.log_metrics({f"internal_test/survival_{k}": float(v) for k, v in survival_metrics.items()})
    mlflow.log_metrics(
        {f"internal_test/kaplan_meier_{k}": float(v) for k, v in baseline_survival_metrics.items()}
    )
    mlflow.log_metrics(
        {
            f"internal_test/ordinal_{key}": float(ordinal_internal_metrics[key])
            for key in ("balanced_accuracy", "macro_f1", "maoe", "total_cost")
        }
    )
    mlflow.log_metrics(
        {
            f"internal_test/majority_ordinal_{key}": float(internal_majority_metrics[key])
            for key in ("balanced_accuracy", "macro_f1", "maoe", "total_cost")
        }
    )
    mlflow.log_metrics(
        {
            f"internal_test/rul_events_only_{key}": float(value)
            for key, value in rul_metrics.items()
            if key != "n"
        }
    )
    mlflow.log_metric("internal_test/rul_events_only_n", int(rul_metrics["n"]))
    mlflow.log_metrics(
        {
            "official_validation/balanced_accuracy": official_metrics["balanced_accuracy"],
            "official_validation/macro_f1": official_metrics["macro_f1"],
            "official_validation/maoe": official_metrics["maoe"],
            "official_validation/total_cost": official_metrics["total_cost"],
            "official_validation/baseline_majority_cost": official_metrics["baseline_majority_cost"],
        }
    )
    mlflow.log_dict(
        {
            "survival": survival_metrics,
            "survival_baseline_km": baseline_survival_metrics,
            "rul_observed_events_only": rul_metrics,
            "ordinal_internal_test": ordinal_internal_metrics,
            "ordinal_internal_test_majority_baseline": internal_majority_metrics,
            "ordinal_official_validation": official_metrics,
            "calibration": survival_calibration(
                cox, test_survival, duration_col, event_col, times
            ),
        },
        "final_metrics.json",
    )
