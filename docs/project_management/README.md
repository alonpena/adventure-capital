# Uso del paquete de planificación

Leer primero `05_RESUMEN_EJECUTIVO.md`, luego el plan director. La auditoría respalda el alcance; el Excel administra el trabajo. Todos los documentos son propuesta de planificación, no contratos, nuevas funcionalidades ni adjudicación.

## Editar el Excel

1. En RESUMEN cambiar D3 por fecha contractual y completar feriados en J6:J25. El inicio 02-11-2026 es sólo ejemplo.
2. En EDT cambiar duración, avance, estado u horas de cada recurso (AD:AJ). Las fórmulas recalculan fechas, holguras, ruta crítica, Gantt y cargas. No sobrescribir celdas de cálculo ni ordenar físicamente filas; usar filtros.
3. RECURSOS muestra carga diaria además de semanal. Cambiar capacidad no vuelve a nivelar automáticamente: una alerta requiere decisión de reasignación o nueva nivelación.
4. Para modificar predecesoras, editar IDs en J y tipos en K, separados por comas en el mismo orden. T técnica, V validación, C contractual, R recurso. Guardar y ejecutar el importador y generador. Los enlaces R se reconstruyen a partir de conflictos reales. **El texto J/K no cambia fórmulas por sí solo.**
5. Nuevas tareas se agregan explícitamente a `plan_data.json` y requieren revisión del grafo/generador. El importador está acotado a las tareas existentes. No presentar el libro como un planificador universal sin mantenimiento.

La línea base contiene 47 tareas. Para gestión diaria, dividir la tarea activa en acciones de 0,5–2 días en el tracker que use el equipo; conservar ID, aceptación y total de horas. `evidence/weekly_plan.md` proporciona vencimientos y trabajo activo por actor. Las fases se solapan; no esperar al cierre de toda una fase para iniciar la siguiente.

## Reproducción

No se agregaron dependencias al producto. `plan.py`, `refresh_from_xlsx.py` y `verify_plan.py` usan biblioteca estándar. El constructor XLSX usa `@oai/artifact-tool` del runtime de artefactos; no modifica dependencias del repositorio. Se necesita tener ese paquete disponible para reconstruir el XLSX. En este entorno se resolvió mediante un enlace temporal `tools/node_modules` al runtime; no forma parte del paquete versionable.

```bash
# Recrear línea base (sobrescribe plan_data.json; no usar sobre cambios sin respaldo)
python3 docs/project_management/tools/plan.py

# Generar Excel; requiere @oai/artifact-tool resoluble por Node
node docs/project_management/tools/build_workbook.mjs

# Tras editar predecesoras/capacidad en el Excel: respaldar antes el archivo
python3 docs/project_management/tools/refresh_from_xlsx.py
node docs/project_management/tools/build_workbook.mjs

# Verificar línea base exportada y regenerar control semanal
python3 docs/project_management/tools/verify_plan.py
```

El importador conserva duración, esfuerzo, estado, avance, dependencias, tasas/capacidades, fecha inicial, feriados y controles numéricos del presupuesto/riesgos/hitos. No es una edición arbitraria de formato ni de todo el texto. El verificador final contiene controles de totales de **esta línea base**: si se cambia alcance/costo, revisar también esos controles y documentos, no eliminarlos para obtener un PASS.

La estimación O/P/C es deliberadamente exploratoria; no es distribución estadística. Calendario lógico y nivelación usan días de trabajo; feriados afectan fechas y cargas semanales, no el esfuerzo. La reserva de calendario no es holgura CPM de todas las tareas ni bolsa de funcionalidades nuevas.

## Evidencia y límites

- `pytest.xml`, `pytest.log`, `ruff.txt`: suite y lint del repositorio auditado.
- `probes.json`: validación negativa, diferencia de canales y sondas inocuas de render.
- `plan_validation.json`: CPM/nivelación y rutas críticas de la línea base.
- `final_validation.json`: verificación independiente del grafo/capacidad y OOXML exportado.
- `workbook_errors.ndjson`: búsqueda de errores de fórmulas; vistas PNG en `evidence/previews/` para revisión visual de las siete hojas.

El libro se recalculó con el motor de artefactos y se probaron cambios de duración, fecha, capacidad y tarifa. Se inspeccionó OOXML exportado. No se verificó recálculo en Microsoft Excel nativo ni se ejecutaron pruebas de navegador del SaaS. Al abrir por primera vez en Excel, confirmar cálculo automático y que RESUMEN muestre 2.193 horas y 55.510.500 CLP para esta línea base.

Los resultados de auditoría y las recomendaciones son independientes de documentación anterior. No se modificaron PLAN/CONTEXT/ADRs existentes: se proponen decisiones, no se implementa una arquitectura. PLAN.md está ausente en master y se registra como deuda documental.
