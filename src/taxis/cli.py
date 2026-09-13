import typer, json

from pathlib import Path

from taxis.pipeline import run_ingest, run_backfill
from taxis.plan import missing_processed_files

from taxis.exceptions import ParquetNoEscrito, FileBlocked

app = typer.Typer()

# acquire → structural → transforms → rows → batch → publish.
# uv run taxis 2024-0
# 
# 1 data/reference/yellow_tripdata_2024-01.parquet
@app.command()
def ingest(date: str, source_path: Path, reprocess: bool = False, db_path: Path = Path('data/control/manifest.db')):
    try:
        result = run_ingest(date, source_path, reprocess, db_path)
        print(json.dumps(result, indent=2))
    except FileBlocked as fb:
        # imprime el mensaje original overrideado
        print(fb)
        raise SystemExit(2)
        #print(f"Block en puerta {fb.type_block}: {fb.metadata_cols}") - otra opcion para modificar el mensaje original
    except ParquetNoEscrito as pn:
        print(pn)
        raise SystemExit(3)

# uv run taxis plan
@app.command()
def plan(date_from: str = "2024-01", date_to: str = "2025-12", db_path: Path = Path('data/control/manifest.db')):
    result = missing_processed_files(date_from, date_to, db_path)
    print(json.dumps(result, indent=2))

@app.command()
def backfill(source_path: Path, date_from: str, date_to: str):
    summary = run_backfill(source_path, date_from, date_to)
    print(json.dumps(summary, indent=2))
    