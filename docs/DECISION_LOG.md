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
