NYC Taxi Batch Pipeline — roadmap de construcción y aprendizaje

1. Tesis del proyecto

Este proyecto no es «descargar taxis y hacer gráficos». Su objeto es construir y poder defender un sistema batch local que procese archivos mensuales crecientes con garantías explícitas.

La pregunta técnica es:

¿Cómo ingerir, validar, versionar, transformar y reprocesar archivos públicos mensuales sin duplicar datos, ocultar fallos ni reconstruir todo el histórico?

La fuente será NYC TLC Trip Record Data, mediante sus archivos Parquet mensuales. No se usará la API de NYC Open Data. La descarga HTTP de archivos bulk no convierte el proyecto en un proyecto de APIs.

Señales que debe demostrar

Ingesta de archivos grandes mediante streaming y escritura temporal.

Particionado temporal y crecimiento mensual.

Estado persistente de ejecuciones.

Idempotencia medible.

Backfills y reprocesados selectivos.

Detección de revisiones de origen.

Evolución de esquema y contratos versionados.

Separación entre errores transitorios, permanentes y filas inválidas.

Publicación atómica de particiones.

Pruebas unitarias, de integración y end-to-end.

CI real, entorno reproducible y release versionada.

Operación documentada: logs, métricas, runbook y recuperación.

Decisiones defendibles con alternativas y límites.

2. Alcance cerrado

Incluido en la versión 1

Dataset: Yellow Taxi Trip Records.

Primer archivo: enero de 2024.

Primer año completo: 2024.

Evolución de esquema deliberada: incorporar 2025, cuando aparece cbd_congestion_fee.

Escala final mínima: enero de 2022 a diciembre de 2025, 48 particiones mensuales.

Lookup de zonas de taxi en CSV como dimensión de referencia.

Capas raw, curated y marts.

CLI reproducible para planificar, ingerir, validar, transformar, ejecutar backfills y reprocesar.

Ejecución local en WSL2.

Excluido del núcleo

Kafka o cualquier simulación de streaming.

Spark: DuckDB basta para esta escala y este patrón.

Airflow: primero debe existir un pipeline correcto y operable sin orquestador.

Kubernetes.

Cloud.

Dashboard complejo.

Modelos predictivos.

Mezclar yellow, green, FHV y HVFHV antes de cerrar Yellow Taxi.

Afirmar exactly-once: la garantía real será publicación idempotente por partición.

Airflow o almacenamiento cloud solo podrán entrar como extensión posterior, mediante ADR y con una necesidad concreta. No forman parte de la definición de terminado.

3. Fuente y riesgo real

La TLC publica archivos Parquet por mes y tipo de servicio. La publicación suele llevar aproximadamente dos meses de retraso. La propia TLC advierte que puede modificar esquemas y que no garantiza la exactitud de los registros enviados por proveedores.

Esto crea tres casos que el sistema debe distinguir:

Archivo todavía no publicado: no es un fallo del pipeline.

Archivo descargado corrupto o petición fallida: puede ser un fallo transitorio.

Mismo mes con contenido diferente: es una revisión de origen; no debe sobrescribirse en silencio.

La adición de cbd_congestion_fee desde 2025 servirá como caso real de evolución de contrato.

Fuentes oficiales:

TLC Trip Record Data

Yellow Taxi Data Dictionary

TLC Trip Records User Guide

Preparar un entorno WSL

VS Code con WSL

4. Arquitectura objetivo

flowchart TD
    A["TLC Parquet mensual"] --> B["Ingesta Python"]
    B --> C["Raw inmutable"]
    B --> D["SQLite: estado y manifiesto"]
    C --> E["Contrato y validación"]
    E --> F["Curated particionado"]
    E --> G["Cuarentena"]
    F --> H["DuckDB + dbt"]
    H --> I["Marts analíticos"]

Plano de control y plano de datos

Función

Tecnología

Razón

Descarga, validación y coordinación

Python 3.12

Hace visibles las garantías y permite probarlas.

Estado de ejecuciones

SQLite

Transacciones y restricciones sin operar un servidor local innecesario.

Archivos raw y curated

Parquet

Es el formato de origen y permite lectura columnar y particionada.

Procesado analítico

DuckDB

Procesa Parquet fuera de memoria con SQL, proyección y pushdown.

Modelos marts y tests de datos

dbt-duckdb

Separa transformación analítica de la lógica operacional.

CLI

Typer

Expone comandos y parámetros reproducibles.

Calidad de código

pytest, Ruff, mypy

Pruebas, lint/formato y tipos.

Dependencias

pyproject.toml + uv.lock

Instalación bloqueada y reconstruible.

Integración continua

GitHub Actions

Verifica el repo en una máquina limpia.

Layout de datos local

data/
├── raw/
│   └── yellow/year=2024/month=01/<sha256>.parquet
├── curated/
│   └── yellow/year=2024/month=01/part-000.parquet
├── quarantine/
│   └── yellow/year=2024/month=01/invalid-000.parquet
├── marts/
└── control/
    └── pipeline.sqlite

data/ no se versiona. Se versionan el código, contratos, migraciones, fixtures pequeños y documentación necesarios para reconstruirlo.

Estructura prevista del repositorio

nyc-taxi-batch/
├── .github/workflows/ci.yml
├── configs/
│   ├── base.toml
│   └── contracts/
├── dbt/
├── docs/
│   ├── adr/
│   ├── architecture.md
│   ├── data-contracts.md
│   ├── runbook.md
│   ├── benchmarks.md
│   └── interview-notes.md
├── migrations/
├── src/nyc_taxi_pipeline/
│   ├── cli.py
│   ├── config.py
│   ├── domain.py
│   ├── ingest/
│   ├── control/
│   ├── quality/
│   ├── transform/
│   └── observability/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── AGENTS.md
├── CHANGELOG.md
├── Makefile
├── README.md
├── pyproject.toml
└── uv.lock

No se crea toda esta estructura vacía el primer día. Cada directorio aparece cuando existe una responsabilidad real.

5. Invariantes del sistema

Estas propiedades son parte del producto. Deben tener pruebas.

Identidad lógica

Una partición se identifica por:

(dataset, service_type, year, month)

Una versión física del origen se identifica además por su sha256.

Idempotencia

Si la clave lógica y el hash ya terminaron correctamente, repetir la orden no descarga ni publica de nuevo.

Raw es inmutable y direccionado por contenido.

Curated se construye en una ruta temporal.

La nueva partición solo se hace visible después de validar la salida.

El manifiesto se marca como completado después de la publicación.

Una interrupción no puede dejar una partición parcial presentada como válida.

Un hash nuevo para el mismo mes se registra como revisión. Requiere una acción explícita para sustituir curated.

Los registros de TLC no proporcionan un identificador de viaje fiable. Por tanto, no se fingirá una deduplicación exacta por fila. La garantía se formula en el nivel que sí controlamos: archivo y partición.

Estados mínimos

DISCOVERED
DOWNLOADING
RAW_READY
VALIDATING
VALIDATED
CURATED
NOT_AVAILABLE
FAILED_TRANSIENT
FAILED_PERMANENT
SUPERSEDED

Cada transición debe estar permitida explícitamente. Un reintento no puede saltarse validaciones.

Errores

Tipo

Ejemplos

Acción

Transitorio

timeout, conexión, HTTP 429, HTTP 5xx

Reintento limitado con backoff y jitter.

No disponible

mes reciente aún no publicado

Registrar y terminar sin corromper el estado.

Permanente

configuración inválida, contrato incompatible, URL histórica inexistente

Fallar sin reintento ciego.

Calidad de fila

duración negativa, zona inválida, importe imposible

Cuarentena con razón; no DLQ.

Revisión de fuente

misma clave lógica, hash diferente

Conservar ambas versiones y exigir aceptación explícita.

6. Roadmap por fases

La unidad de trabajo es una tarea que pueda cerrarse en 45–120 minutos. Cada tarea termina con código o documento verificable, prueba, explicación propia y commit.

Fase 0 — Entorno y contrato de proyecto

Objetivo: impedir que el entorno o la pérdida del equipo vuelvan a destruir el proyecto.

Tareas:

Confirmar WSL2 con Ubuntu y Git.

Guardar el repositorio en el sistema de archivos Linux, por ejemplo ~/code/nyc-taxi-batch, no en /mnt/c.

Abrirlo desde VS Code usando la extensión WSL. No es obligatorio ejecutar code .: se puede usar la paleta WSL: Open Folder in WSL.

Crear el repositorio Git y el remoto antes de implementar el pipeline.

Escribir un README inicial: problema, alcance, no objetivos y criterios de terminado.

Añadir AGENTS.md y este roadmap.

Crear un tablero de issues con las tareas de la fase 1.

Puerta de salida: el repo puede clonarse en otra carpeta; contiene alcance, licencia, .gitignore, roadmap y primer tag v0.0.0 opcional. No contiene datos reales.

Lo que debes poder explicar: por qué el código vive dentro del filesystem de WSL y por qué el remoto existe desde el primer commit.

Fase 1 — Reconocimiento de datos antes de diseñar

Objetivo: basar el contrato en evidencia, no en el PDF únicamente.

Tareas:

Descargar manualmente Yellow Taxi 2024-01.

Inspeccionar metadatos Parquet: tamaño, filas, columnas, tipos, row groups y compresión.

Comparar 2024-01 con 2025-01.

Identificar campos ausentes, nulos y cambios de tipo.

Comprobar rangos básicos: fechas, distancia, importes, pasajeros y zonas.

Documentar qué significa cada columna utilizada y qué afirmaciones no permite la fuente.

Escribir docs/data-contracts.md v0 y el ADR sobre alcance Yellow Taxi.

Experimento obligatorio: demostrar la aparición de cbd_congestion_fee en 2025 y decidir cómo representa el contrato una columna que antes no existía.

Puerta de salida: informe reproducible de profiling y contrato propuesto. Todavía no hay downloader productivo.

Lo que debes poder explicar: diferencia entre esquema físico, contrato canónico y reglas de calidad.

Fase 2 — Corte vertical mínimo

Objetivo: recorrer un solo mes de extremo a extremo antes de añadir robustez.

Tareas:

Crear pyproject.toml, paquete src/ y entorno bloqueado.

Diseñar el primer comando CLI para un mes explícito.

Construir la URL a partir de service_type, año y mes.

Descargar a una ruta temporal.

Calcular SHA-256 y mover a raw.

Leer desde raw con DuckDB.

Seleccionar y normalizar el conjunto canónico de columnas.

Escribir una partición curated.

Ejecutar una consulta de comprobación.

Añadir una prueba unitaria y una prueba end-to-end con un fixture pequeño generado.

Activar CI con Ruff, mypy y pytest.

Restricción: el primer corte puede ser ingenuo, pero sus limitaciones se registran. No se añade retry, concurrencia ni backfill antes de verlo funcionar.

Puerta de salida: un comando procesa enero de 2024 desde cero en un clon limpio y CI queda verde.

Lo que debes poder explicar: recorrido de datos de cinco minutos y responsabilidades de cada módulo.

Fase 3 — Ingesta resistente

Objetivo: hacer correcta la frontera con una fuente remota imperfecta.

Tareas:

Descargar en streaming a *.part sin cargar el archivo en memoria.

Configurar timeouts separados de conexión y lectura.

Implementar retries solo para errores transitorios.

Añadir backoff exponencial, jitter y máximo de intentos.

Capturar tamaño, hash, URL, hora y cabeceras útiles del origen.

Verificar que el archivo se puede abrir como Parquet antes de publicarlo en raw.

Limpiar o recuperar descargas parciales.

Añadir logs estructurados con run_id, partición y etapa.

Probar timeout, 429, 500, 404, descarga truncada y éxito tras reintento mediante servidor HTTP local de prueba.

Puerta de salida: ninguna respuesta incompleta termina como raw válido; los errores se clasifican y las pruebas demuestran la política.

Lo que debes poder explicar: por qué retry no equivale a robustez si no distingue errores.

Fase 4 — Plano de control e idempotencia

Objetivo: conocer el estado exacto de cada partición y hacer seguros los reintentos.

Tareas:

Diseñar el esquema SQLite y escribir una migración.

Definir restricciones únicas para identidad lógica y versión física.

Modelar estados y transiciones permitidas.

Implementar los comandos plan y status.

Hacer que una segunda ejecución correcta sea un no-op verificable.

Publicar curated desde staging mediante sustitución atómica en el mismo filesystem.

Inyectar un fallo entre transformación y publicación.

Recuperar ejecuciones abandonadas sin marcar éxito falso.

Detectar un hash distinto para un mes ya conocido.

Implementar aceptación explícita de revisión y conservar trazabilidad.

Experimentos obligatorios:

Ejecutar el mismo mes dos veces y comparar hashes y tiempos.

Matar el proceso antes de publicar y volver a ejecutarlo.

Simular una revisión de origen con el mismo mes y bytes distintos.

Puerta de salida: las tres propiedades anteriores están probadas automáticamente o mediante script reproducible documentado.

Lo que debes poder explicar: por qué esto es idempotencia por partición y no exactly-once.

Fase 5 — Contrato, calidad y evolución de esquema

Objetivo: separar compatibilidad estructural de calidad semántica.

Tareas:

Versionar el contrato canónico.

Distinguir columnas obligatorias, opcionales y desconocidas.

Definir conversiones de tipos explícitas.

Añadir reglas de validez y severidad.

Enviar filas rechazadas a quarantine con reason_code y run_id.

Calcular métricas de entrada, válidas, rechazadas y salida.

Definir umbrales que adviertan y umbrales que bloqueen.

Incorporar cbd_congestion_fee sin romper 2024.

Probar columna nueva, columna ausente, tipo incompatible y nulos inesperados.

Documentar qué anomalías se conservan porque pueden ser datos reales.

Puerta de salida: 2024 y 2025 producen un esquema canónico compatible; una incompatibilidad real falla antes de publicar.

Lo que debes poder explicar: por qué filtrar todo valor extraño puede destruir información válida.

Fase 6 — Incremental, backfill y reprocesado

Objetivo: demostrar crecimiento sin coste lineal por ejecución ordinaria.

Tareas:

Aceptar intervalos --from y --to.

Crear un plan determinista de particiones antes de ejecutar.

Procesar primero 2024 completo.

Añadir 2025 y comprobar que 2024 no se reescribe.

Añadir --reprocess para particiones seleccionadas.

Añadir --accept-source-revision separado de --reprocess.

Limitar concurrencia de descargas y medir si aporta valor.

Garantizar que el fallo de un mes no borra los éxitos previos del backfill.

Emitir resumen final por partición y código de salida coherente.

Puerta de salida: un backfill de 24 meses puede reanudarse; añadir un mes solo modifica esa partición; el reprocesado tiene alcance explícito.

Lo que debes poder explicar: diferencia entre carga incremental, backfill, retry, replay y revisión de fuente.

Fase 7 — Modelo analítico con dbt

Objetivo: entregar datos utilizables sin mezclar lógica operacional y métricas de negocio.

Marts mínimos:

mart_daily_zone_demand: viajes, pasajeros, distancia y duración por día y zona de recogida.

mart_hourly_zone_revenue: viajes e importes por hora y zona.

mart_monthly_payment_quality: distribución de pagos, tips conocidos y tasas de registros rechazados.

Tareas:

Definir grains y claves antes de escribir SQL.

Incorporar la dimensión oficial de zonas.

Crear staging y marts en dbt.

Añadir tests de unicidad, no nulos, relaciones y valores aceptados donde sean válidos.

Documentar métricas ambiguas: total_amount no incluye tips en efectivo; tip_amount no representa todos los tips.

Generar documentación dbt.

Añadir dos consultas de ejemplo que respondan preguntas concretas.

Puerta de salida: cada mart tiene grain, consumidor, definición de métricas y tests.

Lo que debes poder explicar: por qué una métrica técnicamente calculable puede ser semánticamente inválida.

Fase 8 — Operación, observabilidad y recuperación

Objetivo: que otra persona pueda detectar y reparar fallos sin leer todo el código.

Tareas:

Estandarizar logs JSON y logs legibles en local.

Registrar duración, bytes, filas y estado por etapa.

Añadir un resumen de ejecución consultable desde CLI.

Escribir docs/runbook.md con síntomas, diagnóstico y reparación.

Crear comandos seguros de limpieza para temporales, nunca para raw válido.

Documentar recuperación de SQLite y reconstrucción desde raw.

Añadir una prueba de desastre: eliminar curated y reconstruirlo sin descargar raw.

Puerta de salida: una persona nueva puede diagnosticar cinco fallos preparados usando solo CLI, logs y runbook.

Lo que debes poder explicar: diferencia entre observabilidad y «tener logs».

Fase 9 — Escala, benchmark y cierre de portfolio

Objetivo: medir límites y convertir el trabajo en evidencia defendible.

Tareas:

Ejecutar 1, 12, 24 y 48 meses.

Medir tiempo, bytes de entrada/salida, filas, uso máximo de memoria y particiones tocadas.

Comparar primera ejecución, no-op y adición de un mes.

Identificar el cuello de botella con evidencia.

Registrar una optimización y también una optimización descartada.

Probar instalación desde cero con instrucciones del README.

Completar arquitectura, contratos, runbook, benchmarks y ADRs.

Preparar changelog y release v1.0.0.

Escribir explicación de 60 segundos, recorrido de 5 minutos y defensa de decisiones.

Redactar tres bullets de CV basados en métricas reales.

Puerta de salida: se cumplen todos los criterios de terminado y otra persona reproduce el proyecto desde el repo.

7. ADRs obligatorios

No se redactan retrospectivamente todos al final. Se crean cuando aparece la decisión.

Alcance inicial: Yellow Taxi y archivos bulk.

DuckDB en lugar de Spark.

SQLite como plano de control.

Identidad de partición y semántica de idempotencia.

Estrategia de publicación atómica.

Política de revisiones de fuente.

Contrato canónico y evolución 2024→2025.

Quarantine en batch frente a DLQ.

dbt limitado a transformación analítica.

Airflow fuera del núcleo.

Cada ADR contiene: contexto, decisión, alternativas reales, consecuencias, límites y condición que justificaría revisarlo.

8. Estrategia de pruebas

Nivel

Qué protege

Ejemplos

Unitarias

Reglas puras

rangos mensuales, rutas, hash, estados, clasificación de errores.

Integración

Fronteras reales locales

HTTP local, SQLite, escritura y lectura Parquet, publicación atómica.

Contrato

Compatibilidad de entrada

esquemas 2024/2025, columnas nuevas, tipos incompatibles.

End-to-end

Flujo completo pequeño

fixture generado → raw → curated → mart.

Datos/dbt

Semántica del modelo

grain, claves, relaciones y valores aceptados.

Recuperación

Garantías operativas

proceso interrumpido, partial file, reconstrucción desde raw.

Los tests no deben descargar decenas de megabytes ni depender de que TLC esté disponible. La fuente real se usa en smoke tests manuales documentados.

9. Flujo de trabajo Git

Crear una issue con problema, evidencia y criterio de aceptación.

Abrir rama corta: feat/, fix/, docs/ o test/.

Antes de código, escribir la hipótesis o decisión en la issue.

Implementar el cambio mínimo.

Ejecutar comprobaciones locales.

Actualizar documentación afectada.

Abrir PR aunque trabajes solo: fuerza a explicar el cambio.

Revisar diff y CI.

Fusionar y borrar rama.

Actualizar el roadmap solo si cambió evidencia o alcance.

Un PR no debe mezclar una refactorización general, una feature y documentación no relacionada.

10. Definición de terminado

El proyecto está terminado cuando:

Un clon limpio en WSL se instala mediante instrucciones verificadas.

CI ejecuta lint, tipos y tests sin depender de archivos locales ocultos.

Se procesan al menos 48 meses de Yellow Taxi.

Repetir una partición completada es un no-op demostrado.

Añadir un mes no reescribe el histórico.

Un fallo antes de publicar no deja una partición válida parcial.

Una revisión del origen se detecta y conserva trazabilidad.

2024 y 2025 conviven bajo un contrato canónico versionado.

Las filas inválidas quedan contadas y explicadas.

Curated puede reconstruirse desde raw.

Los marts tienen grain, tests y definiciones semánticas.

El runbook permite diagnosticar y recuperar fallos preparados.

Hay benchmarks reproducibles y límites reconocidos.

Los ADRs coinciden con el código real.

Existe release v1.0.0, changelog y presentación técnica.

11. Ritmo recomendado

Con 7–10 horas semanales:

Semana

Objetivo

1

Fases 0–1: entorno, repo y reconocimiento.

2

Fase 2: corte vertical y CI.

3

Fases 3–4: ingesta, estado e idempotencia.

4

Fase 5: contrato y calidad.

5

Fases 6–7: incremental y marts.

6

Fase 8: operación y recuperación.

7

Fase 9: escala, documentación y release.

No se avanza por calendario. Si una puerta de salida no se cumple, la fase sigue abierta.

12. Primera sesión con Codex

Pega o usa este encargo en la raíz del repositorio:

Estamos en la fase 0 de ROADMAP.md. Lee AGENTS.md y el roadmap completo. No implementes el pipeline. Revisa mi entorno y guíame para crear el repositorio, el README inicial y el backlog de la fase 1. Primero pídeme que formule con mis palabras el problema, el alcance y tres no objetivos. Después critica mi formulación. Propón una sola tarea cada vez, con criterio de aceptación y verificación. No escribas código de implementación salvo que te lo pida expresamente.

La primera sesión termina cuando el repo remoto existe, el README inicial refleja decisiones reales y las tareas de reconocimiento están definidas. No cuando hay un downloader.