import sqlite3

from pathlib import Path

def lookup(db_path: Path, year: int, month: int) -> str:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
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

    sha = conn.execute(
        """
        SELECT sha256
        FROM partitions
        WHERE year=? AND month=?
    """, (year, month)
    ).fetchone()

    conn.commit()
    conn.close()

    return sha[0] if sha else None

def register(db_path: Path, year: int, month: int, sha: str, contract_version: int, row_count: int, curated_count: int, quarantine_count: int, published_at: str):
    conn = sqlite3.connect(str(db_path))
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
    conn.execute(
        """
        INSERT INTO partitions (year, month, sha256, contract_version, row_count, curated_count, quarantine_count, published_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (year, month, sha , contract_version, row_count, curated_count, quarantine_count, published_at)
    )

    conn.commit()
    conn.close()