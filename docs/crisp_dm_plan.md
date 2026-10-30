# Plano CRISP-DM

## 1. Entendimento do Negócio
- **Problema:** falhas no sistema de pressão de ar (APS) de caminhões Scania causam paradas não planejadas
- **Objetivo:** classificar veículos com risco de falha antes que ocorra
- **Métrica de negócio:** redução de falhas não planejadas; custo de manutenção evitada
- **Critério de sucesso:** AUC-ROC > 0.85 e custo total (10*FP + 500*FN) abaixo do baseline

Notebook: `notebooks/01_business_understanding/01_business_context.py`

## 2. Entendimento dos Dados
- **Dataset:** SCANIA APS Failure (UCI / Kaggle)
- ~60.000 amostras de treino, ~16.000 de teste
- 171 atributos anonimizados de sensores do APS
- Alta taxa de missing values (~170 colunas com missings)
- Target binário: `class` = `pos` (falha APS) / `neg` (outra falha ou normal)
- **Custo assimétrico:** FN custa 50x mais que FP (500 vs 10 no contexto original)

Notebooks: `notebooks/02_data_understanding/`

## 3. Preparação dos Dados
- Ingestão do CSV para S3 Raw (sem transformações)
- Limpeza e tipagem → Silver (Delta Lake)
- Imputação de missings, encoding, seleção de features → Gold (Delta Lake)

Notebooks: `notebooks/03_data_preparation/`

## 4. Modelagem
- Baseline: Regressão Logística
- Candidatos: Random Forest, XGBoost, LightGBM
- Tracking de todos os experimentos via MLflow

Notebooks: `notebooks/04_modeling/`

## 5. Avaliação
- Métricas: AUC-ROC, F1, matriz de confusão, custo total
- Comparação de modelos no MLflow UI
- Análise de feature importance (SHAP se viável)

Notebook: `notebooks/05_evaluation/01_model_evaluation.py`

## 6. Implantação (Conceitual)
- **Opção A (PoC):** batch scoring via Databricks Job agendado
- **Opção B (produção):** endpoint REST via MLflow Model Serving
- Monitoramento de drift: a definir

Notebook: `notebooks/06_deployment/01_deployment_concept.py`
