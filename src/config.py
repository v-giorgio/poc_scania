"""Configurações centrais da PoC lidas de variáveis de ambiente."""

import os

# AWS S3
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_RAW_PREFIX = "raw/scania_component_x"
S3_SILVER_PREFIX = "silver/component_x"
S3_GOLD_PREFIX = "gold/features_predictive"

# MLflow
MLFLOW_EXPERIMENT_BASE = "/poc_scania"

# Dataset
TARGET_COLUMN = "class"
POSITIVE_CLASS = "pos"
COST_FALSE_POSITIVE = 10
COST_FALSE_NEGATIVE = 500
