# Data Discovery — SCANIA Component X (IDA 2024)

> Relatório agregado recalculado em 2026-10-30 por `scripts/run_discovery.py`.
> Nenhum registro bruto é escrito no relatório. Tipos são os nomes originais do CSV; parsing validado separadamente.

## Inventário oficial

| Arquivo | Linhas | Colunas | Veículos | Células ausentes | Bytes | Chaves duplicadas |
|---|---:|---:|---:|---:|---:|---:|
| `train_tte.csv` | 23,550 | 3 | 23,550 | 0 | 345,412 | 0 |
| `train_operational_readouts.csv` | 1,122,452 | 107 | 23,550 | 354,634 | 1,219,209,878 | 0 |
| `train_specifications.csv` | 23,550 | 9 | 23,550 | 0 | 1,081,118 | 0 |
| `validation_labels.csv` | 5,046 | 2 | 5,046 | 0 | 38,742 | 0 |
| `validation_operational_readouts.csv` | 196,227 | 107 | 5,046 | 60,339 | 215,593,159 | 0 |
| `validation_specifications.csv` | 5,046 | 9 | 5,046 | 0 | 231,765 | 0 |
| `test_operational_readouts.csv` | 198,140 | 107 | 5,045 | 66,403 | 214,897,259 | 0 |
| `test_specifications.csv` | 5,045 | 9 | 5,045 | 0 | 231,658 | 0 |

## Integridade de chaves

- IDs por veículo coincidem entre os arquivos de cada partição.
- Sobreposição train/validation, train/test e validation/test: 0.
- Leituras operacionais verificadas por chave composta `(vehicle_id, time_step)`.

## TTE de treino

- Eventos observados: 2,272; censurados: 21,278; taxa de evento: 9.65%.
- Duração observada: min=73.400, P25=163.800, mediana=218.200, P75=312.000, max=510.000.
- Unidade: `time_step` anonimizado; não converter para calendário ou distância.

## `train_operational_readouts.csv`

- Veículos: 23,550; time_step observado: 0.0–507.4.
- Leituras por veículo: min=5, mediana=43.0, max=303.
- Chaves duplicadas `(vehicle_id, time_step)`: 0.
- Features com ausências: 104.

## `validation_operational_readouts.csv`

- Veículos: 5,046; time_step observado: 0.0–456.6.
- Leituras por veículo: min=1, mediana=34.0, max=209.
- Chaves duplicadas `(vehicle_id, time_step)`: 0.
- Features com ausências: 104.

## `test_operational_readouts.csv`

- Veículos: 5,045; time_step observado: 0.0–447.6.
- Leituras por veículo: min=1, mediana=34.0, max=262.
- Chaves duplicadas `(vehicle_id, time_step)`: 0.
- Features com ausências: 104.

## Rótulos oficiais de validação

- Classe 0: 4,910 (97.30%).
- Classe 1: 16 (0.32%).
- Classe 2: 14 (0.28%).
- Classe 3: 30 (0.59%).
- Classe 4: 76 (1.51%).

O pacote oficial não contém `test_labels.csv`; arquivos locais com esse nome não são lidos por este relatório nem pelo pipeline.
A semântica de evento e das janelas ordinais está documentada em `docs/data-dictionary.md`; inclusão das fronteiras continua não especificada e os rótulos derivados nesses pontos ficam desconhecidos.

Diretório inspecionado: `dataset_local` (somente leitura).
