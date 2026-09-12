import typer, duckdb, json

from pathlib import Path
from taxis.acquire import get_file
from taxis.manifest import lookup, register
from taxis.gates.structural import get_structural_schema
from taxis.transforms import col_transformations
from taxis.gates.rows import validate_row_quality
from taxis.gates.batch import batch_gate
from taxis.publish import publish
from taxis.exceptions import ParquetNoEscrito
from datetime import datetime, timezone


app = typer.Typer()

# acquire → structural → transforms → rows → batch → publish.
# uv run taxis 2024-01 data/reference/yellow_tripdata_2024-01.parquet
@app.command()
def ingest(date: str, source_path: Path, reprocess: bool = False, db_path: Path = Path('data/control/manifest.db')):
    year, month = date.split('-')
    file_sha, raw_file_path = get_file(source_path, Path('data/raw'), int(year), int(month))

    if reprocess:
        revised_sha = lookup(db_path, int(year), int(month))
        if file_sha == revised_sha:
            print("Ya publicado. Nada que hacer")
            raise SystemExit(0)
        if revised_sha is not None:
            print("Revision detectada; sha distinto")
            raise SystemExit(1)

    metadata_cols, row_count, file_schema = get_structural_schema(raw_file_path)

    print(json.dumps(metadata_cols, indent=2))
    if metadata_cols["block"]:
        print("Hay fallos tipo - block (S) - que revisar")
        raise SystemExit(2)

    transformed_cols = col_transformations(raw_file_path, file_schema, file_sha, int(year), int(month))

    validated_rows = validate_row_quality(transformed_cols)

    meta_batch, curated_rows, quarantine_rows, total_curated, total_quarantine, reasons_rejected_count, reasons_warning_count = batch_gate(validated_rows, row_count)

    if meta_batch["block"]:
        print("Hay fallos tipo block (B) - que revisar")
        raise SystemExit(3)

    tasks = [
        {"rows": curated_rows, "type_rows": "curated_rows"},
        {"rows": quarantine_rows, "type_rows": "quarantine_rows"},
    ]
    written_paths = []
    for task in tasks:
        try:
            final_path = publish(task["rows"], task["type_rows"], int(year), int(month))
            if final_path:
                written_paths.append(final_path)
                print(f"Documento {task['type_rows']} escrito con exito")

        except ParquetNoEscrito as err:
            print(f"Error controlado externamente: {err}")
        except Exception as e:
            print(f"Error no esperado: {e}")

    if all(written_paths):
        published_at = datetime.now(timezone.utc).isoformat()
        register(db_path, int(year), int(month), file_sha, 1, int(row_count), int(total_curated), int(total_quarantine), published_at)

    result = {
        "month": date,
        "sha256": file_sha,
        "row_count": row_count,
        "gates": metadata_cols,
        "total_curated": total_curated,
        "total_quarantine": total_quarantine,
        "rejected_count": reasons_rejected_count,
        "warning_count": reasons_warning_count,
    }

    print(json.dumps(result, indent=2))
    

