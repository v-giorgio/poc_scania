# ADR-001: Escolha da Stack Tecnológica

**Status:** Aceito
**Data:** 2026-10-29
**Contexto:** Definição da stack para PoC de manutenção preditiva com SCANIA APS Failure

## Decisão

| Componente | Escolha | Alternativas Consideradas |
|------------|---------|--------------------------|
| Armazenamento | AWS S3 + Delta Lake | Azure ADLS, GCS |
| Processamento | Databricks + PySpark | EMR + Spark, AWS Glue |
| Tracking ML | MLflow (nativo Databricks) | Weights & Biases, SageMaker |
| Código auxiliar | Python 3.11 + ruff | — |
| Testes | pytest | unittest |
| Gerenciamento de deps | uv | pip, poetry |

## Justificativa

- **Databricks:** amplamente adotado em logística e frotas conectadas; integra Spark, Delta e MLflow nativamente
- **Delta Lake:** ACID + time travel sobre S3 sem custo de serviço gerenciado adicional
- **MLflow:** integrado ao Databricks, reduz fricção operacional; open-source e portável
- **ruff:** linting e formatação em um único binário rápido, substitui flake8 + isort + black
- **uv:** gerenciamento de ambientes e dependências mais rápido que pip/poetry
- Stack alinhada ao perfil técnico de Engenharia de Dados / ML em contexto de frotas (Michelin Connected Fleet)

## Consequências

- **Custo:** Databricks DBU + S3. Ver `docs/cloud_cost_estimate.md`
- **Lock-in:** moderado — Delta Lake tem implementação open-source (delta-rs), MLflow é portável
- **Dataset SCANIA:** verificar licença antes de automatizar o download
- **Databricks Community Edition:** gratuito com limitações (sem jobs agendados) — suficiente para PoC
