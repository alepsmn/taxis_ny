# Bitácora de decisiones

Registro cronológico ligero de decisiones confirmadas, cambios de criterio y decisiones diferidas. No sustituye a los ADR ni documenta propuestas como si fueran historia.

## Convención

Cada entrada contiene:

- **Contexto:** problema o bifurcación que exigió decidir.
- **Decisión:** criterio adoptado realmente.
- **Fundamento confirmado:** razón expresada o evidencia disponible; no inferencias retrospectivas.
- **Consecuencia:** efecto inmediato sobre el trabajo.
- **Estado:** vigente, diferida, sustituida o promovida a ADR.
- **Evidencia:** archivo, commit, prueba o conversación donde quedó confirmada.
- **Promoción a ADR:** condición que justificaría un ADR formal.

## 2026-08-06 — D-001 — Proyecto formativo de Data Engineering

- **Contexto:** definición del propósito frente a un proyecto meramente analítico.
- **Decisión:** usar el análisis de viajes mensuales de Yellow Taxi como caso funcional para construir y comprender un pipeline batch con garantías verificables.
- **Fundamento confirmado:** el objetivo principal es practicar buenas prácticas y profundizar en Data Engineering, no acumular herramientas ni limitarse a producir análisis.
- **Consecuencia:** idempotencia, atomicidad, evolución de esquema, recuperación y reproducibilidad forman parte del producto.
- **Estado:** vigente.
- **Evidencia:** `README.md` y `docs/ROADMAP.md`.
- **Promoción a ADR:** no necesaria; define la tesis y el alcance del proyecto.

## 2026-08-06 — D-002 — Contexto operativo ligero

- **Contexto:** `docs/ROADMAP.md` es demasiado extenso para cargarlo al inicio de cada conversación.
- **Decisión:** mantener el roadmap como fuente detallada y usar `docs/PHASES.md` como mapa estable resumido, junto con `STATUS.md` para el estado mutable.
- **Fundamento confirmado:** reducir el contexto cargado sin perder fases, dependencias ni puertas de salida.
- **Consecuencia:** el roadmap solo se consulta ante cambios de fase, contradicciones o decisiones de alcance.
- **Estado:** vigente.
- **Evidencia:** `docs/PHASES.md`.
- **Promoción a ADR:** no necesaria; es una convención de trabajo.

## 2026-08-06 — D-003 — Separación entre documentación versionada y notas locales

- **Contexto:** la regla `.gitignore` excluía toda la carpeta `doc/`, incluido el contexto necesario para reconstruir el proyecto.
- **Decisión:** versionar `AGENTS.md`, `STATUS.md`, `docs/ROADMAP.md` y `docs/PHASES.md`; reservar `.local/` para conversaciones, borradores y notas privadas no reproducibles.
- **Fundamento confirmado:** la documentación necesaria para comprender, operar o continuar el proyecto debe sobrevivir a un clon limpio.
- **Consecuencia:** el contexto canónico queda en Git y los artefactos conversacionales quedan fuera.
- **Estado:** vigente.
- **Evidencia:** commit `72498e0` y `.gitignore`.
- **Promoción a ADR:** no necesaria salvo que cambie la política de publicación o privacidad del repositorio.

## 2026-08-06 — D-004 — Licencia diferida

- **Contexto:** la fase 0 contempla versionar una licencia, pero el autor todavía no quiere seleccionarla.
- **Decisión:** diferir la elección de licencia sin declarar cerrada la fase 0.
- **Fundamento confirmado:** decisión explícita del autor.
- **Consecuencia:** pueden continuar tareas independientes, pero la puerta de salida de la fase 0 permanece pendiente salvo cambio explícito del roadmap.
- **Estado:** diferida.
- **Evidencia:** `STATUS.md`.
- **Promoción a ADR:** no necesaria; registrar la licencia elegida cuando se resuelva.

## 2026-08-06 — D-005 — Responsabilidad de la memoria operativa

- **Contexto:** el autor necesita reconstruir la secuencia de trabajo sin depender de memoria conversacional ni releer ADRs extensos.
- **Decisión:** el agente mantiene `STATUS.md` y esta bitácora después de cambios comprobados o decisiones confirmadas.
- **Fundamento confirmado:** petición explícita del autor.
- **Consecuencia:** el agente prepara y verifica estas actualizaciones; el usuario conserva la responsabilidad de comprender y confirmar las decisiones y de versionar los cambios.
- **Estado:** vigente.
- **Evidencia:** `AGENTS.md` y `docs/DECISION_LOG.md`.
- **Promoción a ADR:** no necesaria; es una regla de colaboración.

## 2026-08-06 — D-006 — Enseñanza antes de autonomía

- **Contexto:** se pidió al autor definir un issue técnico con procedencia, reproducibilidad y criterios verificables antes de haber enseñado esos conceptos. La tarea dejó de ser comprensible y el autor perdió el hilo.
- **Decisión:** en la primera exposición, el agente explica el concepto y proporciona un ejemplo completo; en la segunda usa una plantilla guiada; la formulación autónoma solo se exige después de comprobar comprensión.
- **Fundamento confirmado:** el autor está aprendiendo Data Engineering durante el grado y pidió explícitamente recibir enseñanza inicial antes de diseñar artefactos nuevos.
- **Consecuencia:** el nivel de autonomía aumentará por evidencia de comprensión, no por asumir experiencia profesional. Ante confusión se reduce el alcance hasta el último concepto comprendido.
- **Estado:** vigente.
- **Evidencia:** `AGENTS.md` y conversación del 6 de agosto de 2026 durante la definición del backlog de la fase 1.
- **Promoción a ADR:** no necesaria; es una regla pedagógica y de colaboración.

## 2026-08-06 — D-007 — Gestión del entorno Python con uv

- **Contexto:** el sistema WSL ofrece Python 3.14.4, mientras que la arquitectura del proyecto establece Python 3.12; además, no existe todavía un manifiesto reproducible de dependencias.
- **Decisión:** usar `uv` para gestionar Python 3.12, el entorno virtual y el bloqueo de dependencias del proyecto.
- **Fundamento confirmado:** el autor confirmó la decisión después de distinguir las responsabilidades de `pyproject.toml`, `uv.lock` y `.venv/`.
- **Consecuencia:** se crearán `.python-version`, `pyproject.toml` y `uv.lock` versionados; `.venv/` será local y reconstruible. DuckDB se declarará como dependencia directa antes de inspeccionar los metadatos Parquet.
- **Estado:** vigente.
- **Evidencia:** confirmación del autor en la conversación del 6 de agosto de 2026 y `STATUS.md`.
- **Promoción a ADR:** si `uv` condiciona el despliegue o debe compararse con otro gestor por una limitación observada.

## 2026-08-12 — D-008 — Ejecución de Git dentro de WSL2

- **Contexto:** Git ejecutado desde PowerShell sobre la ruta UNC de WSL2 rechazó el repositorio por `dubious ownership`, aunque Git dentro de Ubuntu accede correctamente al mismo árbol.
- **Decisión:** ejecutar los comandos del repositorio dentro de Ubuntu y usar la ruta Linux `/home/alex/taxis_ny`; no añadir una excepción global de `safe.directory` para la ruta UNC.
- **Fundamento confirmado:** el fallo se reprodujo desde PowerShell y las mismas comprobaciones funcionaron mediante ejecución directa con `wsl.exe -d Ubuntu -- git -C /home/alex/taxis_ny`; además, se observó que PowerShell puede evaluar expresiones Bash incluidas en cadenas dobles antes de entregarlas a WSL.
- **Consecuencia:** las sesiones posteriores deben entrar en WSL2 antes de ejecutar Git, evitando repetir el diagnóstico o alterar la configuración global.
- **Estado:** vigente.
- **Evidencia:** `AGENTS.md` y comprobación del 12 de agosto de 2026.
- **Promoción a ADR:** no necesaria; es una convención operativa local, no una decisión arquitectónica del pipeline.

## 2026-08-12 — D-009 — La licencia deja de bloquear la fase 0

- **Contexto:** la licencia seguía diferida y bloqueaba formalmente la fase 0, aunque no condiciona las tareas técnicas inmediatas ni existe todavía una necesidad de autorizar reutilización por terceros.
- **Decisión:** mantener la licencia diferida, pero retirarla de la puerta de salida de la fase 0; se reconsiderará cuando exista una necesidad concreta de reutilización, modificación o redistribución.
- **Fundamento confirmado:** decisión explícita del autor de no elegir una licencia todavía porque no afecta al trabajo técnico actual.
- **Consecuencia:** crear el backlog de la fase 1 queda como único pendiente para cerrar la fase 0. Mientras no exista licencia, se mantienen los derechos de autor por defecto y el repositorio no concede permisos generales de reutilización.
- **Estado:** vigente; sustituye la consecuencia de bloqueo de D-004, no la decisión de diferir la licencia.
- **Evidencia:** `STATUS.md` y conversación del 12 de agosto de 2026.
- **Promoción a ADR:** no necesaria; reconsiderar la decisión cuando la licencia pase a afectar distribución, colaboración o reutilización.

## 2026-08-12 — D-010 — Mantenimiento del backlog por el agente

- **Contexto:** trasladar al autor la redacción mecánica de cada entrada del backlog bloqueaba el avance y contradecía la responsabilidad del agente sobre la memoria operativa.
- **Decisión:** el agente mantiene el backlog versionado de la fase activa; el autor comprende y valida el contenido y conserva la responsabilidad sobre las decisiones técnicas.
- **Fundamento confirmado:** petición explícita del autor y coherencia con el modo GUIAR, que exige aprendizaje sin convertir al autor en mantenedor manual de los registros operativos.
- **Consecuencia:** `docs/BACKLOG.md` contiene tareas ordenadas, dependencias, propiedades y criterios observables; `STATUS.md` conserva únicamente la tarea activa y el siguiente paso.
- **Estado:** vigente.
- **Evidencia:** `AGENTS.md`, `docs/BACKLOG.md` y conversación del 12 de agosto de 2026.
- **Promoción a ADR:** no necesaria; es una regla de colaboración.

## 2026-08-12 — D-011 — Inicio de la fase 1

- **Contexto:** la recuperación desde clon limpio quedó verificada, la licencia dejó de bloquear la fase 0 y el backlog de la fase 1 quedó definido.
- **Decisión:** cerrar la fase 0 e iniciar la fase 1 por F1-01, definición del perfil mínimo reproducible.
- **Fundamento confirmado:** existen evidencia de clon limpio, entorno reconstruible y un backlog que cubre perfiles de ambos meses, comparación, contrato v0, reglas de calidad, ADR y verificación final.
- **Consecuencia:** el trabajo activo pasa a reconocimiento y contrato; todavía no se implementa el downloader ni el pipeline productivo.
- **Estado:** vigente.
- **Evidencia:** `STATUS.md`, `docs/BACKLOG.md` y commits `239d48d` y `622a009`.
- **Promoción a ADR:** no necesaria; es una transición de fase, no una decisión arquitectónica.

## 2026-08-15 — D-012 — Contrato de salida del perfil reproducible

- **Contexto:** F1-02 necesita conservar resultados comparables sin confundir perfiles de revisiones distintas ni mezclar diagnósticos con datos válidos.
- **Decisión:** el perfilador recibe un SHA-256 esperado independiente de la entrada, valida la identidad antes de perfilar y emite JSON determinista por `stdout`; los errores se escriben en `stderr` y terminan con código distinto de cero. Se excluyen campos variables y las frecuencias se ordenan por valor con una posición explícita para `NULL`.
- **Fundamento confirmado:** el autor distinguió ruta, nombre e identidad por contenido; comprobó que un hash calculado desde la propia entrada sería una comparación tautológica y verificó los casos de éxito, formato inválido y contenido distinto.
- **Consecuencia:** dos ejecuciones sobre los mismos bytes producen resultados comparables; un archivo distinto con el mismo nombre no genera un perfil exitoso.
- **Estado:** vigente.
- **Evidencia:** `scripts/profile_parquet.py`, `docs/profiling.md` y verificaciones locales del 14 y 15 de agosto de 2026.
- **Promoción a ADR:** si el formato del perfil pasa a ser una interfaz consumida por otros componentes o requiere compatibilidad entre versiones.
