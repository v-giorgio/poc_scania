# Modelagem e avaliação

## Unidade de análise e alvo

O alvo principal é tempo/unidades residuais até o primeiro reparo observado do Component X. Para cada veículo de treino, o fluxo primeiro fixa a partição determinística por `vehicle_id` (70/15/15, estratificada por indicador de evento, seed padrão 42). Em seguida, seleciona um readout pseudoaleatório determinístico por veículo via hash estável de veículo, seed e `time_step`, dentre os readouts com `time_step < length_of_study_time_step`.

Gold registra `prediction_time`, `residual_time = T - prediction_time`, `event_observed`, features dessa leitura e linhagem das fontes. A leitura no evento ou após o evento/fim de acompanhamento não é elegível. Veículos sem leitura elegível são excluídos com contagem explícita. TTE absoluto e flag de evento originais nunca entram como features.

Validation/test oficiais já terminam no corte aleatório fornecido pelo desafio; Gold escolhe a última leitura desse subconjunto e não usa rótulos durante o processamento de features. Preprocessadores Spark são ajustados apenas em `train_fit` e depois aplicados às demais partições.

## Censura e alvo ordinal

- `event_observed=1`: primeiro reparo observado depois do corte; duração residual é evento.
- `event_observed=0`: acompanhamento termina sem reparo; duração residual é censurada à direita.
- RUL usa somente eventos observados e seus erros são métricas completas/seletivas, não corrigidas para censura.
- Ordinal: classe 0 requer evento após 48 unidades residuais ou censura além de 48 unidades completas observadas. Classes 1–4 são eventos em `(24,48)`, `(12,24)`, `(6,12)` e `(0,6)`.
- A chamada oficial não estabelece inclusão exata dos limites; resíduos exatamente 0, 6, 12, 24 ou 48 (inclusive censura em 48) e censuras abaixo de 48 unidades ficam sem rótulo derivado e são excluídos só do benchmark ordinal.
- Rótulos oficiais de validação entram somente no notebook de avaliação final. Não há rótulos oficiais no teste.

## Protocolo de treino

1. Separar veículos antes de gerar os snapshots: 70% `train_fit`, 15% `internal_validation`, 15% `internal_test`, seed 42 por padrão.
2. Ajustar indexação categórica e mediana de imputação somente em `train_fit`; categorias novas na validação usam tratamento `keep`, transformações numéricas são alinhadas às colunas treinadas.
3. Comparar modelos em `internal_validation`; reservar `internal_test` para uma única avaliação final.
4. Usar validation labels oficiais apenas uma vez após o modelo escolhido. Não consultar rótulos do teste.

## Modelos e métricas

| Tarefa | Modelos | Métricas e ressalvas |
|---|---|---|
| Sobrevivência principal | Kaplan–Meier marginal e Cox PH com penalização L2 | Harrell C-index; IBS com IPCW, estimando sobrevivência de censura por Kaplan–Meier no treino; comparação de sobrevivência média prevista com KM observada nos horizontes; quantis/horizontes reportados somente no suporte. Cox exige revisão do pressuposto de riscos proporcionais. |
| RUL benchmark | Random Forest Regressor | MAE, mediana do erro absoluto e RMSE apenas em veículos com reparo observado; informar `n` e possível viés de seleção. |
| Ordinal benchmark | Majority baseline e Random Forest balanceado | Matriz de confusão, recall por classe, balanced accuracy, macro-F1, MAOE e custo oficial. Treino exclui classes desconhecidas. |

Matriz de custo oficial (linhas = classe real, colunas = classe prevista):

```text
             prevista 0  1  2  3  4
real 0              0  7  8  9 10
     1            200  0  7  8  9
     2            300 200  0  7  8
     3            400 300 200  0  7
     4            500 400 300 200  0
```

O IBS usa a fórmula IPCW: eventos até `t` ponderados por `1/G(T_i-)`, observações que permanecem sob risco após `t` ponderadas por `1/G(t)` e censurados antes de `t` sem contribuição observada. `G` é estimada no conjunto de treino como Kaplan–Meier da censura (`1 - event_observed`). Horizontes sem suporte (`G(t)=0`) interrompem o cálculo; não são extrapolados.

## MLflow e rastreabilidade

Cada run registra seed, proporções, política do corte, caminhos e SHA-256 dos CSVs Raw que compõem Gold, revisão informada do código, versões Python/lifelines/scikit-learn/MLflow, parâmetros, métricas e artefatos de modelo/calibração. O experimento é criado sob a pasta pessoal do usuário atual no workspace (`/Users/<usuário>/poc_scania_component_x`), sem exigir uma pasta pai previamente criada. Configure `GIT_REVISION` com a revisão real; o valor `unknown` sinaliza ausência dela.

## Limitações

- O split interno por veículo não substitui a avaliação oficial do desafio.
- Um snapshot aleatório por veículo aproxima o corte oficial, mas não reproduz a política privada de amostragem do desafio.
- Classe ordinal derivada de TTE e censura pode não reproduzir rótulos em fronteiras ambíguas; os pontos exatos são omitidos.
- C-index isolado não prova calibração; RUL não considera censurados; associações não são causais.
- Nenhum métrico/resultado implica desempenho produtivo ou generalização a outras frotas/componentes.
