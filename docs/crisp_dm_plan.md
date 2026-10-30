# Plano CRISP-DM — SCANIA Component X

## 1. Entendimento do negócio

- Pergunta: qual a distribuição do tempo/unidades até o primeiro reparo observado do Component X no instante de previsão?
- A PoC é exploratória. Priorização de inspeções, disponibilidade e economia são hipóteses de valor a validar com stakeholders; não são resultados demonstrados.
- Não inferir falha mecânica geral, causalidade, segurança ou prontidão para produção.

Notebook: `notebooks/01_business_understanding/01_business_context.py`.

## 2. Entendimento dos dados

- Dataset público SCANIA Component X associado ao desafio IDA 2024; inventário de oito CSVs oficiais em `docs/data-discovery.md`.
- `train_tte.csv` descreve primeiro reparo observado ou fim de acompanhamento censurado. Unidade temporal anonimizada.
- Readouts são séries esparsas/irregulares; identificadores de variáveis são anônimos. Rótulos oficiais só existem para validação, não para teste.
- Tipos, chaves, ausências e proveniência estão em `docs/data-dictionary.md`; discovery é reproduzida por `scripts/run_discovery.py`.

## 3. Preparação

- Originais ficam em um Unity Catalog managed volume Raw, tratado como somente leitura depois do upload; Databricks lê diretamente para tabelas UC Bronze Delta com caminho e SHA-256 de linhagem.
- Validar schema, nulabilidade, chaves, valores e joins antes de Silver.
- Dividir veículos antes de selecionar uma leitura por veículo e antes de aprender encoding/imputação.
- Selecionar leitura determinística pseudoaleatória estritamente anterior ao evento/fim; calcular duração residual e censura sem transformar censurados em eventos.

## 4. Modelagem

- Baseline de sobrevivência Kaplan–Meier e CoxPH L2 regularizado.
- Benchmark RUL treinado/avaliado apenas em eventos observados, identificado como completo/seletivo.
- Random Forest ordinal treinado só em rótulos derivados válidos, sem rótulos para censura insuficiente ou fronteiras ambíguas.
- Regras, pressupostos, leakage e métricas em `docs/modeling-and-evaluation.md`.

## 5. Avaliação

- Split determinístico por veículo: treino interno, validação interna e teste interno.
- Sobrevivência: Harrell C-index, IBS IPCW com KM de censura aprendido no treino e calibração Kaplan–Meier por horizonte com suporte.
- RUL: MAE, mediana AE e RMSE somente nos eventos observados.
- Ordinal: matriz de confusão, recall por classe, balanced accuracy, macro-F1, MAOE e matriz de custo oficial IDA.
- Rótulos oficiais da validação são consultados apenas na avaliação final; conjunto de teste não tem rótulos e não recebe métrica supervisionada.

## 6. Entrega

- MLflow registra configurações, seed, split, versão dos objetos fonte, revisão de código, versões de bibliotecas, métricas e artefatos.
- A arquitetura é uma PoC cloud sem implantação produtiva, alertas ou custo/infraestrutura presumidos.
- Resultados e limites de execução ficam em `docs/experiment-results.md`.
