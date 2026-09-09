import hashlib, shutil

from pathlib import Path

def calculate_sha256(path: Path) -> str:
    hasher = hashlib.sha256()

    with path.open("rb") as parquet_file:
        # operador morsa - walrose
        # lee 1MB y lo asigna a chunk; evalua si chunk es algo / tiene datos
        while chunk := parquet_file.read(1024*1024):
            hasher.update(chunk)
        return hasher.hexdigest() # a str de caracteres hexadecimales

        # while True:
        #     chunk = parquet_file.read(1024*1024)
        #     if not chunk:
        #         break
        #     hasher.update(chunk)
                                                                # hash, ruta final
def acquire(source: Path, raw_dir: Path, year: int, month:int) -> tuple[str, Path]:
    actual_sha256 = calculate_sha256(source) # formateo Enero - 01
    final_path = raw_dir / f"year={year}" / f"month={month:02d}" / f"{actual_sha256}.parquet"
    # copiar a data/raw/year=YYYY/month=MM/<hash>.parquet (si no existe)
    final_path.parent.mkdir(parents=True, exist_ok=True) # directorio sin hash.parquet para crearlo: padres y si ya existe no hace nada
    if not final_path.exists(): # comprueba si el archivo no existe
        shutil.copy2(source, final_path) # lo copia de source a final_path

    return actual_sha256, final_path


