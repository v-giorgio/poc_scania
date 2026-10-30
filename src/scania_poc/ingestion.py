"""Funções de ingestão de dados brutos para o S3 Raw.

A camada Raw preserva os arquivos originais sem nenhuma modificação.
Todas as transformações ocorrem na camada Silver (ver silver_transform.py).
"""

from typing import Any


def build_s3_raw_path(bucket: str, prefix: str, filename: str) -> str:
    """Constrói o path S3 completo para um arquivo na camada Raw."""
    return f"s3://{bucket}/{prefix.strip('/')}/{filename}"


def ingest_csv_to_raw(
    spark: Any,
    local_or_s3_source: str,
    s3_dest_path: str,
    *,
    header: bool = True,
    delimiter: str = ",",
) -> int:
    """Copia um CSV para a camada Raw do S3 preservando o conteúdo original.

    Retorna o número de linhas lidas (sem contar o header).
    Não aplica transformações — infere schema apenas para contagem.
    """
    df = spark.read.csv(
        local_or_s3_source,
        header=header,
        sep=delimiter,
        inferSchema=False,
    )
    row_count = df.count()
    df.write.mode("overwrite").option("header", True).csv(s3_dest_path)
    return row_count


def verify_raw_file_exists(spark: Any, s3_path: str) -> bool:
    """Verifica se um arquivo/diretório existe no S3."""
    try:
        df = spark.read.csv(s3_path, header=True)
        return df.count() > 0
    except Exception:
        return False
