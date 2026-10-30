# Arquitetura da PoC

## Fluxo lógico

```text
CSVs oficiais em Unity Catalog managed volume (Raw; somente leitura após upload)
        ↓ leitura direta pelo Databricks serverless
Tabelas UC Bronze Delta: bronze_<arquivo> + caminho/SHA-256/tamanho/horário
        ↓ discovery e quality checks leem Bronze
        ↓ cast + contratos + integridade de joins
Tabelas UC Silver Delta: silver_<artefato>
        ↓ split por veículo → corte temporal → transformações ajustadas no treino
Tabelas UC Gold Delta: gold_train_fit / gold_internal_validation / gold_internal_test
                     gold_challenge_validation / gold_challenge_test
        ↓ Kaplan–Meier / CoxPH / RUL eventos / ordinal conhecido
MLflow gerenciado pelo workspace: parâmetros, métricas e artefatos
```

## Camadas e reexecução

| Camada | Conteúdo | Regra |
|---|---|---|
| Volume Raw | CSVs originais enviados ao diretório `/raw` do volume gerenciado | Imutável por convenção depois do upload; pipeline não modifica a origem. |
| Bronze UC/Delta | Uma tabela por arquivo com `_source_uri`, `_source_version` (SHA-256), `_source_size_bytes` e `_ingested_at` | Ingestão sobrescreve a tabela gerenciada por arquivo em vez de anexar duplicatas. |
| Silver UC/Delta | Tipos validados, dados normalizados e linhagem da fonte | Quality gate interrompe a execução em violações críticas; sem partição por identificador de alta cardinalidade. |
| Gold UC/Delta | Snapshots por veículo, corte, alvos residuais identificáveis, features e hashes das fontes | Split por veículo primeiro; imputação/indexação ajustada somente em `train_fit`. |

As tabelas seguem o padrão `<catalog>.<schema>.<layer>_<artifact>`, por exemplo `main.default.bronze_train_tte` e `main.default.gold_train_fit`. O catálogo e schema são configurados em `DATA_SCHEMA`; o caminho Raw em `RAW_VOLUME_PATH`.

## Ordem efetiva dos notebooks

As etapas são iniciadas manualmente, uma de cada vez, em compute serverless; não há um Job orquestrador configurado.

1. `03_data_preparation/01_ingest_raw.py`: lê os CSVs do volume e grava Bronze.
2. `02_data_understanding/01_data_exploration.py` e `02_data_quality.py`: leem Bronze para discovery e quality checks.
3. `03_data_preparation/02_silver_transform.py`: valida contratos e joins e grava Silver.
4. `03_data_preparation/03_gold_features.py`: cria snapshots/features e grava Gold.
5. `04_modeling/01_baseline_model.py`: ajusta e registra os modelos e métricas no MLflow.
6. `05_evaluation/01_model_evaluation.py`: carrega os runs informados e registra a avaliação final.

`06_deployment/01_deployment_concept.py` documenta possibilidades futuras; não implementa scoring, Job agendado, endpoint de serving ou publicação de modelo. O MLflow Tracking e os artefatos por run são usados, mas o Model Registry não está configurado.

## Alvo, cortes e avaliação

O alvo principal é o tempo residual até o primeiro reparo observado do Component X, com censura à direita preservada. Em treino é escolhida uma leitura pseudoaleatória determinística por veículo, entre leituras estritamente anteriores ao tempo de evento/fim de acompanhamento. O snapshot não inclui TTE absoluto nem a flag de evento como feature.

As leituras oficiais de validação/teste já terminam no corte aleatório do desafio. Validação traz `class_label` e é usada somente na avaliação final; teste não traz rótulo e não recebe métrica supervisionada.

## Componentes e ambiente

- **Databricks Free Edition serverless:** execução pessoal/não comercial, sem cluster AWS configurado pelo usuário; compute sujeito a quotas.
- **Unity Catalog managed volume:** armazenamento Raw acessado por caminho absoluto `/Volumes/...`.
- **Tabelas UC/Delta:** Bronze, Silver e Gold gerenciadas no schema configurado; sem paths S3.
- **lifelines / scikit-learn:** benchmarks de sobrevivência, RUL e classificação ordinal sobre Gold compacto.
- **MLflow:** parâmetros, hashes de origem, revisão de código, métricas e artefatos no workspace.
- **Ambiente local:** testes unitários/sintéticos, helpers puros, lint e checagem de estrutura; não simula a execução do workspace.

Consulte [setup](setup.md), [modelagem e avaliação](modeling-and-evaluation.md) e [resultados](experiment-results.md). Para os limites da Free Edition e o uso com ~1,5 GB, veja [setup](setup.md).
