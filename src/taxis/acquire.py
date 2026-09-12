import hashlib, shutil

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


def get_file(source_path: Path, raw_base_path: Path, year: int, month: int) -> tuple[str, Path]:
    file_sha = get_sha56(source_path)
    raw_file_path = raw_base_path / f"year={year}" / f"month={month:02d}" / f"{file_sha}.parquet"

    raw_file_path.parent.mkdir(parents=True, exist_ok=True)
    if not raw_file_path.exists():
        shutil.copy2(source_path, raw_file_path)

    return file_sha, raw_file_path