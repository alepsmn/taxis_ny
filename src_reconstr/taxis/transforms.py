import duckdb

from duckdb import DuckDBPyRelation
from pathlib import Path
from taxis.contract import CONTRACT_V1

def col_transformations(raw_file_path: Path, schema_col_dtype: dict[str, str], file_sha: str, year: int, month: int) -> DuckDBPyRelation:
    clauses = []
    for col in CONTRACT_V1:
        if col.source.lower() in schema_col_dtype:
            clauses.append(f"CAST('{col.source}' AS {col.type}) AS {col.canonical}")
        else:
            clauses.append(f"NULL::{col.type} AS {col.canonical}")

    select_clauses = ', '.join(clauses)
    transormed_cols = duckdb.sql(
        f"""
        SELECT
            datediff('minute', pickup_at, dropoff_at) AS duration_min,
            '{file_sha}' AS source_sha256,
            {year} AS source_year,
            {month} AS source_month,
            1 AS contract_version,
            CURRENT_TIMESTAMP AS ingested_at
        FROM (
            SELECT {select_clauses}
            FROM read_parquet('{raw_file_path}')
        )
    """
    )

    return transormed_cols