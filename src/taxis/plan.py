from datetime import datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path
from taxis.manifest import lookup_published

def missing_processed_files(date_from: str, date_to: str, db_path: Path) -> dict[str, str]:
    ini_date = datetime.strptime(date_from, "%Y-%m")
    end_date = datetime.strptime(date_to, "%Y-%m")

    actual_date = ini_date

    pending_tasks = []
    published_tasks = []
    expected_tasks = 0

    # itera por el rango de fecha seleccionada 
    while actual_date <= end_date:
        expected_tasks += 1
        year = actual_date.year
        month = actual_date.month

        # devuelve los metadatos de un fichero para un mes
        row = lookup_published(db_path, year, month)
        if not row:
            pending_tasks.append(f"{year}-{month:02d}")
        else:
            published_tasks.append(
                {
                    "year": row["year"], "month": row["month"],
                    "sha256": row["sha256"], "contract_version": row["contract_version"],
                    "row_count": row["row_count"], "curated_count": row["curated_count"],
                    "quarantine_count": row["quarantine_count"], "published_at": row["published_at"]
                }
            )
        actual_date += relativedelta(months=1)

    return { 
        "range": {
            "from": f"{date_from}", "to": f"{date_to}"
        },
        "total": expected_tasks,
        "published": published_tasks,
        "pending": pending_tasks
    }
