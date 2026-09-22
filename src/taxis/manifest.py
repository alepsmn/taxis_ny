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
            SELECT sha256
            FROM partitions
            WHERE year=? AND month=?
        """, (year, month)
        ).fetchone() # Si esta vacio (ninguna fila cumplio) tira None

    return row[0] if row else None #(sha256x, )

def register(db_path: Path, year: int, month: int, sha: str, contract_version: int, row_count: int, curated_count: int, quarantine_count: int, published_at: str):
    ensure_schema(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        INSERT OR REPLACE INTO partitions (year, month, sha256, contract_version, row_count, curated_count, quarantine_count, published_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (year, month, sha , contract_version, row_count, curated_count, quarantine_count, published_at)
    )
    conn.commit()
    conn.close()

def lookup_published(db_path: Path, year: int, month: int) -> sqlite3.Row:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row # ahora devuelve obj Row ~ dict (acceso por claves sin depende de posiciones de tupla)
    published = conn.execute(
        """
        SELECT *
        FROM partitions
        WHERE year=? AND month=?
    """, (year, month)
    ).fetchone() 
    conn.commit()
    conn.close()

    return published
