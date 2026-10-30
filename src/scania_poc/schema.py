"""Constantes de schema para o dataset SCANIA Component X (IDA 2024).

Derivadas da inspeção dos arquivos CSV em dataset_local/ e dos PDFs em papers/.
Qualquer semântica marcada como hipótese deve ser confirmada antes de uso.
"""

# --- Colunas de identidade (presentes em todos os arquivos) ---
VEHICLE_ID_COL = "vehicle_id"

# --- train_operational_readouts.csv ---
TIME_STEP_COL = "time_step"

# Grupos de sensores: chave = prefixo numérico, valor = lista de índices
# Nomes reais observados no CSV (ex: "167_0", "167_1", ..., "167_9")
SENSOR_GROUPS: dict[str, list[int]] = {
    "171": list(range(1)),
    "666": list(range(1)),
    "427": list(range(1)),
    "837": list(range(1)),
    "167": list(range(10)),
    "309": list(range(1)),
    "272": list(range(10)),
    "835": list(range(1)),
    "370": list(range(1)),
    "291": list(range(11)),
    "158": list(range(10)),
    "100": list(range(1)),
    "459": list(range(20)),
    "397": list(range(36)),
}

FEATURE_COLS: list[str] = [
    f"{group}_{i}" for group, indices in SENSOR_GROUPS.items() for i in indices
]

N_FEATURE_COLS = 105  # verificado no header do CSV

# --- train_tte.csv ---
TTE_COL = "length_of_study_time_step"  # duração de acompanhamento do veículo
# 1 = reparo observado, 0 = censurado (hipótese confirmada pelo paper)
EVENT_COL = "in_study_repair"

# --- train_specifications.csv ---
SPEC_COLS: list[str] = [f"Spec_{i}" for i in range(8)]

# --- validation_labels.csv / test_labels.csv ---
CLASS_LABEL_COL = "class_label"

# Classes ordinais IDA 2024 — limites em time_steps (unidade anonimizada)
# Fonte: papers/2024_IDA_challenge_v2.pdf (transcrever regra exata após leitura)
ORDINAL_CLASSES: dict[int, tuple[float, float]] = {
    0: (0.0, 6.0),
    1: (6.0, 12.0),
    2: (12.0, 24.0),
    3: (24.0, 48.0),
    4: (48.0, float("inf")),
}

N_ORDINAL_CLASSES = 5
