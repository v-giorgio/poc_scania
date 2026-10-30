# Setup local e execução

Este guia cobre o ambiente Python local e descreve o que é necessário para usar os notebooks no Databricks. No estado atual do repositório, **não há um comando local que execute o pipeline completo**: ingestão, transformações Delta e notebooks dependem de Spark/Databricks e de recursos cloud configurados.

## Pré-requisitos

- Windows, macOS ou Linux.
- Python 3.11 ou superior.
- Git.
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) para criar o ambiente e instalar as dependências travadas em `uv.lock`.

AWS e Databricks não são necessários para instalar o ambiente Python ou rodar os testes unitários. São necessários para executar o fluxo cloud.

## Instalação local (PowerShell)

Abra o PowerShell na pasta do repositório:

```powershell
uv sync --dev
uv run python --version
```

`uv sync --dev` instala as dependências de `pyproject.toml` e cria/atualiza `.venv` usando `uv.lock`. Se `uv` não estiver instalado, siga o guia de instalação oficial acima e reabra o terminal.

## Verificações locais

```powershell
uv run pytest tests/unit/ -v
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

Para formatar arquivos depois de uma edição, remova `--check` de `ruff format`. O script `scripts/validate_structure.sh` ainda valida caminhos de uma estrutura antiga (`src/data/` e outros); não o use como verificação de validade desta versão do projeto.

Os módulos de discovery e qualidade que recebem DataFrames Spark e os notebooks Databricks não são executados por esses comandos locais. `pyspark` não está declarado como dependência do projeto.

## Dados locais

Os CSVs e PDFs não são instalados por `uv` nem devem ser commitados. Se você já recebeu os arquivos, mantenha os CSVs em `dataset_local/` e a documentação oficial em `papers/`, conforme as exclusões do `.gitignore`. Um clone novo pode não conter essas pastas; obtenha os arquivos pela página oficial do [dataset SCANIA Component X](https://researchdata.se/en/catalogue/dataset/2024-34) e pelo [chamado IDA 2024](https://ida2024.blogs.dsv.su.se/industrial-challenge/), respeitando os termos de uso.

O script `scripts/download_dataset.sh` não baixa o dataset Component X: ele descreve o antigo conjunto APS Failure e usa nomes de arquivos diferentes. Não o use para preparar os dados desta PoC. Também não presuma que `test_labels.csv` pertence ao pacote oficial; confira a lista de arquivos e a documentação de origem antes de usá-lo.

## Execução no Databricks/AWS

O fluxo cloud é uma execução separada do ambiente local. Para executá-lo, configure por conta própria:

- Um workspace Databricks com cluster Spark/Delta e permissões de leitura e escrita no S3.
- Um bucket S3 e os caminhos de origem dos CSVs, usando a identidade/perfil AWS ou o mecanismo de credenciais aprovado no workspace.
- Os notebooks deste repositório e o pacote `src/` disponíveis no workspace. Os notebooks importam `src.scania_poc`; essa distribuição ainda precisa ser feita/configurada no Databricks.

Não há bucket, workspace, região ou credenciais padrão. Não coloque tokens, chaves ou segredos em arquivos rastreados pelo Git. O arquivo `config/dev.env.example` é apenas um exemplo de nomes de variáveis: a aplicação não carrega `.env` automaticamente e o valor de bucket nele é ilustrativo. Para uma sessão PowerShell, uma variável pode ser definida temporariamente assim:

```powershell
$env:S3_BUCKET = "<bucket-configurado-por-voce>"
```

Os notebooks usam widgets Databricks para `S3_BUCKET` e `SOURCE_PATH`; revise cada notebook e seus pré-requisitos antes de executar. Faça primeiro uma execução pequena e controlada no ambiente autorizado. A execução cloud não foi comprovada por este setup.

## Limitações atuais

- `pyproject.toml` não inclui PySpark nem define um comando CLI para executar discovery ou o pipeline localmente.
- Os notebooks são protótipos para Databricks e algumas etapas ainda não atendem à metodologia de `SPEC.md`; em particular, o Gold usa a última leitura de treino sem validar se ela ocorre antes do evento e as etapas de modelagem não implementam ainda um protocolo completo de treino/avaliação.
- O contrato de dados, relatórios de discovery e dicionário contêm hipóteses/contagens que precisam ser reconciliadas com os CSVs e a documentação oficial antes de interpretar métricas.

Consulte [SPEC.md](../SPEC.md), [data discovery](data-discovery.md) e [arquitetura](architecture.md) antes de interpretar os resultados ou iniciar uma execução cloud.
