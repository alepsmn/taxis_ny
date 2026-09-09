import duckdb
from duckdb import DuckDBPyRelation

from pathlib import Path
from taxis.contract import CONTRACT_V1


# recibe la ruta formada por acquire
def transform(parquet_raw_path: Path, sha: str, year: int, month: int, schema: dict[str, str]) -> duckdb.DuckDBPyRelation:
    columns = []
    # T-01, T-02 - renombrar y cast
    for col in CONTRACT_V1:
        if col.source.lower() in schema:
            # las columnas en ambos, se anaden a las columnas FINALES en este resultado
            columns.append(f'CAST("{col.source}" AS {col.type}) AS {col.canonical}')
        else:
            # T-03 - cols opcionales que no existan, como NULL
            columns.append(f'NULL::{col.type} AS {col.canonical}')

    select_clause = ', '.join(columns)
    # T-04 - duration_min derivada
    # datediff usa alias canonicos antes de que se hayan renombrado -> SUBCONSULTA RENOMBRANDO 1o
    #select_clause += ", datediff('minute', pickup_at, dropoff_at) AS duration_min"

    # T-05 - linaje 
    # select_clause += f", '{sha}' AS source_sha256"
    # select_clause += f", {year} AS source_year"
    # select_clause += f", {month} AS source_month"
    # select_clause += ", 1 AS contract_version"
    # select_clause += ", CURRENT_TIMESTAMP AS ingested_at"

    result = duckdb.sql( # Si .execute devuelve objeto DuckDBPyConnection no Relation
        f"""
        SELECT *,
            -- T-04
            date_diff('minute', pickup_at, dropoff_at) AS duration_min, -- fallo mio
            -- T-05
            '{sha}' AS source_sha256,
            {year} AS source_year,
            {month} AS source_month,
            1 AS contract_version,
            CURRENT_TIMESTAMP AS ingested_at -- fallo mio
        FROM ( -- T-01, T-02, T-03
            SELECT {select_clause} 
            FROM read_parquet('{parquet_raw_path}') -- fallo mio
        )
        """
        )

    return result

