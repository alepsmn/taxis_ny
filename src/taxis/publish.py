import duckdb
from duckdb import DuckDBPyRelation
from taxis.exceptions import ParquetNoEscrito
from pathlib import Path

def publication_parquet(rows: DuckDBPyRelation, type_rows: str, year: int, month: int) -> bool | Exception | Path:
    temp_path = Path(f"data/staging/{type_rows}.parquet")
    base_path = Path(f"data/{type_rows}")

    try:
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        rows.write_parquet(str(temp_path))

        final_path = base_path / f"year={year}" / f"month={month}" / f"{type_rows}.parquet"
        final_path.parent.mkdir(parents=True, exist_ok=True)
        temp_path.replace(final_path)
        
        if final_path.exists():
            return final_path
        else:
            return False

    except Exception as e:
        if temp_path.exists(): # si el temporal se creo, se borra
            temp_path.unlink()
        raise ParquetNoEscrito(year, month, type_rows) from e
