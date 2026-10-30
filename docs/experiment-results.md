# Estado de execução e resultados

## Estado

- **Discovery local:** executada em 2026-10-30 por `scripts/run_discovery.py` sobre os oito CSVs oficiais já disponíveis em `dataset_local/`. O relatório contém apenas contagens, schemas, taxas agregadas, integridade de chaves e distribuição dos rótulos de validação; nenhum registro bruto foi copiado para a documentação.
- **Testes unitários:** `python -m pytest tests/unit/ -q` passou com 84 testes em 2026-10-30. Há um aviso do scikit-learn em um teste ordinal porque uma predição contém uma classe ausente no `y_true`; o resultado esperado foi validado.
- **Lint e formatação:** `ruff check src/ tests/` passou; `ruff format --check src/ tests/` passou com 35 arquivos formatados.
- **Validação estrutural:** `python scripts/validate_structure.py` passou, conferindo 16 caminhos obrigatórios. `git diff --check` não encontrou erros de whitespace.
- **Sintaxe dos notebooks:** 10 arquivos `.py` em `notebooks/` passaram pelo parser Python; isso não executa as células nem integra com Spark.
- **Databricks Free Edition com volume UC:** ainda não executada neste ambiente. Portanto, não há métricas de modelos, tabelas UC geradas ou uso/quota do workspace reportados como resultados medidos.

## Métricas futuras

Quando a execução na Free Edition for realizada, registrar nesta página data, revisão de código, SHA-256 dos CSVs Raw, seed, split, política de snapshot, horizonte e suporte, métricas de treino/validação interna/teste interno, número de casos por métrica e avaliação ordinal oficial de validação. Informar métricas RUL como condicionais aos eventos observados; não reportar métrica supervisionada para o teste oficial sem rótulos.

Até lá, interprete os notebooks como pipeline implementado/configurável, não como execução comprovada nem evidência de desempenho. As verificações registradas acima cobrem módulos locais e fixtures sintéticas; não validam execução Spark/Delta, permissões UC, quotas serverless ou escalabilidade com o dataset completo.
