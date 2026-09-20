import hashlib, requests, shutil, time

from pathlib import Path

def get_sha256(source_file_path: Path):
    hasher = hashlib.sha256()
    with source_file_path.open('rb') as file:
        while chunk := file.read(1024*1024):
            hasher.update(chunk)
        return hasher.hexdigest()

def download(year: int, month: int, raw_base_path: Path):
    MAX_RETRIES = 4
    BACKOFF = 2
    REQUEST_TIMEOUT = 30
    REQUEST_TIMEOUT_READ = 300
    RETRAYABLE_STATUS = frozenset(
        {
            429, # TooManyRequests
            500, # InternalServerError
            502, # BadGateway
            503, # ServiceUnavailable
            504  # GatewayTimeout
        }
    )

    url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet"
    part_path = raw_base_path / f"year={year}" / f"month={month}" / f"download.part"
    part_path.parent.mkdir(parents=True, exist_ok=True)

    last_exc = Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            with requests.get(url, stream=True, timeout=(REQUEST_TIMEOUT, REQUEST_TIMEOUT_READ)) as r:
                r.raise_for_status()
                with part_path.open('wb') as p:
                    chunk = r.iter_content(chunk_size=1024*1024)
                    p.write(chunk)

                file_sha = get_sha256(part_path)
                raw_file_path = raw_base_path / f"year={year}" / f"month={month}" / f"{file_sha}.parquet"
                if  raw_file_path.exists():
                    part_path.unlink()
                    return raw_file_path

                part_path.replace(raw_file_path)
                return raw_file_path
        except requests.HTTPError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status == 400:
                return None
            if status not in RETRAYABLE_STATUS:
                print(f"TLC NY respondio con {status}. No reintentable {exc}")
                raise
            last_exc = exc
            print(f"Error {status}. Reintentando {attempt + 1}/{MAX_RETRIES}")
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_exc = exc
            print(f"Fallo en la red {exc}")

        if attempt < MAX_RETRIES - 1:
            wait = BACKOFF ** attempt
            print(f"Reintentando en {wait}s")
            time.sleep(wait)

    raise RuntimeError(
        f"Todos los reintentos fallaron (max {MAX_RETRIES})"
    ) from last_exc 
            
def get_raw_file(source_file_path: Path, raw_base_path: Path, year: int, month: int):
    file_sha = get_sha256(source_file_path)
    raw_file_path = raw_base_path / f"year={year}" / f"month={month}" / f"{file_sha}.parquet"

    raw_file_path.parent.mkdir(parents=True, exist_ok=True)
    if not raw_file_path.exists():
        # copia del archivo con sus metadatos
        shutil.copy2(source_file_path, raw_file_path)

    return file_sha, raw_file_path