# Especificação técnica — PoC de manutenção preditiva SCANIA Component X

**Status:** proposta para validação durante a fase de entendimento dos dados  
**Público:** Claude Code e revisores do projeto  
**Idioma do projeto:** código e nomes técnicos em inglês; documentação explicativa em português, salvo decisão posterior.

## 1. Objetivo

Construir uma prova de conceito reproduzível de manutenção preditiva para o Component X, usando o dataset SCANIA Component X associado ao desafio IDA 2024. A pergunta analítica principal é: **dadas as informações disponíveis até um instante de observação, qual é a distribuição do tempo até o primeiro reparo observado do Component X?**

A abordagem principal será análise de sobrevivência, porque parte dos veículos pode não ter reparo observado até o fim do acompanhamento. A PoC também comparará, com ressalvas metodológicas explícitas, regressão de RUL e classificação ordinal inspirada nas classes do desafio. O resultado deve demonstrar um fluxo enxuto e auditável de S3 → Databricks/PySpark → Delta Lake → modelos → MLflow.

O uso pretendido é demonstrativo e exploratório. O conjunto não autoriza afirmar previsão de falha mecânica geral, diagnóstico causal, recomendação de segurança ou desempenho operacional em produção. O alvo deve ser referido como **tempo/unidades até reparo observado do Component X**, não como falha física, salvo se a documentação e os dados confirmarem essa equivalência.

## 2. Contexto conhecido e hipóteses a validar

O material do artigo/desafio consultado na conversa descreve, preliminarmente, os arquivos `train_operational_readouts.csv`, `train_tte.csv`, `train_specifications.csv` e rótulos de validação do desafio. Também sugere identificador de veículo, `time_step`, colunas de leituras, `length_of_study_time_step` e `in_study_repair`. Os números divulgados anteriormente (cerca de 1,12 milhão de leituras, 23.550 veículos, 107 colunas e aproximadamente 2.272 eventos) são **referências não verificadas pelo código**: recalcular e registrar valores reais a partir dos arquivos e da documentação fornecida.

As unidades temporais podem ter sido modificadas/anonimizadas pelo desafio. Não converter unidades em dias, horas, quilometragem ou tempo de calendário sem confirmação explícita. A semântica de “reparo”, a relação entre tabelas, o significado de cada coluna, a codificação de nulos/sentinelas, a granularidade e as regras das classes do desafio são hipóteses até validação documental e empírica.

## 3. Instruções obrigatórias para Claude Code

1. **Antes de implementar transformações ou modelos, inspecione todos os CSVs disponíveis, seus cabeçalhos, amostras, tipos, valores distintos relevantes, chaves, duplicatas e valores ausentes. Leia também os PDFs/documentação oficial do desafio presentes no projeto.** Se os dados não estiverem no repositório, procure somente caminhos explicitamente configurados/documentados; não varra diretórios pessoais nem copie arquivos grandes para o repositório.
2. Gere primeiro um relatório de descoberta de dados e um dicionário de dados com origem da afirmação (documentação, observação empírica ou hipótese), evidências e pendências. Não presuma nomes, tipos, semânticas, chaves, limites de classe ou correspondência entre tabelas a partir desta especificação ou de memória externa.
3. Não crie colunas inexistentes nem atribua significado a `sensor_*`, `feature_*`, códigos, sentinelas ou valores ausentes. Mantenha nomes originais no bronze. Registre mapeamentos aprovados em configuração/versionamento e no dicionário.
4. Confirme por evidência qual é o tempo de evento/observação, como identificar evento e censura, e se há reparos recorrentes. Se o TTE for somente um resumo por veículo, **não** o replique ingenuamente em cada leitura como se fosse evento individual; estabeleça o desenho de risco e o instante de predição em conjunto com a documentação.
5. Antes de assumir que as classes do IDA podem ser derivadas de RUL, transcreva as regras oficiais e valide limites, inclusão das fronteiras, ordem, unidade e significado dos rótulos. A informação preliminar menciona intervalos 0–6, 6–12, 12–24, 24–48 e acima de 48, mas isso não é uma definição normativa sem confirmação nos arquivos oficiais.
6. Não invente credenciais, bucket, catálogo, schema, workspace, região, URIs ou configuração de nuvem. Use parâmetros externos e placeholders documentados. Nunca inclua segredos em código, logs, notebooks ou commits.
7. Se uma pendência bloquear alvo válido, split ou avaliação, pare a implementação dependente, descreva evidência e opções no relatório e peça decisão ao usuário. Continue apenas as etapas independentes.
8. Não alegue que a PoC foi executada em AWS/Databricks se não tiver sido executada. Diferencie instruções, execução local, execução cloud e resultados medidos.

## 4. Metodologia CRISP-DM

1. **Business Understanding:** definir pergunta, usuário da previsão, horizonte de ação e hipóteses de valor. Sem acesso a stakeholders da Michelin, registrar benefícios (priorização de inspeções, disponibilidade, custo) como hipóteses, não fatos.
2. **Data Understanding:** inventariar arquivos, documentação, semântica, qualidade, população, eventos, censura e limitações.
3. **Data Preparation:** ingestão imutável, validação, junções justificadas, snapshots históricos e features sem informação futura.
4. **Modeling:** baseline e abordagens de sobrevivência, RUL e classificação ordinal, com protocolo comum por veículo.
5. **Evaluation:** avaliar discriminação, calibração/erro e utilidade segundo alvos válidos; comparar com baseline e documentar limitações.
6. **Deployment:** para esta PoC, entregar pipeline reproduzível, artefatos e instruções de execução/monitoramento; não publicar serviço produtivo sem escopo e autorização próprios.

## 5. Escopo

### Incluído

- Descoberta e validação dos CSVs e da documentação do desafio.
- Ingestão de arquivos de origem em S3 (camada raw, imutável) e leitura/processamento em Databricks com PySpark.
- Camadas Delta Bronze, Silver e Gold com contratos e validações explícitos.
- Construção de exemplos de predição em um ou mais instantes por veículo, somente após validar a estrutura temporal e o desenho de risco.
- Análise exploratória de eventos, censura, cobertura, desbalanceamento, qualidade e possível recorrência de reparos.
- Modelos mínimos comparáveis: baseline não treinado; pelo menos um modelo de sobrevivência; regressão RUL como benchmark sob amostra/estratégia cuja censura esteja declarada; classificador ordinal para rótulos deriváveis/oficiais.
- Tracking de parâmetros, métricas, versões de dados/código e artefatos no MLflow disponível no ambiente.
- Relatórios, documentação, testes de dados e instruções para execução cloud.

### Fora do escopo

- Alegações de manutenção geral do veículo ou causalidade entre sensores e reparo.
- Produção, alertas em tempo real, integração com sistemas de frota ou intervenção automática.
- Converter tempo de estudo para calendário ou quilometragem sem evidência.
- Construir uma infraestrutura AWS/Databricks completa, pagar recursos ou criar credenciais.
- Tratar predição de “falha” como sinônimo de reparo sem validação da documentação.

## 6. Requisitos funcionais

**RF-01 Descoberta:** identificar arquivos, tamanho, encoding/delimitador, schema observado, contagens, chaves candidatas, intervalos temporais, nulos, sentinelas, duplicatas e consistência entre arquivos. Salvar relatório reproduzível sem publicar dados sensíveis.

**RF-02 Contrato de dados:** manter dicionário com nome original, tipo observado, significado documentado, regra de parsing, nulabilidade, domínio observado, proveniência e confiança. Distinguir “documentado” de “inferido”.

**RF-03 Ingestão:** ler dados diretamente do caminho S3 configurado pelo usuário/ambiente, sem etapa local intermediária no fluxo pretendido. Persistir cópia Bronze em Delta com metadados de ingestão e rastreabilidade da origem. Ingestão deve ser reexecutável sem duplicar registros indevidamente.

**RF-04 Qualidade:** validar schema, integridade de chaves, unicidade esperada, domínios, tempos, junções, contagens e proporção de nulos/sentinelas. Falhas críticas devem interromper a etapa dependente com mensagem acionável; não descartar linhas silenciosamente.

**RF-05 Preparação temporal:** produzir tabela Gold de exemplos de predição com identificador de veículo, instante de corte, features permitidas, tempo observado até evento/fim, indicador de evento/censura e campos de proveniência — apenas se a semântica for confirmada. O corte não pode exceder o tempo disponível na previsão. Excluir variáveis que revelem o evento futuro, duração total observada ou rótulo.

**RF-06 Sobrevivência:** treinar e avaliar um baseline e pelo menos um método de sobrevivência compatível com o ambiente. O modelo deve produzir função de sobrevivência ou risco ao longo de tempos válidos e, se tecnicamente suportado, mediana/quantis de tempo até evento. Reportar quando tais quantis não são identificáveis dentro do horizonte observado.

**RF-07 Benchmark RUL:** implementar regressão contínua como comparação, nunca transformando censurados em eventos no fim do acompanhamento. Registrar população usada, censura e possível viés de seleção. Uma análise de casos completos pode ser benchmark, mas não deve ser descrita como corrigida para censura.

**RF-08 Classificação ordinal:** implementar comparação ordinal alinhada às regras oficiais do IDA, se puderem ser confirmadas. Preservar ordem dos níveis e relatar macro-F1/balanced accuracy e métricas por classe; comparar com a função de custo oficial somente se sua fórmula estiver documentada e implementada literalmente.

**RF-09 Avaliação:** usar split determinístico por veículo, sem veículo compartilhado entre treino/validação/teste. Se houver avaliação temporal, estabelecer cortes temporais sem treinar com informações posteriores ao corte. Ajuste de hiperparâmetros e transformações aprendidas apenas no treino. Publicar as métricas no MLflow e em relatório.

**RF-10 Reprodutibilidade:** parametrizar caminhos, seed, split, colunas aprovadas, horizonte e configurações. Registrar versões de dependências, commit/revisão, fingerprint/versionamento dos dados e parâmetros do experimento.

**RF-11 Entrega:** fornecer documentação de arquitetura, decisões, limitações, execução, resultados e troubleshooting; notebooks devem chamar código reutilizável em `src/` e não conter lógica crítica duplicada.

## 7. Requisitos não funcionais

- **Reprodutibilidade:** mesma versão de dados, código e parâmetros deve produzir o mesmo split e resultados determinísticos quando suportado pelo algoritmo.
- **Escalabilidade pragmática:** transformações tabulares distribuídas em PySpark/Databricks; evitar coletar dados operacionais completos para o driver ou para ambiente local.
- **Rastreabilidade:** manter linhagem entre origem, Delta, exemplos, modelo e métricas.
- **Segurança:** credenciais por mecanismos nativos/secret scopes ou identidade gerenciada; princípio do menor privilégio; nenhum segredo persistido.
- **Privacidade e minimização:** não replicar datasets grandes nem incluir registros brutos em relatórios, logs, testes versionados ou exemplos.
- **Manutenibilidade:** módulos pequenos, configuração validada, logging útil, tipagem quando prática e erros explícitos.
- **Custo:** execução por parâmetros e amostras apenas para exploração; documentar clusters e custo como itens a configurar, sem assumir tamanho ou preço.
- **Portabilidade:** lógica de negócio separada de paths/ambiente Databricks sempre que viável; diferenças locais/cloud documentadas.

## 8. Arquitetura lógica

```text
CSV/documentação do desafio
          │ upload/armazenamento controlado pelo usuário
          ▼
S3 raw (originais imutáveis, URI configurada)
          │ leitura direta por Databricks/PySpark
          ▼
Delta Bronze → Delta Silver → Delta Gold (snapshots de predição)
                                      │
                     split por veículo / corte temporal
                                      │
            baseline → sobrevivência → RUL → classificação ordinal
                                      │
                              MLflow tracking
                                      │
                relatório, artefatos e instruções de uso
```

Bronze conserva o conteúdo e metadados de ingestão; Silver contém dados parseados/normalizados sem apagar origem ou mascarar decisões; Gold contém exemplos de modelagem e features aprovadas, com regras e versão documentadas. A organização física, catálogo, nomes e particionamento Delta devem ser escolhidos após inspeção do volume e do workspace. Não particionar automaticamente por identificador de alta cardinalidade.

### Componentes sugeridos

- **S3:** armazenamento raw; acesso direto pelo Databricks conforme suporte e permissões do workspace.
- **Databricks + PySpark:** ingestão, validação, preparação e execução escalável.
- **Delta Lake:** persistência transacional das camadas e dados derivados.
- **MLflow:** experiment tracking, parâmetros, métricas, artefatos e modelo; Model Registry é opcional.
- **Python:** módulos reutilizáveis para contratos, validações, criação do split, avaliação e configuração.

## 9. Protocolo de alvo, censura e vazamento

1. Determinar documentalmente a relação entre o identificador e as três tabelas, a unidade de `time_step` e o significado exato de cada campo de TTE.
2. Representar, quando confirmado, tempo de duração observado `T` e indicador `E` (evento observado = 1; censura à direita = 0). Se nomes e codificação oficiais diferirem, documentar mapeamento em vez de forçar esses nomes.
3. Para snapshots de predição no instante `t`, o tempo residual até evento só é conhecido para eventos que ocorreram após `t`. Veículos que não tiveram evento até o encerramento são censurados em `T - t`. Dados após `t` nunca podem alimentar features daquele snapshot.
4. Verificar se existe reparo recorrente/novo episódio após reparo. Se existir e o material não definir o alvo, não fingir que o estudo é de eventos recorrentes; propor alvo alternativo explicitamente e registrar a decisão pendente.
5. Não tratar o término do estudo como instante de reparo. Não calcular RUL de censurados como `fim_do_estudo - t` rotulado como evento.
6. Eventos observados apenas antes do fim do período podem gerar amostra de regressão restrita aos eventos conhecidos, mas essa avaliação é seletiva e sujeita a viés. Rotular isso claramente; não comparar de forma ingênua com métricas de sobrevivência em população diferente.
7. Excluir TTE, status de reparo, variáveis posteriores ao corte, derivados do rótulo e qualquer proxy que carregue informação futura das features. Avaliar candidatos a leakage por definição, disponibilidade temporal e testes de perturbação/ablação.
8. O split primário é por veículo. Construir as linhas temporais de cada veículo depois de fixar sua partição, ou garantir que todos os snapshots do mesmo veículo pertençam à mesma partição. Seed e proporções são configuráveis e registradas.

## 10. Modelos e métricas

### Baselines

- Baseline de sobrevivência não treinado: Kaplan–Meier para sobrevivência marginal e/ou estimativa de risco de referência, conforme a população e horizonte permitam.
- Baseline de classificação: classe majoritária e/ou regra simples autorizada pela definição oficial.
- Para RUL, reportar uma referência simples em eventos observados; declarar população e limitação.

### Sobrevivência — principal

Selecionar algoritmo apenas após verificar compatibilidade com Spark, tamanho, licenças e ambiente. Uma opção distribuída e uma biblioteca não distribuída podem ser avaliadas se o volume permitir, mas não pressupor que Random Survival Forest, Cox ou boosting estejam instalados. Comparar com baseline e registrar limitações (incluindo riscos proporcionais, se Cox for escolhido).

Métricas: concordance index (especificar variante e tratamento de censura), Integrated Brier Score ou Brier em tempos definidos, calibração de sobrevivência por horizonte e curvas de Kaplan–Meier estratificadas por grupos de risco. Selecionar horizonte somente dentro da faixa com suporte suficiente e justificar. Reportar intervalos de confiança/variabilidade por bootstrap agrupado por veículo quando praticável. Não tratar C-index isolado como prova de boa calibração.

### Regressão RUL — benchmark

Métricas: MAE, mediana do erro absoluto e RMSE nos eventos observados elegíveis, sempre identificadas como métricas condicionais aos eventos observados. Se houver método de regressão que trate censura disponível e validado, ele pode ser adicionado, com pressupostos documentados. Comparabilidade com sobrevivência exige mesmo split e transparência sobre conjuntos avaliados.

### Classificação ordinal — benchmark do desafio

Métricas: matriz de confusão, balanced accuracy, macro-F1, recall por classe e métrica ordinal (por exemplo, erro absoluto médio entre índices de classe), além da função de custo do desafio apenas após sua confirmação. Usar os rótulos oficiais de validação apenas para a avaliação prevista pelas regras; não usá-los para treinar/tunar se isso violar as regras do desafio. Registrar claramente a separação entre validação interna e avaliação oficial.

### Seleção e comunicação

Não escolher modelo por uma métrica sem considerar censura, cobertura do horizonte, calibração e utilidade. Relatório deve apresentar desempenho do baseline, incerteza e limitações. Interpretabilidade (importância/SHAP) é opcional; não interpretar associação como causalidade.

## 11. Estrutura de pastas proposta

```text
.
├── CLAUDE.md                 # instruções de trabalho e regras do repositório
├── SPEC.md                   # esta especificação
├── README.md
├── pyproject.toml            # dependências e ferramentas, após definir ambiente
├── .gitignore
├── configs/
│   ├── example.yaml          # somente placeholders, sem credenciais
│   └── data_contract.yaml    # mapeamentos validados, não presumidos
├── docs/
│   ├── data-discovery.md
│   ├── data-dictionary.md
│   ├── architecture.md
│   ├── modeling-and-evaluation.md
│   └── decisions/            # ADRs para decisões relevantes
├── notebooks/
│   ├── 01_business_and_data_understanding.py
│   ├── 02_data_preparation.py
│   ├── 03_modeling.py
│   └── 04_evaluation.py
├── src/scania_poc/
│   ├── config.py
│   ├── discovery.py
│   ├── contracts.py
│   ├── ingestion.py
│   ├── quality.py
│   ├── features.py
│   ├── splitting.py
│   ├── survival.py
│   ├── rul.py
│   ├── ordinal.py
│   ├── evaluation.py
│   └── tracking.py
├── tests/
│   ├── unit/
│   ├── data_contracts/
│   └── integration/
└── scripts/
    ├── run_discovery.py
    └── run_pipeline.py
```

Os nomes são sugestão inicial; adaptar à convenção do repositório existente depois de inspecioná-lo. Dados originais, credenciais, outputs volumosos e caches devem estar excluídos do Git.

## 12. Etapas de implementação

### Fase 0 — reconhecer o repositório

Ler `CLAUDE.md`, instruções existentes, dependências, convenções e estado do Git. Preservar alterações existentes. Não substituir arquivos de projeto sem entender o uso atual.

### Fase 1 — descoberta (bloqueia decisões de alvo)

Catalogar arquivos e documentação; inspecionar schemas e amostras; perfil de qualidade; chaves e cardinalidades; cronologia; associação entre arquivos; semântica de TTE, censura e rótulos. Produzir `docs/data-discovery.md` e `docs/data-dictionary.md`, com perguntas abertas. **Não treinar ainda.**

### Fase 2 — desenho e contrato

Propor tabela de análise, unidade observacional e instante de predição; desenhar split por veículo e regras anti-leakage. Registrar decisões e esquema esperado. Se faltarem evidências, sinalizar bloqueio sem inventar semântica.

### Fase 3 — pipeline de dados

Implementar configuração sem segredos, leitor S3/Databricks, Delta Bronze/Silver/Gold, validações e reexecução idempotente. Começar por amostra controlada para validar lógica; executar escala completa apenas no ambiente configurado.

### Fase 4 — snapshots e split

Construir snapshots/cortes temporais aprovados, features históricas disponíveis no corte e alvos com evento/censura. Separar veículos antes de ajuste de qualquer estatística/transformação. Registrar cobertura e descartes com motivos.

### Fase 5 — modelos

Implementar baselines; modelo de sobrevivência; benchmark de RUL com limitação explícita; benchmark ordinal se regras confirmadas. Rastreamento no MLflow incluindo dados, código, split e horizonte.

### Fase 6 — avaliação e comunicação

Calcular métricas por abordagem, checks de calibração/erro, análise de segmentos e incerteza. Produzir relatório com resultados medidos, decisões, riscos e próximos passos. Não extrapolar para operação real.

### Fase 7 — documentação e entrega

Completar README com setup, configuração, comandos, recursos cloud necessários, execução, artefatos esperados, limpeza/custos de recursos e limitações. Confirmar que uma pessoa consegue reproduzir a descoberta e o experimento com configuração própria.

## 13. Testes e verificações

Escrever testes unitários para parsing, regras confirmadas de censura, cálculo de tempo residual, criação de features até o corte, codificação ordinal oficial, métricas e divisão por grupo. Incluir fixtures sintéticas pequenas com casos: evento antes/depois do corte, censura, empate/fronteira temporal, nulos, duplicatas e veículo com várias linhas. Fixtures devem testar comportamento sem pretender representar o dataset real.

Testes de integração com dados pequenos devem verificar leitura → Bronze → Silver → Gold, idempotência, contagens/linhagem, falhas de contrato e tracking simulado/local quando possível. Testes cloud devem ser marcados separadamente e só rodam com ambiente configurado.

Verificações obrigatórias antes de aceitar resultados:

- nenhum veículo aparece em mais de uma partição;
- nenhuma feature usa informação após instante de corte;
- nenhum censurado foi convertido em evento para regressão;
- todo alvo/split/métrica usa semântica documentada;
- transformações aprendidas são ajustadas apenas no treino;
- joins não multiplicam linhas sem justificativa;
- avaliação cobre casos observados e censurados conforme a métrica;
- execução reproduz parâmetros, versões e dados de origem;
- segredos e dados brutos não aparecem em Git/logs/relatórios.

## 14. Critérios de aceite

1. A documentação oficial e os CSVs disponíveis foram inspecionados; `data-discovery.md` e dicionário distinguem fatos, inferências e hipóteses, com perguntas abertas.
2. O significado de evento, censura, unidade temporal, chaves e rótulos foi confirmado ou o projeto declara precisamente quais etapas estão bloqueadas.
3. O pipeline proposto lê do S3 por Databricks/PySpark e escreve Bronze/Silver/Gold Delta, sem mover dados pesados para o computador local; execução cloud é reportada como realizada somente se ocorreu.
4. Construção de alvo trata censura à direita corretamente e não chama reparo observado de falha sem evidência.
5. Split determinístico por veículo é comprovado por teste; não há leakage entre tempo de corte e features.
6. Há resultados comparáveis de baseline e modelo de sobrevivência; benchmarks RUL e ordinal são incluídos apenas com limitações/regras descritas.
7. Métricas, parâmetros, versões e artefatos estão rastreados no MLflow ou a limitação de integração está documentada com alternativa reproduzível.
8. Testes automatizados cobrem contratos e casos temporais sintéticos essenciais e passam no ambiente correspondente.
9. README explica como configurar e executar sem credenciais embutidas e sem exigir dados locais como intermediário do pipeline final.
10. Relatório final limita conclusões ao Component X e às unidades observadas no dataset, descrevendo validade externa, censura, desbalanceamento e possíveis distorções temporais.

## 15. Documentação a entregar

- `README.md`: objetivo, setup, configuração, comandos, execução local limitada/cloud, custos/recursos a configurar, artefatos e troubleshooting.
- `docs/data-discovery.md`: inventário e evidências da inspeção, qualidade, limitações e questões em aberto.
- `docs/data-dictionary.md`: schema, semântica e proveniência de cada campo utilizado.
- `docs/architecture.md`: fluxo, camadas, permissões requeridas e decisões de implantação.
- `docs/modeling-and-evaluation.md`: alvo, censura, split, leakage, modelos, métricas, critérios de seleção e limitações.
- `docs/decisions/`: decisões relevantes e alternativas descartadas, com motivação.
- Relatório de resultados com data, versão de dados/código, protocolo, métricas e ressalvas.

## 16. Orientação para a primeira resposta do Claude Code

Antes de editar código de modelagem, Claude deve apresentar um resumo do repositório e dos arquivos efetivamente encontrados, os schemas e chaves observados, evidências da documentação sobre alvo/censura/classes, riscos de leakage e perguntas não resolvidas. Em seguida, deve propor o contrato de dados e o desenho dos snapshots/split. Só depois de resolver as pendências que bloqueiam o alvo deve implementar o pipeline e modelos, mantendo esta especificação e as hipóteses atualizadas.
