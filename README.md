## Alcance del proyecto

Pipeline de datos para viajes mensuales de Yellow Taxi (NYC TLC). Procesará archivos Parquet mediante ingesta, validación, versionado del contenido de origen y contratos de datos, transformación y reprocesamiento.

## Cobertura temporal

48 particiones mensuales, 2022-01 a 2025-12, progresión incremental desde 2024-01.

## Capas de datos

- **raw**: evidencia inmutable del origen, identificada por hash.
- **curated**: datos validados y transformados.
- **quarantine**: filas con errores semánticos explicables.
- **marts**: agregados listos para consumo.

## Garantías previstas del sistema

- **Idempotencia**: repetir una partición con la misma clave y hash completados produce un no-op. `--reprocess` fuerza ejecución.
- **Publicación atómica**: cada partición mensual de `curated` se construirá en staging y solo sustituirá a la versión anterior tras validarse completamente; un fallo previo no hará visible una partición parcial.
- **Evolución de esquema**: cambios compatibles se normalizan; una incompatibilidad real bloquea la publicación.
- **Recuperación**: un fallo a mitad de proceso dejará la partición marcada como incompleta en un registro de estado (no en `curated`); un rerun retomará desde el último paso confirmado sin duplicar escritura, verificable consultando ese registro.

## Exclusiones deliberadas

No se usan Kafka, Spark ni Airflow. El volumen (48 particiones, batch mensual) no exige procesamiento distribuido ni streaming; su inclusión sería sobre-ingeniería no sustentada por los requisitos. Airflow queda como extensión futura, condicionada a un ADR que documente evidencia de necesidad.