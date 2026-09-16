import typer, json

from pathlib import Path

from taxis.acquire import download
from taxis.pipeline import run_ingest, run_backfill
from taxis.plan import missing_processed_files

from taxis.exceptions import ParquetNoEscrito, FileBlocked
from  typing import Optional

app = typer.Typer()

# acquire → structural → transforms → rows → batch → publish.
# uv run taxis 2024-0
# 
# 1 data/reference/yellow_tripdata_2024-01.parquet
@app.command()
def ingest(date: str, source_file: Optional[Path] = None, reprocess: bool = False, download_flag: bool = typer.Option(False, '--download'), db_path: Path = Path('data/control/manifest.db')):
    if download_flag and source_file:
        print("Flags: download_flag y source_file - ACTIVOS (incompatibles)")
        return

    if not download_flag and source_file is None:
        print("Necesitas --download-flag o source_file")
        raise SystemExit(1)
    
    if download_flag:
        year, month = date.split('-')
        # Este source file corresponde a FINAL_PATH (sha.parquet)
        # Evitando complejidad, source_file se usa para poder reusar el parametro en caso de ser pasado como arg
        source_file = download(int(year), int(month), Path('data/raw'))
        if source_file is None:
            print(f"Mes {date} no publicado en TLC (404)")
            return
    try:
        result = run_ingest(date, source_file, reprocess, db_path)
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
def backfill(date_from: str, date_to: str, download_flag: bool = typer.Option(False, '--download'), 
            source_path: Optional[Path]= None):
    if download_flag and source_path:
        print("Flags: download_flag y source_file - ACTIVOS (incompatibles)")
        raise SystemExit(1)

    if not download_flag and source_path is None:
        print("Necesitas --download-flag o source_file")
        raise SystemExit(1)
    summary = run_backfill(download_flag, source_path, date_from, date_to)
    print(json.dumps(summary, indent=2))
    