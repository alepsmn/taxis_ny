import sqlite3

from pathlib import Path

def ensure_schema(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
           """
            CREATE TABLE IF NOT EXISTS partitions (
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            sha256 TEXT NOT NULL,
            contract_version INTEGER NOT NULL,
            row_count INTEGER NOT NULL,
            curated_count INTEGER NOT NULL,
            quarantine_count INTEGER NOT NULL,
            published_at TEXT NOT NULL,
            PRIMARY KEY (year, month)
            )
        """ 
        )

def lookup_sha(db_path: Path, year: int, month: int):
    ensure_schema(db_path)
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT sha256,
            FROM partitions
            WHERE year=? AND mont=?
        """(year, month)
        ).fetchone() # Si esta vacio (ninguna fila cumplio) tira None

    return row[0] if row else None #(sha256x, )
