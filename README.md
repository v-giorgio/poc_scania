# PoC — Manutenção preditiva SCANIA Component X

Prova de conceito exploratória para estimar o tempo residual até o primeiro reparo observado do Component X no dataset associado ao desafio IDA 2024. O alvo não representa automaticamente falha mecânica, causalidade ou recomendação operacional.

## Stack e armazenamento

- **Databricks Free Edition:** notebooks Python em compute serverless para uso pessoal/não comercial.
- **Unity Catalog managed volume:** CSVs oficiais Raw, mantidos sem alteração após upload.
- **Tabelas UC gerenciadas em Delta:** Bronze, Silver e Gold.
- **lifelines / scikit-learn / MLflow:** benchmarks e rastreamento de experimentos no workspace.

## Setup e execução

Consulte [docs/setup.md](docs/setup.md) para criar o volume, carregar os oito arquivos oficiais (~1,5 GB), configurar o Git Folder e executar os notebooks na ordem. O pipeline local contém somente testes sintéticos; a execução completa depende das quotas disponíveis na Free Edition.

## Dados e metodologia

Use os arquivos e documentação do [dataset oficial SCANIA Component X](https://researchdata.se/en/catalogue/dataset/2024-34) e do [chamado IDA 2024](https://ida2024.blogs.dsv.su.se/industrial-challenge/). O pacote oficial não contém rótulos de teste. Consulte [SPEC.md](SPEC.md), [discovery](docs/data-discovery.md), [dicionário](docs/data-dictionary.md), [modelagem/avaliação](docs/modeling-and-evaluation.md) e [estado dos resultados](docs/experiment-results.md).

## Estrutura

- `src/scania_poc/`: lógica reutilizável, paths de volume/tabelas UC e funções puras testáveis localmente.
- `notebooks/`: fluxo Databricks em etapas CRISP-DM.
- `config/data_contract.yaml`: contratos para os oito CSVs oficiais.
- `docs/experiment-results.md`: verificações locais e estado da execução no workspace.
