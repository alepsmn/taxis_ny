# Reglas de validación y transformaciones, v0

Este catálogo es lo que el código implementa. Cada regla tiene un id estable, una severidad (D-08), una condición expresada de forma que se traduzca directamente a SQL de DuckDB, y un `reason_code` que aparece en quarantine o en el resumen.
Los umbrales numéricos son configuración (`config.toml` o similar), no constantes en el código.
Las columnas se nombran con el contrato canónico v1 (D-15), es decir, después de T-01.

Los porcentajes de impacto se midieron sobre 2024-01. Sirven para calibrar, no para decidir validez.

## Contrato canónico v1

| Canónico | En origen | Tipo | Obligatoria |
|---|---|---|---|
| vendor_id | VendorID | INTEGER | sí |
| pickup_at | tpep_pickup_datetime | TIMESTAMP | sí |
| dropoff_at | tpep_dropoff_datetime | TIMESTAMP | sí |
| passenger_count | passenger_count | INTEGER | no |
| trip_distance | trip_distance | DOUBLE | sí |
| ratecode_id | RatecodeID | INTEGER | no |
| store_and_fwd_flag | store_and_fwd_flag | VARCHAR | no |
| pu_location_id | PULocationID | INTEGER | sí |
| do_location_id | DOLocationID | INTEGER | sí |
| payment_type | payment_type | INTEGER | sí |
| fare_amount | fare_amount | DECIMAL(10,2) | sí |
| extra | extra | DECIMAL(10,2) | sí |
| mta_tax | mta_tax | DECIMAL(10,2) | sí |
| tip_amount | tip_amount | DECIMAL(10,2) | sí |
| tolls_amount | tolls_amount | DECIMAL(10,2) | sí |
| improvement_surcharge | improvement_surcharge | DECIMAL(10,2) | sí |
| total_amount | total_amount | DECIMAL(10,2) | sí |
| congestion_surcharge | congestion_surcharge | DECIMAL(10,2) | no |
| airport_fee | Airport_fee / airport_fee | DECIMAL(10,2) | no |
| cbd_congestion_fee | cbd_congestion_fee | DECIMAL(10,2) | no |

"Obligatoria" significa que la columna debe existir en el fichero (S-01). Que una fila tenga NULL en ella es asunto de las reglas R-xx.
El mapeo de nombres de origen no distingue mayúsculas.

## S. Puerta estructural (sobre el esquema del fichero, antes de leer filas)

| Id | Condición | Severidad | reason_code | Por qué |
|---|---|---|---|---|
| S-01 | Falta alguna columna obligatoria | block | `missing_required_column` | Sin ella el contrato no se puede aplicar (D-16). |
| S-02 | Alguna columna existe pero su tipo no se puede convertir al del contrato (p. ej. VARCHAR en un importe) | block | `incompatible_type` | Un cast que falla a mitad de fichero no es recuperable fila a fila. INT32 a INTEGER, INT64 a INTEGER y DOUBLE a DECIMAL sí son convertibles. |
| S-03 | El fichero trae columnas que no están en el contrato | warn | `unknown_column` | Es compatible hacia delante; se descarta y se avisa para valorar añadirla (D-16). |
| S-04 | El fichero tiene 0 filas | block | `empty_file` | Un mes vacío es un fallo de descarga o del origen, no un dato. |

Detalle de S-02: la comprobación en la tarea 1 es por lista blanca de pares (tipo origen, tipo contrato) aceptados. Un INT64 con valores que no caben en INTEGER se detectaría en T-02 al hacer el cast; eso pasa a `block` en la puerta de lote (B-03).

## T. Transformaciones (lista ordenada; el flujo solo recorre la lista)

| Id | Qué hace | Por qué |
|---|---|---|
| T-01 | Renombra columnas de origen a canónicas según el contrato, sin distinguir mayúsculas | D-15. |
| T-02 | Cast a los tipos del contrato. DOUBLE a DECIMAL(10,2) con redondeo a 2 decimales | D-15. Los valores del origen ya tienen 2 decimales; el redondeo solo limpia ruido binario. |
| T-03 | Añade como NULL las columnas opcionales que no existan en el fichero | D-16. |
| T-04 | Deriva `duration_min` = minutos entre pickup y dropoff, como DOUBLE | La usan R-02, R-03 y la mayoría de los marts. Se calcula una vez. |
| T-05 | Añade linaje: `source_sha256`, `source_year`, `source_month`, `contract_version` = 1, `ingested_at` = timestamp de ejecución | D-05 y D-06. Cualquier fila de curated debe poder rastrearse hasta sus bytes de origen. |

Orden fijo: T-01 → T-05. Añadir una transformación es añadir un elemento a la lista con su posición; el flujo principal no cambia.
`ingested_at` es el único campo no determinista; queda excluido de las comparaciones en tests.

## R. Reglas de fila (después de T-xx; todas se evalúan para cada fila, D-07)

| Id | Condición | Severidad | reason_code | Impacto 2024-01 | Por qué |
|---|---|---|---|---|---|
| R-01 | `pickup_at IS NULL OR dropoff_at IS NULL` | reject | `missing_timestamp` | 0 | Sin tiempos no hay viaje. |
| R-02 | `dropoff_at < pickup_at` | reject | `negative_duration` | 56 (0,002%) | Contradice el orden temporal; no se sabe cuál de los dos es el erróneo, así que no se corrige. |
| R-03 | `duration_min > 1440` | reject | `duration_over_24h` | 16 | D-13. Taxímetro sin apagar. |
| R-04 | `date_trunc('month', pickup_at) <> mes del fichero` | reject | `pickup_outside_partition` | 18 | D-04. Mantiene la independencia de particiones. |
| R-05 | `trip_distance < 0` | reject | `negative_distance` | 0 | Una distancia negativa no tiene significado físico. |
| R-06 | `trip_distance > 200` | reject | `implausible_distance` | 31 | D-13. |
| R-07 | `fare_amount < 0 OR total_amount < 0` | reject | `negative_amount` | 37.448 (1,26%) | D-12. Anulaciones y disputas, no viajes cobrados. |
| R-08 | `fare_amount IS NULL OR total_amount IS NULL` | reject | `missing_amount` | 0 | Sin importe no hay viaje cobrado. |
| R-09 | `pu_location_id NOT BETWEEN 1 AND 265 OR do_location_id NOT BETWEEN 1 AND 265` (o NULL) | reject | `unknown_zone` | 0 | D-14. Fuera del catálogo oficial. |
| R-10 | `duration_min > 180` (y ≤ 1440) | warn | `long_duration` | 1.983 (0,07%) | D-13. Raro pero posible. |
| R-11 | `trip_distance = 0` | warn | `zero_distance` | 60.371 (2,04%) | D-13. El 94% tiene tarifa positiva: viajes reales con odómetro a cero o cancelaciones cobradas. |
| R-12 | `total_amount = 0` | warn | `zero_amount` | 416 | Viaje sin cobro; se conserva pero no debe entrar en promedios de tarifa. |
| R-13 | `pu_location_id IN (264, 265) OR do_location_id IN (264, 265)` | warn | `unresolved_zone` | 31.527 (1,06%) | D-14. Zona legítimamente desconocida. |
| R-14 | `passenger_count IS NULL OR passenger_count = 0` | warn | `passenger_count_unknown` | 171.627 (5,79%) | D-10. El conductor no lo registró; el viaje es válido. |
| R-15 | `passenger_count > 6` | warn | `passenger_count_high` | 60 | Un taxi amarillo lleva como mucho 5 o 6; valores mayores son error de tecleo, pero no invalidan el viaje. |
| R-16 | `ratecode_id NOT IN (1,2,3,4,5,6)` y no NULL | warn | `undocumented_ratecode` | 28.663 (0,97%, todo 99) | El diccionario TLC documenta 1 a 6; 99 aparece de forma sistemática y no está documentado. Se conserva el código. |
| R-17 | `payment_type NOT IN (1,2,3,4,5,6)` | warn | `undocumented_payment_type` | 140.162 (4,73%, todo 0) | D-10. Coincide exactamente con el bloque nulo. |
| R-18 | `vendor_id NOT IN (1,2,6,7)` | warn | `undocumented_vendor` | 0 (el 6 aparece en 260 filas y es válido) | Diccionario 2025: 1 CMT, 2 Curb, 6 Myle, 7 Helix. |
| R-19 | `store_and_fwd_flag NOT IN ('Y','N')` y no NULL | warn | `invalid_sf_flag` | 0 | Dominio de dos valores. |

Regla de implementación: cada R-xx es un objeto `{id, severity, reason_code, sql}` en una lista. El motor construye una única consulta que evalúa todas y produce `reasons` (lista de reason_codes de severidad reject) y `warnings` (lista de los de severidad warn). Curated recibe las filas con `reasons` vacía; quarantine las demás. Ambas conservan las dos columnas.

Unión de todas las reglas `reject` sobre 2024-01: 37.687 filas, 1,27%.

## B. Puerta de lote (después de evaluar R-xx, antes de publicar)

| Id | Condición | Severidad | reason_code | Por qué |
|---|---|---|---|---|
| B-01 | Filas con `reasons` no vacía > 5% del total | block | `reject_ratio_exceeded` | D-09. |
| B-02 | Filas exactamente duplicadas > 0,1% | warn | `exact_duplicates` | D-17. Métrica, no rechazo. |
| B-03 | Algún cast de T-02 falló | block | `cast_failure` | Complementa S-02 para casos que solo se ven con los valores. Diferida: con `CAST` directo el proceso aborta antes de llegar a batch; implementar si se migra a `TRY_CAST`. |
| B-04 | Corte 3: filas del mes difieren más del 50% respecto al mes anterior publicado | warn | `row_count_drift` | Detecta ficheros truncados o duplicados sin bloquear meses legítimamente atípicos (abril de 2020 existió). |

## Resumen de ejecución

Cada ejecución emite un JSON con: clave de partición, sha256, contrato, filas leídas, filas en curated, filas en quarantine, conteo por reason_code (reject y warn), resultado de S-xx y B-xx, y ruta publicada. Es la base de la observabilidad del corte 6 y de los tests de integración.
