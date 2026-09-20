import duckdb

from duckdb import DuckDBPyRelation
from pathlib import Path


def publish(rows: DuckDBPyRelation, type_rows: str, year: int, month: int):
    temp_path = Path(f"data/staging/{type_rows}/download.part")
    base_path = Path(f"data/{type_rows}")

    try:
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        rows.write_parquet(temp_path)

        final_path = base_path / f"year={year}" / f"month={month}" / f"{type_rows}.parquet"
        final_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.replace(final_path)

        return False if not final_path.exists() else final_path

    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        raise ParquetNoEscrito(year, month, type_rows) from e

        