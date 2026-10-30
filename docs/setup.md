# Setup local e execução na Databricks Free Edition

O uso previsto é pessoal e não comercial. Localmente, o projeto executa testes sintéticos, lint e validação estrutural. O processamento dos CSVs ocorre na Databricks Free Edition usando compute serverless e armazenamento gerenciado pelo Unity Catalog; não é necessário criar conta AWS, bucket S3 ou cluster próprio.

## Pré-requisitos

- Conta Databricks Free Edition e um workspace com Unity Catalog/compute serverless.
- Repositório importado como **Git Folder**.
- Os oito CSVs oficiais disponíveis localmente para upload. O conjunto observado totaliza cerca de 1,5 GB e cada arquivo é menor que o limite documentado de 5 GB por arquivo da [interface de upload de volumes](https://docs.databricks.com/aws/en/volumes/volume-files).
- Ambiente serverless configurado com as dependências Python listadas em `pyproject.toml` (incluindo `lifelines`, `scikit-learn` e `PyYAML`). Use a versão serverless 4 ou mais recente, que inclui Spark ML. Não instale PySpark: ele já é fornecido pelo runtime.

## Verificações locais — PowerShell

Na raiz do repositório:

```powershell
uv sync --dev
uv run pytest tests/unit/ -v
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run python scripts/validate_structure.py
```

Os testes locais usam fixtures pequenas e não carregam os CSVs reais. Eles não validam Spark, Delta, quotas ou o acesso ao volume do workspace.

## Preparar volume e tabelas

1. No workspace, abra **Catalog**. Pense na hierarquia como: **catálogo → schema → tabelas/volumes**. Se sua conta mostrar `main` e `default`, você pode usar esses nomes; caso contrário, escolha os que aparecem no seu Catalog Explorer.
2. Dentro do schema escolhido, crie um **managed volume** pelo botão **Create > Volume**, com o nome `component_x`. Um volume é a pasta de arquivos Raw que o Spark vai ler; o schema também receberá as tabelas Delta produzidas pelo pipeline.
3. Abra o volume, crie uma pasta `raw` e envie os oito CSVs oficiais abaixo para ela. A interface aceita até 5 GB por arquivo; os arquivos Delta derivados ocuparão espaço adicional. Depois da ingestão, trate `raw/` como somente leitura.

   - `train_tte.csv`
   - `train_operational_readouts.csv`
   - `train_specifications.csv`
   - `validation_labels.csv`
   - `validation_operational_readouts.csv`
   - `validation_specifications.csv`
   - `test_operational_readouts.csv`
   - `test_specifications.csv`

   Não carregue `test_labels.csv`: esse arquivo não faz parte do pacote oficial.

4. Entenda e anote os dois valores que os notebooks vão pedir:

   - `RAW_VOLUME_PATH` é o caminho até a pasta `raw` dentro do volume. Exemplo: `/Volumes/main/default/component_x/raw`.
   - `DATA_SCHEMA` é só `<catalog>.<schema>`, sem o volume e sem `/raw`. Exemplo: `main.default`.

   Nesse exemplo, uma tabela Bronze será chamada `main.default.bronze_train_tte`. O caminho do volume é para ler os CSVs; `DATA_SCHEMA` diz onde criar as tabelas Delta.

   O Unity Catalog controla permissões separadas: para ler os CSVs, o usuário precisa de `USE CATALOG`, `USE SCHEMA` e `READ VOLUME` no volume. Para criar as tabelas, precisa de `CREATE TABLE` no schema. Para sobrescrever tabelas já existentes, precisa de `MODIFY` nelas; normalmente o usuário que criou as tabelas é seu proprietário e já pode modificá-las. Se a conta bloquear alguma ação, peça ao proprietário do catálogo/schema para conceder o privilégio correspondente. [Referência de privilégios UC](https://docs.databricks.com/aws/en/data-governance/unity-catalog/access-control/privileges-reference).
5. Adicione o repositório ao workspace como **Git Folder**: na barra lateral abra **Workspace**, selecione sua pasta pessoal e escolha **Create > Git folder**. Informe a URL do repositório e autentique-se no provedor Git se solicitado. Depois, os notebooks e a pasta `src/` do projeto ficam acessíveis nessa pasta. [Como criar Git Folders](https://docs.databricks.com/aws/en/repos/git-operations-with-repos).

   Abra um notebook do projeto nessa Git Folder e selecione compute **Serverless**. Abra o painel lateral **Environment**, escolha o ambiente-base e adicione as dependências Python que faltarem, conforme `pyproject.toml`; depois clique **Apply**. Isso instala as bibliotecas e reinicia a sessão Python. Faça a configuração nos notebooks que precisam dessas bibliotecas, a menos que seu workspace ofereça um ambiente serverless compartilhado. **Não instale PySpark**: ele já vem no compute.

   A raiz da Git Folder contém `src/`, então os imports do projeto, como `from src.scania_poc...`, vêm dali. Se adicionar uma biblioteca ou arquivo do workspace como dependência, use o caminho absoluto começando com `/Workspace/`; para os dados use o caminho `/Volumes/...`. [Dependências do compute serverless](https://docs.databricks.com/aws/en/compute/serverless/dependencies).

## Ordem de execução

Execute manualmente e de forma sequencial em compute serverless:

1. `notebooks/03_data_preparation/01_ingest_raw.py`: informe `RAW_VOLUME_PATH` e `DATA_SCHEMA`. Para o smoke test inicial, informe um nome oficial em `SOURCE_FILE` (por exemplo `train_tte.csv`); deixe-o vazio para ingerir os oito CSVs. Antes de escrever, o notebook verifica a presença de todos os arquivos selecionados e cria as tabelas `bronze_<arquivo>`.
2. Rode `notebooks/02_data_understanding/01_data_exploration.py` e `02_data_quality.py`, informando `DATA_SCHEMA`, para perfilar e validar Bronze.
3. `notebooks/03_data_preparation/02_silver_transform.py`: informe `DATA_SCHEMA`; cria tabelas `silver_<artefato>` após contratos e joins.
4. `notebooks/03_data_preparation/03_gold_features.py`: informe `DATA_SCHEMA` e `SEED`; cria tabelas `gold_<partição>`.
5. `notebooks/04_modeling/01_baseline_model.py`: informe `DATA_SCHEMA`, `SEED` e `GIT_REVISION`. Registre os IDs MLflow impressos para CoxPH, RUL e ordinal.
6. `notebooks/05_evaluation/01_model_evaluation.py`: informe `DATA_SCHEMA` e os três run IDs para avaliar o teste interno reservado e, uma vez, os rótulos oficiais da validação.

Discovery e quality checks leem tabelas Bronze; portanto, rode-os após a ingestão. O fluxo não usa rótulos oficiais do teste. Os notebooks escrevem Delta como tabelas Unity Catalog gerenciadas, sem particionar por `vehicle_id`.

## Linhagem e reexecução

Bronze registra caminho absoluto do CSV no volume, SHA-256 do conteúdo, tamanho em bytes e horário de ingestão. Cada tabela Bronze é sobrescrita de forma idempotente em uma nova execução; os CSVs Raw permanecem intactos. Silver e Gold também substituem suas tabelas gerenciadas correspondentes.

## Limites e diagnóstico

- Free Edition oferece compute serverless limitado por quotas de uso. Ao ultrapassar a quota, o compute pode ficar indisponível até a renovação ([limitações oficiais](https://docs.databricks.com/aws/en/getting-started/free-edition-limitations)); execute um notebook por vez e confira os outputs após cada camada.
- Os 1,5 GB são apenas os arquivos Raw. Bronze e Silver materializam dados e ocupam armazenamento adicional; não há garantia de que uma execução completa caiba na quota de compute/armazenamento da conta.
- Se a quota interromper a execução, os CSVs Raw e tabelas já gravadas permanecem; reexecute o notebook da etapa incompleta. A ingestão sobrescreve cada tabela Bronze, sem anexar duplicatas.
- O processamento completo de 1,5 GB só será considerado validado após uma execução real na conta. Consulte [docs/experiment-results.md](experiment-results.md) para o estado registrado.
- Testes automatizados locais: `uv run pytest tests/unit/ -v`. Nenhum resultado local deve ser descrito como execução Databricks.
