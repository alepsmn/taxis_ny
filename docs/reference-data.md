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