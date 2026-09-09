import typer, duckdb, json

from pathlib import Path
from taxis.acquire import acquire
from taxis.gates.structural import comparing_schemas
from taxis.transforms import transform
from taxis.gates.rows import row_rule
from taxis.gates.batch import batch_door
from taxis.publish import publication_parquet
from taxis.exceptions import ParquetNoEscrito

app = typer.Typer()

# acquire → structural → transforms → rows → batch → publish.
# uv run taxis 2024-01 data/reference/yellow_tripdata_2024-01.parquet
@app.command()
def ingest(date: str, source: Path): # Typer convierte a los tipos indicados
    year, month = date.split('-') # '2024', '01'
    sha, dest = acquire(source, Path("data/raw"), int(year), int(month))

    door_cols_info, row_count, schema = comparing_schemas(source)

    if door_cols_info["block"]:
        raise SystemExit(2)

    transformed = transform(dest, sha, int(year), int(month), schema)
    rows_ruled = row_rule(transformed)


    meta_batch, curated, quarantine, total_curated, total_quarantine, rejected_count, warning_count = batch_door(rows_ruled, row_count)

    print(json.dumps(meta_batch, indent=2))

    if meta_batch["block"]:
        raise SystemExit(2)

    tareas = [
        {"rows": curated, "type_rows": "curated", "year": int(year), "month": int(month)},
        {"rows": quarantine, "type_rows": "quarantine", "year": int(year), "month": int(month)},
    ]
    published_paths = []
    for tarea in tareas:
        try:
            exito = publication_parquet(tarea['rows'], tarea['type_rows'], tarea['year'], tarea['month'])
            published_paths.append(exito)
            if exito:
                print(f"Documento {tarea['type_rows']} escrito con exito")
        except ParquetNoEscrito as err:
            print(f"Error controlado externamente: {err}")
        except Exception as e:
            print(f"Error no esperado: {e}")

    result = {
        "month": date,
        "sha256": sha,
        "row_count": row_count,
        "gates": door_cols_info,
        "total_curated": total_curated,
        "total_quarantine": total_quarantine,
        "rejected_count": rejected_count,
        "warning_count": warning_count,
    }
    print(json.dumps(result, indent=2))
    

