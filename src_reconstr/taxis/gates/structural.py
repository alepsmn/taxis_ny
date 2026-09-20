import duckdb

from pathlib import Path

from taxis.contract import CONTRACT_V1, COMPATIBLE_TYPES

def get_structural_schema(raw_file_path: Path, ) -> tuple[dict[str, str], int, dict[str, str]]:
    metadata_cols = {
        "block": [],
        "warn": []
    }

    row_count = duckdb.execute(
        """
        SELECT COUNT(*)
        FROM read_parquet(?)
    """, [str(raw_file_path)]
    ).fetchone()[0]

    if row_count == 0:
        metadata_cols["block"].append(
            {"id": "S-04", "reason": "emtpy_file"}
        )
        return metadata_cols, row_count, None

    schema = duckdb.execute(
        """
        DESCRIBE
        SELECT *
        FROM read_parquet(?)
    """, [str(raw_file_path)]
    ).fetchall()

    schema_col_dtype = {row[0]: row[1] for row in schema}
    for col in CONTRACT_V1:
        if col.source.lower() not in schema_col_dtype:
            if col.required:
                metadata_cols["block"].append(
                    {"id": "S-01", "reason": "missed_required_column", "column": col.source}
                )
        else:
            col_type = schema_col_dtype[col.source.lower()]
            if col_type != col.type and (col_type, col.type) not in COMPATIBLE_TYPES:
                metadata_cols["block"].append(
                    {"id": "S-02", "reason": "incompatible_type", "column": col.canonical, "expected": col.type, "got": col_type}
                )

    exptected_cols = {obj.source.lower() for obj in CONTRACT_V1}
    for col in schema_col_dtype:
        if col not in exptected_cols:
            metadata_cols["warn"].append(
                {"id": "S-03", "reason": "unknown_column", "column": col}
            )

    return metadata_cols, row_count, schema_col_dtype
