import duckdb
from pathlib import Path
from taxis.contract import CONTRACT_V1, COMPATIBLE_TYPES

def get_structural_schema(raw_file_path: Path, ) -> tuple[dict[str, str], int, dict[str, str]]:
    meta_cols = {
        "block": [],
        "warn": []
    }

    row_count = duckdb.execute(
        """
        SELECT COUNT(*)
        FROM read_parquet(?)
    """, [str(raw_file_path)]
    ).fetchone()[0] #

    if row_count == 0:
        meta_cols["block"].append(
            {"id": "S-04", "reason": "empty_file"}
        )
        return meta_cols, row_count, None

    object_schema = duckdb.execute(
        """
        DESCRIBE
        SELECT *
        FROM read_parquet(?)
    """, [str(raw_file_path)]
    ).fetchall()

    file_schema = {schema[0].lower(): schema[1] for schema in object_schema}

    for col in CONTRACT_V1:
        if col.source.lower() not in file_schema:
            if col.required:
                meta_cols["block"].append(
                    {"id": "S-01", "reason": "missing_required_column", "column": col.source}
                )
        else:
            parquet_type = file_schema[col.source.lower()]
            if col.type != parquet_type and (parquet_type, col.type) not in COMPATIBLE_TYPES:
                meta_cols["block"].append(
                    {"id": "S-02", "reason": "incompatible_type", "column": col.canonical, "expected": col.type, "got": parquet_type}
                )

    expected_cols = {obj.source.lower() for obj in CONTRACT_V1}
    for col in file_schema:
        if col not in expected_cols:
            meta_cols["warn"].append(
                {"id": "S-03", "reason": "unknown_column", "column": col}
            )

    return meta_cols, row_count, file_schema