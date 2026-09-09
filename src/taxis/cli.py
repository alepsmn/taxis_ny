import typer

from pathlib import Path
from taxis.acquire import acquire
from taxis.gates.structural import comparing_schemas
from taxis.transforms import transform
from taxis.gates.rows import row_rule

app = typer.Typer()
# acquire → structural → transforms → rows → batch → publish.
# uv run taxis 2024-01 data/reference/yellow_tripdata_2024-01.parquet
@app.command()
def ingest(date: str, source: Path): # Typer convierte a los tipos indicados
    year, month = date.split('-') # '2024', '01'
    sha, dest = acquire(source, Path("data/raw"), int(year), int(month))

    door_cols_info, row_count, schema = comparing_schemas(source)
    import json

    result = {
        "month": date,
        "sha256": sha,
        "row_count": row_count,
        "gates": door_cols_info
    }
    print(json.dumps(result, indent=2))

    if door_cols_info["block"]:
        raise SystemExit(2)

    transformed = transform(dest, sha, int(year), int(month), schema)
    rows_ruled = row_rule(transformed)
    
    #print(result)