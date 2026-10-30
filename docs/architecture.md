# Arquitetura da PoC

## Visão Geral

```
[Dataset SCANIA] → [S3 Raw] → [Databricks Ingest] → [S3 Silver / Delta Lake]
                                                    → [S3 Gold / Delta Lake]
                                                    → [MLflow Tracking]
                                                    → [MLflow Model Registry]
```

## Camadas de Dados

| Camada | Localização S3 | Formato | Descrição |
|--------|---------------|---------|-----------|
| Raw    | `raw/scania_component_x/`      | CSV original  | Ingestão sem transformações |
| Silver | `silver/component_x/`          | Delta Lake    | Limpeza, tipagem, particionamento |
| Gold   | `gold/features_predictive/`    | Delta Lake    | Features prontas para modelagem |

## Componentes

### AWS S3
- Armazenamento durável e barato para todas as camadas
- Sem estrutura local para dados — tudo no S3
- Políticas IAM controlam acesso por camada

### Databricks
- Notebooks organizados por etapa CRISP-DM em `notebooks/`
- Código reutilizável de `src/` instalado como wheel ou via `%run`
- MLflow integrado nativamente ao workspace Databricks
- Cluster Spark para processamento distribuído com PySpark

### Delta Lake
- ACID sobre S3
- Schema enforcement e evolução controlada
- Time travel para auditoria e reprodutibilidade

### MLflow
- Experimentos organizados por etapa de modelagem
- Métricas: AUC-ROC, custo total (10*FP + 500*FN)
- Model Registry para versionamento conceitual do melhor modelo

### Python Local (`src/`)
- Módulos reutilizáveis com testes unitários
- Sem dependência de Spark para funções puras
- `scripts/` para automação pontual (download, validação)

## Decisões de Arquitetura
Ver `docs/decisions/` para ADRs detalhados.
