from pathlib import Path

from taxis.acquire import get_raw_file
from taxis.manifest import lookup_sha
from taxis.gates.structural import get_structural_schema
from taxis.transforms import col_transformations
from taxis.gates.rows import validate_row_quality
from taxis.gates.batch import batch_gate

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
    transformed_cols = col_transformations(schema_col_dtype)
    # Validacion de reglas de filas ~ 19
    validated_rows = validate_row_quality(transformed_cols)
    # Puerta de verificacion del lote
    metadata_batch, curated_rows, quarantine_rows, total_curated, total_quarantine, \
    each_reject_count, each_warning_count = batch_gate(validated_rows, row_count)

    if metadata_batch["reject"]:
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
        register()