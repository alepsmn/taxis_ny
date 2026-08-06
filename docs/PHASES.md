# NYC Taxi Batch Pipeline — síntesis de fases

Este documento es el mapa operativo estable del proyecto. `ROADMAP.md` conserva el detalle y es la fuente canónica cuando cambian el alcance, una fase o una garantía. El estado de ejecución no se registra aquí: debe vivir en `STATUS.md`.

## Secuencia de consulta

Al iniciar una sesión:

1. Leer `AGENTS.md`.
2. Leer `STATUS.md`.
3. Leer solo la fase activa en este documento o su documento específico.
4. Consultar `ROADMAP.md` únicamente ante contradicciones, cambios de fase o decisiones de alcance.

No se avanza por calendario. Cada fase termina cuando su puerta de salida queda demostrada.

## Principios transversales

- Dataset único inicial: NYC TLC Yellow Taxi mediante Parquet mensual bulk.
- Ejecución local en WSL2.
- Python coordina; SQLite mantiene el plano de control; DuckDB procesa Parquet; dbt construye marts.
- Raw es inmutable. Curated se publica desde staging después de validarse.
- La garantía es idempotencia por versión de archivo y partición publicada, no `exactly-once` ni deduplicación exacta por viaje.
- Una revisión del origen es contenido nuevo para el mismo mes. Se conserva y exige aceptación explícita.
- Kafka, Spark, Airflow, Kubernetes, cloud, ML y dashboards complejos quedan fuera del núcleo.
- Cada tarea debe caber en 45–120 minutos y cerrar con evidencia verificable y explicación propia.

## Fase 0 — Entorno y contrato del proyecto

**Objetivo:** asegurar que el proyecto sea recuperable y tenga alcance explícito antes de implementar.

**Entregas:** repositorio Git y remoto; `.gitignore`; README inicial; reglas para agentes; roadmap; backlog de la fase 1.

**Puerta de salida:** el repositorio puede clonarse en otra carpeta, conserva el alcance y no contiene datos reales.

## Fase 1 — Reconocimiento y contrato de datos

**Objetivo:** diseñar desde evidencia de los Parquet reales, no solo desde documentación externa.

**Entregas:** profiling reproducible de 2024-01 y 2025-01; contrato de datos v0; ADR del alcance Yellow Taxi.

**Puerta de salida:** están documentados el esquema físico, el contrato canónico, las reglas de calidad y la aparición de `cbd_congestion_fee` en 2025. Aún no existe downloader productivo.

## Fase 2 — Corte vertical mínimo

**Objetivo:** procesar un mes de extremo a extremo antes de añadir robustez.

**Entregas:** paquete instalable; CLI mensual; descarga temporal; hash y raw; transformación con DuckDB; curated; fixture pequeño; tests y CI.

**Puerta de salida:** un comando procesa enero de 2024 desde cero en un clon limpio y CI ejecuta Ruff, mypy y pytest correctamente.

## Fase 3 — Ingesta resistente

**Objetivo:** proteger la frontera con una fuente HTTP remota e imperfecta.

**Entregas:** descarga en streaming a `.part`; timeouts; retries limitados solo para errores transitorios; validación Parquet; recuperación de parciales; logs estructurados.

**Puerta de salida:** ninguna respuesta incompleta se publica como raw válido y las pruebas locales cubren timeout, 429, 500, 404, truncado y recuperación.

## Fase 4 — Plano de control e idempotencia

**Objetivo:** persistir el estado real de cada partición y hacer seguros retries, interrupciones y revisiones.

**Entregas:** esquema y migraciones SQLite; máquina de estados; comandos `plan` y `status`; no-op verificable; publicación atómica; recuperación; aceptación explícita de revisiones.

**Puerta de salida:** está demostrado que repetir el mismo contenido no repite trabajo, una interrupción no publica éxito falso y un hash nuevo conserva trazabilidad.

## Fase 5 — Contrato, calidad y evolución de esquema

**Objetivo:** separar compatibilidad estructural de validez semántica.

**Entregas:** contrato versionado; columnas obligatorias y opcionales; conversiones explícitas; reglas con severidad; cuarentena con `reason_code`; métricas y umbrales.

**Puerta de salida:** 2024 y 2025 producen un esquema canónico compatible; una incompatibilidad real impide publicar.

## Fase 6 — Incrementalidad, backfill y reprocesado

**Objetivo:** crecer por particiones sin rehacer el histórico en cada ejecución.

**Entregas:** intervalos temporales; plan determinista; backfill reanudable; `--reprocess`; aceptación de revisión separada; resumen y códigos de salida coherentes.

**Puerta de salida:** añadir un mes solo modifica su partición, un backfill conserva éxitos previos y todo reprocesado tiene alcance explícito.

## Fase 7 — Modelo analítico con dbt

**Objetivo:** producir marts utilizables sin mezclar transformación analítica y operación del pipeline.

**Entregas:** dimensión de zonas; staging; tres marts mínimos; grains y métricas documentados; tests dbt; consultas de ejemplo.

**Puerta de salida:** cada mart tiene consumidor, grain, definición semántica y pruebas de claves, relaciones y valores pertinentes.

## Fase 8 — Operación, observabilidad y recuperación

**Objetivo:** permitir que otra persona diagnostique y repare fallos sin estudiar todo el código.

**Entregas:** logs legibles y JSON; métricas por etapa; resumen consultable; runbook; limpieza segura de temporales; reconstrucción desde raw.

**Puerta de salida:** una persona nueva puede diagnosticar cinco fallos preparados usando solo CLI, logs y runbook; curated puede reconstruirse sin descargar raw.

## Fase 9 — Escala y cierre de portfolio

**Objetivo:** medir límites y convertir el sistema en evidencia técnica reproducible.

**Entregas:** benchmarks de 1, 12, 24 y 48 meses; análisis del cuello de botella; optimización medida; instalación limpia; documentación final; ADRs; release `v1.0.0`.

**Puerta de salida:** se cumplen los criterios globales de terminado, otra persona reproduce el proyecto y las afirmaciones del portfolio se apoyan en métricas reales.

## Dependencias críticas

- La fase 1 precede al contrato implementado: primero evidencia, después diseño.
- La fase 2 precede a retries, concurrencia y backfills: primero un corte completo y observable.
- La fase 4 precede a incrementalidad real: sin estado persistente no existe una garantía demostrable de no-op.
- La fase 5 precede a combinar 2024 y 2025 de forma defendible.
- La fase 6 precede a benchmarks de crecimiento: antes debe estar definido qué se reutiliza y qué se reprocesa.
- La fase 8 precede al cierre: un pipeline no está terminado si solo su autor puede recuperarlo.

## Criterio global de terminado

El proyecto termina cuando un clon limpio instala y ejecuta el pipeline; CI valida código y tests; se procesan 48 meses; idempotencia, atomicidad, revisiones y evolución de contrato están demostradas; raw permite reconstruir curated; los marts tienen semántica y tests; existe runbook, benchmarks, ADRs coherentes y release `v1.0.0`.
