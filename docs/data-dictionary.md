# Dicionário de Dados — SCANIA Component X (IDA 2024)

> Baseado na inspeção dos arquivos CSV. Semântica derivada do paper quando explícita,
> ou marcada como [HIPÓTESE] quando inferida. Atualizar após leitura completa dos PDFs.

---

## train_tte.csv

Tabela de sobrevivência: uma linha por veículo do conjunto de treino.

| Coluna | Tipo | Missing | Semântica | Fonte |
|---|---|---|---|---|
| `vehicle_id` | int | 0% | Identificador único do veículo | Observado |
| `length_of_study_time_step` | float | 0% | Duração de acompanhamento do veículo no estudo (time_steps) | Paper |
| `in_study_repair` | int {0,1} | 0% | 1 = reparo do Componente X observado no período; 0 = censurado | [HIPÓTESE: confirmar com paper] |

**Notas:**
- `in_study_repair = 0` significa que o veículo saiu do estudo sem reparo (right-censoring)
- TTE varia de 73,4 a 510,0 time_steps (todos acima de 48)
- Taxa de evento: 9,64% (2.272/23.550 veículos)

---

## train_operational_readouts.csv / validation_operational_readouts.csv / test_operational_readouts.csv

Série temporal de leituras de sensores por veículo. Múltiplas linhas por veículo.

| Coluna | Tipo | Missing (treino) | Semântica | Fonte |
|---|---|---|---|---|
| `vehicle_id` | int | 0% | Identificador do veículo | Observado |
| `time_step` | float | 0% | Instante da leitura no tempo anonimizado | [HIPÓTESE: unidade não é dia/km] |
| `171_0` | float | 0% | Leitura do sensor do grupo 171 (1 sub-canal) | [HIPÓTESE: cumulative counter] |
| `666_0` | float | 0% | Leitura do sensor do grupo 666 (1 sub-canal) | [HIPÓTESE] |
| `427_0` | float | 0% | Leitura do sensor do grupo 427 (1 sub-canal) | [HIPÓTESE] |
| `837_0` | float | 0% | Leitura do sensor do grupo 837 (1 sub-canal) | [HIPÓTESE] |
| `167_0`..`167_9` | float | <1% | 10 sub-canais do sensor 167 | [HIPÓTESE] |
| `309_0` | float | <1% | Leitura do sensor do grupo 309 | [HIPÓTESE] |
| `272_0`..`272_9` | float | <1% | 10 sub-canais do sensor 272 | [HIPÓTESE] |
| `835_0` | float | <1% | Leitura do sensor do grupo 835 | [HIPÓTESE] |
| `370_0` | float | <1% | Leitura do sensor do grupo 370 | [HIPÓTESE] |
| `291_0`..`291_10` | float | **~0,86%** | 11 sub-canais do sensor 291 — faltam em bloco | [HIPÓTESE] |
| `158_0`..`158_9` | float | <1% | 10 sub-canais do sensor 158 | [HIPÓTESE] |
| `100_0` | float | <1% | Leitura do sensor do grupo 100 | [HIPÓTESE] |
| `459_0`..`459_19` | float | **~0,74%** | 20 sub-canais do sensor 459 — faltam em bloco | [HIPÓTESE] |
| `397_0`..`397_35` | float | <1% | 36 sub-canais do sensor 397 (maior grupo) | [HIPÓTESE] |

**Total de colunas de features:** 105  
**Codificação de missings:** valores nulos reais (NaN), **não** string `"na"`

---

## train_specifications.csv / validation_specifications.csv / test_specifications.csv

Atributos categóricos fixos por veículo (não variam com o tempo).

| Coluna | Tipo | Missing | Valores únicos | Semântica |
|---|---|---|---|---|
| `vehicle_id` | int | 0% | — | Identificador do veículo |
| `Spec_0` | string | 0% | Cat0, Cat1, Cat2 (3) | [HIPÓTESE: tipo de veículo?] |
| `Spec_1` | string | 0% | Cat0..Cat28 (29) | [HIPÓTESE: modelo/configuração?] |
| `Spec_2` | string | 0% | Cat0..Cat20 (21) | [HIPÓTESE] |
| `Spec_3` | string | 0% | Cat0..Cat3 (4) | [HIPÓTESE] |
| `Spec_4` | string | 0% | Cat0, Cat1 (2) | [HIPÓTESE: feature binária] |
| `Spec_5` | string | 0% | Cat0..Cat4 (5) | [HIPÓTESE] |
| `Spec_6` | string | 0% | Cat0..Cat18 com gaps (17) | [HIPÓTESE] |
| `Spec_7` | string | 0% | Cat0..Cat8 (9) | [HIPÓTESE] |

---

## validation_labels.csv / test_labels.csv

Rótulos ordinais para avaliação classificatória. Não existe equivalente no treino
(o treino usa `train_tte.csv` diretamente para sobrevivência).

| Coluna | Tipo | Missing | Semântica | Fonte |
|---|---|---|---|---|
| `vehicle_id` | int | 0% | Identificador do veículo | Observado |
| `class_label` | int {0,1,2,3,4} | 0% | Classe ordinal de urgência de reparo | [HIPÓTESE: 0=sem urgência, 4=urgente] |

**[HIPÓTESE — CONFIRMAR COM papers/2024_IDA_challenge_v2.pdf]**

Mapeamento tentativo (a confirmar):

| Classe | Intervalo de TTE | Semântica |
|---|---|---|
| 0 | > 48 time_steps (ou censurado) | Sem reparo iminente |
| 1 | 24–48 time_steps | Reparo relativamente distante |
| 2 | 12–24 time_steps | Reparo moderadamente próximo |
| 3 | 6–12 time_steps | Reparo próximo |
| 4 | 0–6 time_steps | Reparo muito iminente |

**Alternativa hipótese (inversa):** 0=0-6, 1=6-12, 2=12-24, 3=24-48, 4=48+ (padrão SPEC.md).
A distribuição (classe 0 = 97%) favorece a primeira hipótese (0 = sem urgência).

---

## Relações entre Arquivos

```
vehicle_id (PK)
   ├── train_tte.csv           (1:1 por veículo)
   ├── train_specifications.csv (1:1 por veículo)
   └── train_operational_readouts.csv (1:N por veículo — múltiplos time_steps)

vehicle_id (PK, apenas val/test)
   ├── validation_labels.csv   (1:1)
   ├── validation_specifications.csv (1:1)
   └── validation_operational_readouts.csv (1:N)
```

**Joins confirmados:** `vehicle_id` está presente em todos os arquivos e é o único campo de junção.
