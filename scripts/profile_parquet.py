import argparse
import hashlib
import json
import sys
from pathlib import Path

import duckdb


FREQUENCY_COLUMN_NAMES = (
    "VendorID",
    "RatecodeID",
    "store_and_fwd_flag",
    "payment_type",
    "PULocationID",
    "DOLocationID",
    "passenger_count",
)

PASSENGER_COUNT_COLUMN_NAME = "passenger_count"


def calculate_sha256(path: Path) -> str:
    hasher = hashlib.sha256()

    with path.open("rb") as parquet_file:
        while chunk := parquet_file.read(1024 * 1024):
            hasher.update(chunk)

    return hasher.hexdigest()


def calculate_percentage(count: int, total: int) -> float:
    if total == 0:
        return 0.0

    return round(count / total * 100, 6)


def build_frequency_metrics(
    frequency_rows: list[tuple[object, int]],
    row_count: int,
) -> dict[str, object]:
    item_frequencies = []
    item_distinct_non_null = 0

    for value, value_count in frequency_rows:
        if value is not None:
            item_distinct_non_null += 1

        item_frequencies.append(
            {
                "value": value,
                "count": value_count,
                "percentage": calculate_percentage(value_count, row_count),
            }
        )

    return {
        "distinct_non_null": item_distinct_non_null,
        "frequencies": item_frequencies,
    }


def build_passenger_count_metrics(
    frequency_rows: list[tuple[object, int]],
    row_count: int,
) -> dict[str, object]:
    metrics = build_frequency_metrics(frequency_rows, row_count)
    non_null_values: list[int | float] = []
    negative_count = 0

    for value, value_count in frequency_rows:
        if value is None:
            continue
        if not isinstance(value, (int, float)):
            raise TypeError(
                "passenger_count debe contener valores numericos o NULL"
            )

        non_null_values.append(value)
        if value < 0:
            negative_count += value_count

    metrics.update(
        {
            "minimum": min(non_null_values, default=None),
            "maximum": max(non_null_values, default=None),
            "negative_count": negative_count,
            "negative_percentage": calculate_percentage(
                negative_count,
                row_count,
            ),
        }
    )
    return metrics


def fetch_frequency_rows(
    connection: duckdb.DuckDBPyConnection,
    parquet_path: Path,
    column_name: str,
) -> list[tuple[object, int]]:
    if column_name not in FREQUENCY_COLUMN_NAMES:
        raise ValueError(f"columna de frecuencia no permitida: {column_name}")

    query = f"""
        SELECT
            {column_name} AS value,
            COUNT(*) AS value_count
        FROM read_parquet(?)
        GROUP BY {column_name}
        ORDER BY {column_name} ASC NULLS FIRST
    """
    return connection.execute(query, [str(parquet_path)]).fetchall()


def find_column(
    column_name: str,
    columns: list[dict[str, object]],
) -> dict[str, object]:
    return next(
        column
        for column in columns
        if column["name"] == column_name
    )


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("parquet_path", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)

    if not args.parquet_path.is_file():
        parser.error(f"no existe un archivo regular: {args.parquet_path}")

    expected_sha256 = args.expected_sha256.lower()

    has_valid_length = len(expected_sha256) == 64
    has_only_hex_digits = all(
        character in "0123456789abcdef"
        for character in expected_sha256
    )

    if not has_valid_length or not has_only_hex_digits:
        parser.error(
            "--expected-sha256 debe contener exactamente "
            "64 caracteres hexadecimales"
        )

    actual_sha256 = calculate_sha256(args.parquet_path)

    if actual_sha256 != expected_sha256:
        print(
            "error: SHA-256 incorrecto; "
            f"esperado={expected_sha256}, obtenido={actual_sha256}",
            file=sys.stderr,
        )
        return 1

    with duckdb.connect() as connection:
        row_count = connection.execute(
            "SELECT count(*) FROM read_parquet(?)",
            [str(args.parquet_path)],
        ).fetchone()[0]

        schema_rows = connection.execute(
            "DESCRIBE SELECT * FROM read_parquet(?)",
            [str(args.parquet_path)],
        ).fetchall()

        columns: list[dict[str, object]] = []
        for schema_row in schema_rows:
            columns.append(
                {
                    "name": schema_row[0],
                    "logical_type": schema_row[1],
                }
            )

        non_null_counts = connection.execute(
            "SELECT COUNT(COLUMNS(*)) FROM read_parquet(?)",
            [str(args.parquet_path)],
        ).fetchone()

        for column, non_null_count in zip(
            columns,
            non_null_counts,
            strict=True,
        ):
            null_count = row_count - non_null_count

            column["null_count"] = null_count
            column["null_percentage"] = calculate_percentage(
                null_count,
                row_count,
            )

        for column_name in FREQUENCY_COLUMN_NAMES:
            frequency_rows = fetch_frequency_rows(
                connection,
                args.parquet_path,
                column_name,
            )
            column = find_column(column_name, columns)

            if column_name == PASSENGER_COUNT_COLUMN_NAME:
                metrics = build_passenger_count_metrics(
                    frequency_rows,
                    row_count,
                )
            else:
                metrics = build_frequency_metrics(
                    frequency_rows,
                    row_count,
                )

            column["metrics"] = metrics

    profile = {
        "profile_version": 1,
        "row_count": row_count,
        "columns": columns,
        "source": {
            "file_name": args.parquet_path.name,
            "sha256": actual_sha256,
            "size_bytes": args.parquet_path.stat().st_size,
        },
    }

    json.dump(profile, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
