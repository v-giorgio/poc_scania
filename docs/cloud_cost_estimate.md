# Estimativa de Custos Cloud (PoC)

> Estimativas aproximadas para uso pontual em PoC. Revisar antes de escalar.
> Preços baseados em us-east-1, outubro 2026.

## AWS S3

| Item | Volume | Estimativa/mês |
|------|--------|---------------|
| Dataset Raw (~50 MB) | 0,05 GB | < $0,01 |
| Silver + Gold (Delta) ~200 MB | 0,2 GB | < $0,01 |
| Transferência de dados | Negligível para PoC | < $0,01 |
| **Total S3** | | **< $1/mês** |

## Databricks

| Cenário | Estimativa |
|---------|-----------|
| Community Edition (gratuito, sem jobs) | $0 |
| Trial ou workspace pago — exploração (4h, cluster pequeno) | $2–8 |
| Trial — treinamento de modelos (2h) | $1–4 |
| **Total Databricks (PoC pontual)** | **$0–15** |

## Notas
- **Databricks Community Edition** é gratuito mas não suporta jobs agendados — suficiente para PoC interativa
- Usar **Spot Instances** no cluster para reduzir custo em ~70%
- Desligar clusters imediatamente após uso
- Custos reais dependem da configuração do workspace e região AWS
- Para entrevista/demonstração: Community Edition elimina custo Databricks
