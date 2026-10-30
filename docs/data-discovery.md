# Data Discovery — SCANIA Component X (IDA 2024)

> Gerado a partir da inspeção dos arquivos CSV em `dataset_local/` e dos PDFs em `papers/`.
> Todos os números foram calculados programaticamente. Hipóteses de semântica são marcadas como [HIPÓTESE].

---

## 1. Arquivos do Dataset

| Arquivo | Linhas | Colunas | Missings | Descrição |
|---|---|---|---|---|
| `train_operational_readouts.csv` | 1.122.452 | 107 | 354.634 (~0,86% das células) | Leituras de sensores por veículo × time_step (treino) |
| `train_tte.csv` | 23.550 | 3 | 0 | TTE e status de evento por veículo (treino) |
| `train_specifications.csv` | 23.550 | 9 | 0 | Especificações categóricas do veículo (treino) |
| `validation_operational_readouts.csv` | 196.227 | 107 | 60.339 (~1,0%) | Leituras operacionais (validação) |
| `validation_labels.csv` | 5.046 | 2 | 0 | Classes ordinais por veículo (validação) |
| `validation_specifications.csv` | 5.046 | 9 | 0 | Especificações do veículo (validação) |
| `test_operational_readouts.csv` | 198.140 | 107 | 66.403 (~1,0%) | Leituras operacionais (teste) |
| `test_labels.csv` | 5.045 | 2 | 0 | Classes ordinais por veículo (teste) |
| `test_specifications.csv` | 5.045 | 9 | 0 | Especificações do veículo (teste) |

**Total de veículos:** 23.550 (treino) + 5.046 (validação) + 5.045 (teste) = **33.641 veículos**

---

## 2. Dataset de Treino: TTE e Eventos

**Arquivo:** `train_tte.csv` — colunas: `vehicle_id`, `length_of_study_time_step`, `in_study_repair`

| Métrica | Valor |
|---|---|
| Total de veículos | 23.550 |
| Eventos (in_study_repair = 1) | 2.272 |
| Censurados (in_study_repair = 0) | 21.278 |
| Taxa de evento | **9,64%** |

**Distribuição do TTE (length_of_study_time_step):**

| Estatística | Todos (n=23.550) | Apenas eventos (n=2.272) |
|---|---|---|
| Mínimo | 73,4 | 73,4 |
| P25 | — | 148,6 |
| Mediana | 218,2 | 208,4 |
| P75 | — | 276,2 |
| Máximo | 510,0 | 482,0 |

> **Nota:** Todos os valores de TTE estão acima de 48 time_steps. A unidade é anonimizada (não é dias/km).

---

## 3. Dataset de Leituras Operacionais

**Arquivos:** `*_operational_readouts.csv` — 107 colunas: `vehicle_id`, `time_step` + 105 features de sensores

### Estrutura temporal (treino)

| Métrica | Valor |
|---|---|
| Total de linhas | 1.122.452 |
| Veículos únicos | 23.550 |
| Leituras/veículo mínimo | 5 |
| Leituras/veículo mediana | 43 |
| Leituras/veículo máximo | 303 |
| time_step mínimo | 0,0 |
| time_step máximo | 507,4 |

### Valores ausentes nas features

- **100/105 colunas** apresentam valores ausentes
- **Máximo de missings:** grupo `291` (~0,86% das linhas)
- **Segundo maior:** grupo `459` (~0,74% das linhas)
- **Nenhuma coluna** ultrapassa 1% de missing
- O padrão de ausência é em bloco por grupo de sensores (todas as colunas do grupo 291 faltam juntas)
- **Não há string `"na"`** como sentinel — os missings são valores nulos reais (NaN/null)

### Grupos de sensores (105 features)

| Grupo | Colunas | Exemplo | Missing? |
|---|---|---|---|
| 171 | 1 | 171_0 | Não |
| 666 | 1 | 666_0 | Não |
| 427 | 1 | 427_0 | Não |
| 837 | 1 | 837_0 | Não |
| 167 | 10 | 167_0..167_9 | Não |
| 309 | 1 | 309_0 | Não |
| 272 | 10 | 272_0..272_9 | Não |
| 835 | 1 | 835_0 | Não |
| 370 | 1 | 370_0 | Não |
| 291 | 11 | 291_0..291_10 | **Sim (~0,86%)** |
| 158 | 10 | 158_0..158_9 | Sim (baixo) |
| 100 | 1 | 100_0 | Não |
| 459 | 20 | 459_0..459_19 | **Sim (~0,74%)** |
| 397 | 36 | 397_0..397_35 | Sim (baixo) |

---

## 4. Especificações dos Veículos

**Arquivo:** `train_specifications.csv` — colunas: `vehicle_id`, `Spec_0`..`Spec_7`

| Coluna | Valores únicos | Cardinalidade |
|---|---|---|
| Spec_0 | Cat0, Cat1, Cat2 | 3 |
| Spec_1 | Cat0..Cat28 | 29 |
| Spec_2 | Cat0..Cat20 | 21 |
| Spec_3 | Cat0..Cat3 | 4 |
| Spec_4 | Cat0, Cat1 | 2 |
| Spec_5 | Cat0..Cat4 | 5 |
| Spec_6 | Cat0..Cat18 (com gaps) | 17 |
| Spec_7 | Cat0..Cat8 | 9 |

- Sem valores ausentes
- Todos os valores são strings do padrão `CatN`

---

## 5. Classes Ordinais (Validação e Teste)

**[HIPÓTESE — confirmar com papers/2024_IDA_challenge_v2.pdf]**

A semântica exata das classes ordinais deve ser transcrita do paper oficial antes de uso em modelos.

### Distribuição observada

**Validação (n=5.046):**

| Classe | Contagem | % |
|---|---|---|
| 0 | 4.910 | 97,3% |
| 1 | 16 | 0,3% |
| 2 | 14 | 0,3% |
| 3 | 30 | 0,6% |
| 4 | 76 | 1,5% |

**Teste (n=5.045):**

| Classe | Contagem | % |
|---|---|---|
| 0 | 4.903 | 97,2% |
| 1 | 26 | 0,5% |
| 2 | 15 | 0,3% |
| 3 | 41 | 0,8% |
| 4 | 60 | 1,2% |

**Observação crítica:** A classe 0 domina com ~97% dos veículos. Dado que os TTE de treino estão todos acima de 48 time_steps, a hipótese mais provável é:
- Classe 0 = veículo censurado ou com TTE > 48 time_steps a partir do ponto de predição
- Classes 1–4 = veículos com reparo iminente em janelas crescentemente próximas

Isso é o **inverso** do ordenamento ascendente implícito (0=mais urgente). **Confirmar com paper antes de modelar.**

---

## 6. Verificação de Sobreposição entre Splits

Verificar que nenhum `vehicle_id` aparece em mais de um split é obrigatório (SPEC.md §5).

```python
# executar após carregar os três splits
from src.scania_poc.discovery import find_vehicles_in_multiple_splits
overlaps = find_vehicles_in_multiple_splits(train_ids, val_ids, test_ids)
assert all(v == 0 for v in overlaps.values()), f"Sobreposição detectada: {overlaps}"
```

(Esta verificação deve ser executada no notebook 02_data_understanding/02_data_quality.py)

---

## 7. Anomalias e Pontos de Atenção

1. **Padrão de missing em bloco:** Os grupos 291 e 459 têm todas as suas sub-colunas faltando juntas — provavelmente por ausência de leitura do sensor naquele time_step, não por dado corrompido.
2. **time_step não começa em 0 para todos os veículos:** O mínimo é 0, mas veículos distintos podem ter time_steps com granularidade diferente (observe 11.2, 11.4, 19.6 no exemplo).
3. **Unidade de tempo anonimizada:** Não converter `time_step` para dias/km sem evidência do paper.
4. **Classe 0 domina 97%:** Desequilíbrio severo na validação/teste — estratégia de threshold ou custo assimétrico necessária.
5. **TTE nunca < 73 no treino:** Sugere que o dataset de treino foi filtrado ou que o estudo começa após um período de burn-in.

---

## 8. Próximos Passos (Fase 3)

- [ ] Transcrever as regras exatas de classe do `papers/2024_IDA_challenge_v2.pdf`
- [ ] Confirmar se classe 0 = censurado/48+ ou 0-6 time_steps
- [ ] Criar `config/data_contract.yaml` baseado nesta discovery
- [ ] Atualizar `src/scania_poc/schema.py` com `ORDINAL_CLASSES` correto
