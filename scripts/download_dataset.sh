#!/usr/bin/env bash
# Download do dataset SCANIA APS Failure
#
# AVISO: Este dataset requer aceite manual de licença.
# Verifique os termos antes de executar qualquer automação.
#
# Fontes:
#   UCI ML Repository: https://archive.ics.uci.edu/dataset/421/aps+failure+at+scania+trucks
#   Kaggle:            https://www.kaggle.com/datasets/uciml/aps-failure-at-scania-trucks-data-set

set -euo pipefail

echo "========================================"
echo " SCANIA APS Failure — Download do Dataset"
echo "========================================"
echo ""
echo "Este script NÃO faz o download automaticamente."
echo "O dataset requer aceite manual da licença."
echo ""
echo "Passos:"
echo "  1. Acesse um dos links acima e aceite os termos de uso"
echo "  2. Faça o download dos arquivos: aps_failure_training_set.csv, aps_failure_test_set.csv"
echo "  3. Coloque os arquivos em um diretório temporário (ex: /tmp/scania_dataset/)"
echo "  4. Execute o upload para o S3:"
echo ""
echo "  aws s3 cp /tmp/scania_dataset/ s3://\${S3_BUCKET}/raw/scania_component_x/ --recursive"
echo ""
echo "Variáveis de ambiente necessárias: S3_BUCKET"
echo "Não commitar os arquivos CSV no repositório."
