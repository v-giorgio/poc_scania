# Recursos e limites de execução

O caminho pessoal desta PoC usa Databricks Free Edition e armazenamento gerenciado pelo Unity Catalog, sem bucket S3 ou cluster provisionado pelo usuário. Não há estimativa numérica de custo; a Free Edition é limitada por quotas e os ~1,5 GB referem-se apenas aos CSVs Raw, não às cópias Delta geradas.

## Itens a acompanhar

| Componente | Consideração |
|---|---|
| Volume Raw | Tamanho dos oito arquivos e disponibilidade do volume após upload. |
| Tabelas Delta | Bronze e Silver materializam cópias; Gold acrescenta snapshots e features. Espaço total supera o Raw. |
| Compute serverless | Quota diária/uso justo da Free Edition; uma execução longa pode ser pausada até a quota renovar. |
| Upload | Transferência dos CSVs locais (~1,5 GB) para o volume UC; limite UI documentado de 5 GB por arquivo. |

Execute notebooks em sequência e confira o estado depois de cada camada. A execução completa no dataset só será considerada validada depois de concluída no workspace. Se migrar para workspace pago ou cloud externa, estimar compute, armazenamento e transferência com preços vigentes antes de executar.
