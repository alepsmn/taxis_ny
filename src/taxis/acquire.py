import hashlib, shutil, requests, time

from pathlib import Path

def get_sha56(source_path: Path) -> str:
    hasher = hashlib.sha256()
    with source_path.open('rb') as parquet_file:
        # while True:
        #     chunk = parquet_file.read(1024*1024)
        #     if not chunk:
        #         break
        #     hasher.update(chunk)

        while chunk := parquet_file.read(1024*1024):
            hasher.update(chunk)

        return hasher.hexdigest()

def get_file(source_file_path: Path, raw_base_path: Path, year: int, month: int) -> tuple[str, Path]:
    file_sha = get_sha56(source_file_path)
    raw_file_path = raw_base_path / f"year={year}" / f"month={month:02d}" / f"{file_sha}.parquet"

    raw_file_path.parent.mkdir(parents=True, exist_ok=True)
    if not raw_file_path.exists():
        shutil.copy2(source_file_path, raw_file_path)

    return file_sha, raw_file_path

def download(year: int, month: int, raw_base_path: Path) -> Path:   # data/reference
    REQUEST_TIMEOUT = 30 # segs
    REQUEST_TIMEOUT_READ = 300
    MAX_RETRIES = 4
    BACKOFF_BASE = 2 
    # TooManyRequests/IntervalServerError/BadGateway/ServiceUnavailable/GatewayTimeout
    RETRAYABLE_STATUS = frozenset({429, 500, 502, 503, 504})

    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet"
    part_path = raw_base_path / f"year={year}" / f"month={month:02d}" / "download.part"
    part_path.parent.mkdir(parents=True, exist_ok=True)

    last_exc : Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            # aseguramos la conexion de red, para q no se cierre
            with requests.get(url, stream=True, timeout=(REQUEST_TIMEOUT, REQUEST_TIMEOUT_READ)) as r:
                r.raise_for_status()
                with part_path.open('wb') as f:
                    print("Escribiendo documento")
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        f.write(chunk)
                # este renombre se hace para evitar que run_ingest, al llamar a get_file no duplique el archivo
                # asi, se asegura la comprobacion de existencia por contenido, no por llamada
                file_sha = get_sha56(part_path)
                final_path = raw_base_path / f"year={year}" / f"month={month:02d}" / f"{file_sha}.parquet"

                # evite sobreescribir (si se llama solo a ingest)
                if final_path.exists():
                    part_path.unlink()
                    return final_path
                
                part_path.replace(final_path)
                return final_path
        except requests.HTTPError as exc:
            # valida que exista respuesta antes de asignar status_code
            status = exc.response.status_code if exc.response is not None else None
            if status == 404:
                print(f"Fallo: no se encontro el archivo buscado")
                return None
            if status not in RETRAYABLE_STATUS:
                print(f"TLC NY respondio {status} (No recupereable: {exc})")
                raise
            last_exc = exc
            print(f"TLC NY {status} - Intento: {attempt + 1}/{MAX_RETRIES}")
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_exc = exc
            print(f"Fallo de red: {exc}")

        if attempt < MAX_RETRIES - 1:
            wait = BACKOFF_BASE ** attempt
            print(f"Reintentando en {str(wait)}s")
            time.sleep(wait)

    raise RuntimeError(
        f"TLC NY no respondio tras: {MAX_RETRIES} intentos"
    ) from last_exc