import duckdb


PARQUET_PATH = "data/reference/yellow_tripdata_2024-01.parquet"


file_metadata = duckdb.execute(

    # num_row_groups: como estan agrupadas FISICAMENTE
    # parquet_file_metadata(?) - f. de duckdb para acceder al footer c Metadatos
    # ? - se inserta la ruta de manera segura
    """
    SELECT
        file_name,
        num_rows,
        num_row_groups,
        format_version,
        file_size_bytes,
        footer_size
    FROM parquet_file_metadata(?)
    """,
    [PARQUET_PATH],
).fetchone()

schema = duckdb.execute(
    """
    SELECT name, type
    FROM parquet_schema(?)
    WHERE num_children IS NULL
    """,
    [PARQUET_PATH],
).fetchall()

row_groups = duckdb.execute(
    # Elimina repeticiones cuando todas las cols son del mismo
    # grupo usan la misma compresion
    # Compression
    """
    SELECT DISTINCT
        row_group_id,
        row_group_num_rows,
        compression
    FROM parquet_metadata(?)
    ORDER BY row_group_id, compression
    """,
    [PARQUET_PATH],
).fetchall()


print("METADATOS DEL ARCHIVO")
print(file_metadata)

print(f"\nESQUEMA FÍSICO: {len(schema)} columnas")
for name, physical_type in schema:
    print(f"{name}: {physical_type}")

print("\nROW GROUPS")
for row_group_id, num_rows, compression in row_groups:
    print(
        f"row_group={row_group_id}, "
        f"filas={num_rows}, "
        f"compresión={compression}"
    )