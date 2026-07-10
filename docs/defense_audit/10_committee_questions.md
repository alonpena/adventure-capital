# 10 Committee Questions

| Pregunta | Respuesta corta |
|---|---|
| ¿Esto reemplaza al evaluador? | No. Estandariza cálculos, evidencia y alertas; la decisión queda bajo juicio experto. |
| ¿Por qué YAML? | Porque deja supuestos legibles, versionables y reproducibles. |
| ¿Por qué MILP? | El plan mezcla decisiones operacionales discretas/continuas y restricciones de capacidad/caja. |
| ¿Qué significa target-driven? | El plan debe cumplir una tesis explícita de crecimiento, por defecto triplicar stock entre mes 12 y 36. |
| ¿Por qué M4 no es plan oficial? | ADR 0015: en MVP M4 se usa como robustez; plan oficial es determinista. |
| ¿Qué pasa si DD bloquea M4? | Se reporta como diagnóstico de negocio: recalibrar antes de leer riesgo estocástico. |
| ¿Los múltiplos son de mercado? | No necesariamente; son referencias configurables si no hay comparables externos. |
| ¿Hay datos reales? | Hay YAMLs/benchmarks y outputs; gold final pendiente si no se define `{{GOLD_RUN_PATH}}`. |
| ¿Qué pruebas existen? | `uv run pytest -q`: 186 passed, 3 skipped en esta rama. |
| ¿Qué falla hoy? | Ruff falla por lint preexistente; no se corrigió por restricción docs-only. |

