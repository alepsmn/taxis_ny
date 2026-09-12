import duckdb
from duckdb import DuckDBPyRelation

from pathlib import Path
from taxis.contract import CONTRACT_V1


def col_transformations(raw_file_path: Path, file_schema: dict[str, str], sha: str, year: int, month: int) -> DuckDBPyRelation:
    clauses = []
    for col in CONTRACT_V1:
        if col.source.lower() in file_schema:
            clauses.append(f'CAST("{col.source}" AS {col.type}) AS {col.canonical}')
        else:
            clauses.append(f"NULL::{col.type} AS {col.canonical}")

    select_clause = ', '.join(clauses)
    transformed_cols = duckdb.sql(
        f"""
        SELECT *,
            datediff('minute', pickup_at, dropoff_at) AS duration_min,
            '{sha}' AS source_sha256,
            {year} AS source_year,
            {month} AS source_month,
            1 AS contract_version,
            CURRENT_TIMESTAMP AS ingested_at
            --lineage
        FROM (
            SELECT {select_clause}
            FROM read_parquet('{raw_file_path}')
        )
    """
    )
    return transformed_cols
