# Datos de referencia

Archivos utilizados para el reconocimiento inicial de NYC TLC Yellow Taxi.
Los Parquet se almacenan localmente bajo `data/reference/` y no se versionan.

Fuente oficial: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

| Mes | URL | Descarga local completada | Tamaño (bytes) | SHA-256 |
|---|---|---:|---:|---|
| 2024-01 | https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet | 2026-08-06 19:16:46 +02:00 | 49961641 | `c4d59da7bbc8abaeeeb1727947ee93d9891a71acb42854bd80db1571b2030510` |
| 2025-01 | https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet | 2026-08-06 19:21:51 +02:00 | 59158238 | `9af277e4c0d3f9deb30644da822981e1e7df6af58313170fd3aa8a474485488a` |

## Verificación

```bash
stat -c '%n | %s bytes' data/reference/*.parquet
sha256sum data/reference/*.parquet
git status --short
```

## Interpretación

Un cambio futuro de SHA-256 para el mismo mes se tratará como una posible
revisión del origen, no como el mismo archivo.

## Metadatos físicos de Yellow Taxi 2024-01

Procedimiento:

```bash
uv sync
uv run python scripts/inspect_parquet_metadata.py
```

Resultado verificado el 12 de agosto de 2026:

- Filas: 2.964.624.
- Columnas físicas: 19.
- Row groups: 3.
- Filas por row group: 1.048.576, 1.048.576 y 867.472.
- Compresión: ZSTD en todos los column chunks.
- Tipos físicos observados: INT32, INT64, DOUBLE y BYTE_ARRAY.

| Columna | Tipo físico |
|---|---|
| VendorID | INT32 |
| tpep_pickup_datetime | INT64 |
| tpep_dropoff_datetime | INT64 |
| passenger_count | INT64 |
| trip_distance | DOUBLE |
| RatecodeID | INT64 |
| store_and_fwd_flag | BYTE_ARRAY |
| PULocationID | INT32 |
| DOLocationID | INT32 |
| payment_type | INT64 |
| fare_amount | DOUBLE |
| extra | DOUBLE |
| mta_tax | DOUBLE |
| tip_amount | DOUBLE |
| tolls_amount | DOUBLE |
| improvement_surcharge | DOUBLE |
| total_amount | DOUBLE |
| congestion_surcharge | DOUBLE |
| Airport_fee | DOUBLE |

El script consulta el footer Parquet mediante las funciones
`parquet_file_metadata()`, `parquet_schema()` y `parquet_metadata()` de
DuckDB. No realiza perfilado de valores ni carga todas las filas.