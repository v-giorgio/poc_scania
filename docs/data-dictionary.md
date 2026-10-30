# Dicionário de dados — SCANIA Component X (IDA 2024)

Os nomes, tipos observados, nulabilidade e chaves abaixo vêm dos oito CSVs oficiais em `dataset_local/`; agregados são recalculáveis com `scripts/run_discovery.py`. As semânticas documentadas vêm do chamado `papers/2024_IDA_challenge_v2.pdf`. A documentação não define o significado físico dos códigos numéricos nem a inclusão dos limites temporais.

## Arquivos oficiais

| Arquivo | Grão | Chave | Conteúdo |
|---|---|---|---|
| `train_tte.csv` | Um registro por veículo | `vehicle_id` | Duração até o primeiro reparo observado ou duração de acompanhamento censurada. |
| `train_operational_readouts.csv` | Leitura por veículo e instante | `(vehicle_id, time_step)` | Contadores/histogramas anonimizados ao longo do tempo. |
| `train_specifications.csv` | Um registro por veículo | `vehicle_id` | Categorias de especificação selecionadas por especialistas. |
| `validation_labels.csv` | Um rótulo por veículo | `vehicle_id` | Classe da última leitura disponibilizada na validação oficial. |
| `validation_operational_readouts.csv` | Série truncada por veículo | `(vehicle_id, time_step)` | Leituras disponíveis até o corte aleatório definido pelo desafio. |
| `validation_specifications.csv` | Um registro por veículo | `vehicle_id` | Categorias de especificação. |
| `test_operational_readouts.csv` | Série truncada por veículo | `(vehicle_id, time_step)` | Leituras até o corte aleatório definido pelo desafio; sem rótulos oficiais. |
| `test_specifications.csv` | Um registro por veículo | `vehicle_id` | Categorias de especificação. |

`test_labels.csv` não faz parte do pacote oficial e não é lido pelo pipeline. Se existir uma cópia local com esse nome, sua proveniência não está validada e ela não deve ser usada para avaliação.

## Campos e proveniência semântica

### `train_tte.csv`

| Coluna | Tipo observado | Nulos | Semântica e evidência |
|---|---|---:|---|
| `vehicle_id` | Inteiro | 0 | Identificador do veículo; observado como chave nos CSVs e descrito pelo chamado. |
| `length_of_study_time_step` | Numérico | 0 | Duração em unidades `time_step` desde o início de operação com Component X. Para eventos, tempo até o primeiro reparo; para `in_study_repair=0`, duração sem reparo observado. Fonte: chamado oficial, seção Training Data. |
| `in_study_repair` | Inteiro `{0,1}` | 0 | `1`: Component X reparado pela primeira vez na duração informada; `0`: nenhum reparo no período informado, tratado como censura à direita. Fonte: chamado oficial. |

O chamado confirma que o alvo é o **primeiro reparo observado**. Não há base para tratar a duração censurada como um reparo nem para inferir recorrência após esse primeiro reparo.

### `*_operational_readouts.csv`

| Colunas | Tipo observado | Nulos | Semântica e evidência |
|---|---|---:|---|
| `vehicle_id` | Inteiro | 0 | Identificador do veículo. |
| `time_step` | Numérico | 0 | Tempo relativo ao início de operação do veículo e Component X. A unidade é anonimizada; não converter para dias, horas ou distância. |
| 105 colunas com padrão `<variable_id>_<bin_index>` | Numérico | Presentes em 104 colunas no arquivo de treino observado | Contadores numéricos ou bins de histogramas de 14 variáveis anonimizadas. O chamado explica o formato do nome, mas não divulga o significado físico dos códigos. |

O chamado informa que as séries são esparsas e irregularmente amostradas, e que frequências de reparos e leituras podem ter sido modificadas. Os nulos são mantidos; nenhuma semântica de sensor é atribuída aos prefixos numéricos. A chave composta foi verificada sem duplicatas nos CSVs observados.

### `*_specifications.csv`

| Colunas | Tipo observado | Nulos | Semântica e evidência |
|---|---|---:|---|
| `vehicle_id` | Inteiro | 0 | Identificador do veículo. |
| `Spec_0`–`Spec_7` | String categórica (`CatN`) | 0 | Especificações selecionadas por especialistas; o chamado cita tipo de motor e configuração de rodas como exemplos, mas não mapeia cada coluna a um atributo. |

### `validation_labels.csv`

| Coluna | Tipo observado | Nulos | Semântica e evidência |
|---|---|---:|---|
| `vehicle_id` | Inteiro | 0 | Identificador do veículo da validação. |
| `class_label` | Inteiro `{0,1,2,3,4}` | 0 | Rótulo da última leitura fornecida para o veículo. A validação serve para avaliação prevista pelo desafio, não para treino ou tuning. |

O chamado oficial define as janelas 1–4 antes do primeiro evento: classe 1 entre 48 e 24 unidades; classe 2 entre 24 e 12; classe 3 entre 12 e 6; classe 4 entre 6 e 0. A classe 0 representa a classe restante sem evento iminente dentro do horizonte de 48 unidades. A publicação não especifica se as pontas das janelas são inclusivas; por isso o código não deriva rótulos para tempos residuais exatamente iguais a 0, 6, 12, 24 ou 48.

Para treino ordinal derivado, a classe 0 só é conhecida se o evento ocorrer depois de 48 unidades residuais ou se houver mais de 48 unidades completas de acompanhamento censurado sem evento. Censura abaixo de 48 ou exatamente na fronteira é desconhecida, não classe 0.

## Junções e split

`vehicle_id` é a chave de junção entre arquivos de cada partição. A discovery valida igualdade de conjuntos de IDs entre TTE, especificações e readouts de treino; entre labels/specs/readouts de validação; e entre specs/readouts de teste. Também verifica que os IDs não se sobrepõem entre partições oficiais.

No split interno de modelagem, a partição é feita por veículo antes de derivar snapshots ou ajustar preprocessadores. O snapshot de treino é uma leitura pseudoaleatória determinística, estritamente anterior ao primeiro reparo ou fim do acompanhamento. A saída Gold registra `prediction_time`, tempo residual, evento/censura e caminhos/SHA-256 das fontes Raw.
