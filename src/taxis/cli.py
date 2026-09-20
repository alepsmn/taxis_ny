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
def ingest(date: str, source_file_path: Optional[Path] = None, reprocess: bool = False, download_flag: bool = typer.Option(False, '--download'),
            raw_base_path: Path = Path('data/raw'), db_path: Path = Path('data/control/manifest.db')):

    # 1. Validar argumentos criticos
    if source_file_path and download_flag:
        print(f"Args incompatibles")
        raise SystemExit(1)

    if source_file_path is None and not download_flag:
        print(f"Argumentos incompatibles")
        raise SystemExit(1)

    # 2. Parsear fecha y download si E
    date_year, date_month = date.split('-')
    year = int(date_year)
    month = int(date_month)    

    if download_flag:
        # es raw_file_path, por simplicidad mismo nombre, se procesara igual
        source_file_path = download(year, month, raw_base_path)
        if source_file_path is None: # 404
            print(f"Recurso no encontrado para {date}")
            return

    # 3. Proceso de ingesta para el archivo obtenido/pasado por CLI
    try:
        results = run_ingest(year, month, source_file_path, raw_base_path, db_path, reprocess)
        print(json.dumps(results, indent=2))
    except FileBlocked as fb:
        print(fb)
        raise SystemExit(2)
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
            source_file_path: Optional[Path]= None, raw_base_path: Path = Path('data/raw'), db_path: Path = Path('data/control/manifest.db')):
    if download_flag and source_file_path:
        print("Flags: download_flag y source_file - ACTIVOS (incompatibles)")
        raise SystemExit(1)

    if not download_flag and source_file_path is None:
        print("Necesitas --download-flag o source_file")
        raise SystemExit(1)
    summary = run_backfill(download_flag, source_file_path, date_from, date_to, db_path, raw_base_path)
    print(json.dumps(summary, indent=2))

@app.command()
def marts():
    import subprocess
    subprocess.run(
        ["uv", "run", "dbt", "run", "--project-dir", "dbt", "--profiles-dir", "dbt"],
        check=True
    )
    # para exportar las tablas a un formato unico para cada una
    import duckdb

    db = duckdb.connect("data/marts/marts.duckdb", read_only=True)
    for mart in ["mart_hourly", "mart_daily", "mart_zone_pair"]:
        db.sql(f"COPY {mart} TO 'data/marts/{mart}.parquet' (FORMAT PARQUET)")
    db.close()