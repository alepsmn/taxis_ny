import duckdb, json

from taxis.acquire import get_file, download
from taxis.manifest import lookup, register
from taxis.gates.structural import get_structural_schema
from taxis.transforms import col_transformations
from taxis.gates.rows import validate_row_quality
from taxis.gates.batch import batch_gate
from taxis.publish import publish
from taxis.plan import missing_processed_files

from taxis.exceptions import FileBlocked, ParquetNoEscrito
from datetime import datetime, timezone
from pathlib import Path


def run_ingest(year: int, month:int, source_file_path: Path, reprocess: bool = False, db_path: Path = Path('data/control/manifest.db')):
    file_sha, raw_file_path = get_file(source_file_path, Path('data/raw'), year, month)

    if not reprocess:
        revised_sha = lookup(db_path, year, month)
        # No son fallos de bloqueo, avisan y continuan si se hacen varias ingestas seguidas
        if revised_sha == file_sha:
            return {"status": "skipped", "reason": "already_published"}
        if revised_sha is not None:
            # ya hay un sha para esa fecha y no coincide con el del archivo actual
            return {"status": "revision detected", "message": "try: --reprocess"}

    metadata_cols, row_count, file_schema = get_structural_schema(raw_file_path)
    print(json.dumps(metadata_cols, indent=2))
    if metadata_cols["block"]:
        raise FileBlocked(metadata_cols, "S", year, month)

    transformed_cols = col_transformations(raw_file_path, file_schema, file_sha, year, month)
    validated_rows = validate_row_quality(transformed_cols)

    meta_batch, curated_rows, quarantine_rows, total_curated, total_quarantine, reasons_rejected_count, reasons_warning_count = batch_gate(validated_rows, row_count)

    if meta_batch["block"]:
        raise FileBlocked(meta_batch, "B", year, month)

    tasks = [
        {"rows": curated_rows, "type_rows": "curated_rows"},
        {"rows": quarantine_rows, "type_rows": "quarantine_rows"}
    ]

    written_paths = []

    for task in tasks:
        final_path = publish(task["rows"], task["type_rows"], int(year), int(month))
        if final_path:
            written_paths.append(final_path)
            print(f"Documento {task['type_rows']} escrito con exito")

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
            "rejected_count": reasons_rejected_count,
            "warning_count": reasons_warning_count,
        }
    
    return result

# source_path: donde estan los archivos originales descargados - data/reference
def run_backfill(download_flag: bool, source_path: Path, date_from: str, date_to: str, db_path: Path = Path('data/control/manifest.db')):
    info_missed = missing_processed_files(date_from, date_to, db_path)
    pending_tasks = info_missed["pending"]
    processed_tasks = 0
    not_found_paths = []
    error = None
    
    for task in pending_tasks:
        year, month = task.split('-')

        if download_flag:
            final_path = download(int(year), int(month), Path('data/raw'))
            if final_path is None:
                not_found_paths.append(task)
                continue # siguiente iter para evitar el None
        else:
            final_path = source_path / f"yellow_tripdata_{year}-{month}.parquet"
            if not final_path.exists():
                not_found_paths.append(task)
                continue

        try:
            result = run_ingest(task, final_path)
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