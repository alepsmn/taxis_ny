import duckdb
from pathlib import Path
from taxis.contract import CONTRACT_V1, COMPATIBLE_TYPES

def comparing_schemas(parquet_path: Path) -> tuple[dict[str, str|int], int, dict[str, str]]:

    meta_cols = {
        "block": [],
        "warn": []
    }
    # S-04 # -------------------------------------------------------------------------
    count = duckdb.execute(
        """SELECT COUNT(*) FROM read_parquet(?)""",
        [str(parquet_path)]
    ).fetchone()[0] #  fila como TUPLA - Ej: (29438924, ) -> aunque solo una col

    if count == 0:
        meta_cols["block"].append(
            {
                "rule": "S-04", "row_count": 0
            }
        )
        return meta_cols, count

    # S-01 # -------------------------------------------------------------------------

    result_schema = duckdb.execute(
            """DESCRIBE SELECT * FROM read_parquet(?)""",
            # antes FROM parquet_schema(?) - esquema fisico del propio parquet no de duckdb
            [str(parquet_path)]
        ).fetchall()
        # name col, type data, require,  3nones for parquet
        #[('id', 'BIGINT', 'YES', None, None, None),]

            # nombre columna : tipo de dato,
    schema = {row[0].lower(): row[1] for row in result_schema}
    for col in CONTRACT_V1:
        source = col.source.lower()
        # verificas que las obligatorias (del contrato) esten antes de nada
        if source not in schema:
            # si no esta, y es required - blocked
            if col.required:
                meta_cols["block"].append(
                    {
                        "rule": "S-01", "column": col.source
                    }
                )
        else:
            # S-02 # -------------------------------------------------------------------------
            # Indicar el tipo obtenido y el tipo esperado
            parquet_type = schema[source]
            if parquet_type != col.type and (parquet_type, col.type) not in COMPATIBLE_TYPES:
                meta_cols["block"].append(
                    {
                        "rule": "S-02", "column": col.canonical,
                        "expected": col.type, "got": parquet_type
                    }
                )
    # S-03 # -------------------------------------------------------------------------
    contract_sources = {c.source.lower() for c in CONTRACT_V1}
    for name in schema:
        if name not in contract_sources:
            meta_cols["warn"].append(
                {
                    "rule": "S-03", "unknown_column": name
                }
            )

    return meta_cols, count, schema