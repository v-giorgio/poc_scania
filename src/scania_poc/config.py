"""Configurações centrais da PoC lidas de variáveis de ambiente."""

import os

S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_RAW_PREFIX = "raw/scania_component_x"
S3_SILVER_PREFIX = "silver/component_x"
S3_GOLD_PREFIX = "gold/features_predictive"

MLFLOW_EXPERIMENT_BASE = "/poc_scania"
