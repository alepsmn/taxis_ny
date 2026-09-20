import typer,json

from typing import Optional
from pathlib import Path

from taxis.acquire import download

app = typer.Typer()

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