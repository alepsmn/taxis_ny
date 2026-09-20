import duckdb, json

from taxis.acquire import get_raw_file, download
from taxis.manifest import lookup_sha, register
from taxis.gates.structural import get_structural_schema
from taxis.transforms import col_transformations
from taxis.gates.rows import validate_row_quality
from taxis.gates.batch import batch_gate
from taxis.publish import publish
from taxis.plan import missing_processed_files

from taxis.exceptions import FileBlocked, ParquetNoEscrito
from datetime import datetime, timezone
from pathlib import Path


def run_ingest(year: int, month:int, source_file_path: Path, raw_base_path: Path, db_path: Path, reprocess: bool = False):
    file_sha, raw_file_path = get_raw_file(source_file_path, raw_base_path, year, month)

    if not reprocess:
        revised_sha = lookup_sha(db_path, year, month)
        if file_sha == revised_sha: # ya existe/publicado
            return {"status": "skipped", "reason": "already_published"}
        if revised_sha is not None: # existe pero posiblemente hay cambios
            return {"status": "revision_detected", "reason": "try --reprocess"}

    # Puerta de esquema - como es solo extraer datos: duckdb.execute
    metadata_cols, row_count, schema_col_dtype = get_structural_schema(raw_file_path)
    if metadata_cols["block"]:
        raise FileBlocked(metadata_cols, "S", year, month)
    # Transformaciones que se acarrearan - duckdb.sql
    transformed_cols = col_transformations(raw_file_path, schema_col_dtype, file_sha, year, month)
    # Validacion de reglas de filas ~ 19
    validated_rows = validate_row_quality(transformed_cols)
    # Puerta de verificacion del lote
    metadata_batch, curated_rows, quarantine_rows, total_curated, total_quarantine, \
    each_reject_count, each_warning_count = batch_gate(validated_rows, row_count)

    if metadata_batch["block"]:
        raise FileBlocked(metadata_batch, "B", year,month)

    tasks = [
        {"rows": curated_rows, "type_rows": "curated_rows"},
        {"rows": quarantine_rows, "type_rows": "quarantine_rows"}
    ]

    written_paths = []
    for task in tasks:
        final_path = publish(task["rows"], task["type_rows"], year, month)
        if final_path:
            written_paths.append(final_path)
            print(f"Docuemnto {task['type_rows']} escrito con extio")

    if all(written_paths):
        published_at = datetime.now(timezone.utc).isoformat()
        register(db_path, year, month, file_sha, 1, int(row_count), int(total_curated), int(total_quarantine), published_at)

    result = {
            "year": year,
            "month": month,
            "sha256": file_sha,
            "row_count": row_count,
            "gates": metadata_cols,
            "total_curated": total_curated,
            "total_quarantine": total_quarantine,
            "rejected_count": each_reject_count,
            "warning_count": each_warning_count,
        }
    
    return result

# source_path: donde estan los archivos originales descargados - data/reference
def run_backfill(download_flag: bool, source_file_path: Path, date_from: str, date_to: str, db_path: Path, raw_base_path: Path):
    info_missed = missing_processed_files(date_from, date_to, db_path)
    pending_tasks = info_missed["pending"]
    processed_tasks = 0
    not_found_paths = []
    error = None
    
    for task in pending_tasks:
        date_year, date_month = task.split('-')
        year = int(date_year)
        month = int(date_month)

        if download_flag:
            raw_file_path = download(year, month, raw_base_path)
            if raw_file_path is None:
                not_found_paths.append(task)
                continue # siguiente iter para evitar el None
        else:
            raw_file_path = source_file_path / f"yellow_tripdata_{year}-{month}.parquet"
            if not raw_file_path.exists():
                not_found_paths.append(task)
                continue

        try:
            result = run_ingest(year, month, raw_file_path)
            processed_tasks += 1
            print(json.dumps(result, indent=2))
        except (FileBlocked, ParquetNoEscrito) as e:
            error = {"task": task, "error": str(e)}
            break

    balance_summary = {
        "total_tasks": len(pending_tasks),
        "processed_tasks": processed_tasks,
        "not_found_tasks": len(not_found_paths),
        "pending_paths": not_found_paths,
        "error": error,
        "unprocessed_tasks": len(pending_tasks) - processed_tasks
    }
    return balance_summary