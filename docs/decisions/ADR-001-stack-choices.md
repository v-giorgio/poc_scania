# ADR-001: Escolha da Stack Tecnológica

**Status:** Aceito
**Data:** 2026-10-29
**Contexto:** Definição da stack para PoC de manutenção preditiva com SCANIA Component X (IDA 2024)

## Decisão

| Componente | Escolha | Alternativas Consideradas |
|------------|---------|--------------------------|
| Raw | Unity Catalog managed volume | AWS S3, Azure ADLS, GCS |
| Camadas tabulares | Tabelas UC gerenciadas em Delta | Paths Delta externos |
| Processamento | Databricks + PySpark | EMR + Spark, AWS Glue |
| Tracking ML | MLflow (nativo Databricks) | Weights & Biases, SageMaker |
| Código auxiliar | Python 3.11 + ruff | — |
| Testes | pytest | unittest |
| Gerenciamento de deps | uv | pip, poetry |

## Justificativa

- **Databricks:** amplamente adotado em logística e frotas conectadas; integra Spark, Delta e MLflow nativamente
- **Unity Catalog volumes/tabelas:** armazenamento gerenciado simples para execução pessoal na Free Edition; SHA-256 dá identidade reprodutível à origem Raw.
- **Delta Lake:** ACID e reexecução idempotente via tabelas gerenciadas no Unity Catalog.
- **MLflow:** integrado ao Databricks, reduz fricção operacional; open-source e portável
- **ruff:** linting e formatação em um único binário rápido, substitui flake8 + isort + black
- **uv:** gerenciamento de ambientes e dependências mais rápido que pip/poetry
- Stack alinhada ao perfil técnico de Engenharia de Dados / ML em contexto de frotas (Michelin Connected Fleet)

## Consequências

- **Custo/limites:** Free Edition é limitada por quotas e apropriada somente para uso pessoal/não comercial. Ver `docs/cloud_cost_estimate.md`.
- **Lock-in:** moderado — Delta Lake tem implementação open-source (delta-rs), MLflow é portável
- **Dataset SCANIA Component X:** aquisição manual pela fonte oficial; a PoC não automatiza download.
- **Databricks:** exige volume e schema UC gerenciados; compute serverless e quotas são determinados pela Free Edition.
