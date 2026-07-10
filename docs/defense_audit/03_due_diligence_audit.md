# 03 Due Diligence Audit

## Qué Hace DD

Due Diligence es un workflow de evaluación iterativa: revisa inputs, ejecuta baseline determinista, usa calibración como evidencia, agrega reglas de escalabilidad/liquidez y produce un veredicto con recomendaciones. Fuente: `docs/DUE_DILIGENCE.md`, `src/adventure_capital/due_diligence/workflow.py`.

## Tabla De Reglas

| Regla | Significado negocio | Severidad | Consecuencia | Evidencia |
|---|---|---|---|---|
| DD01 | config válido | structural | bloquea M4 si falla | `rules.py` |
| DD02 | margen unitario positivo | structural | bloquea M4 | `rules.py` |
| DD03 | financiamiento inicial presente | structural/warning | bloquea salvo `operating_company` | `rules.py` |
| DD04 | churn en rango | structural | bloquea M4 | `rules.py` |
| DD05 | churn excesivo | warning/major | alerta o major adjustment | `rules.py` |
| DD06 | breakeven | warning/major | recalibrar costos/adquisición | `rules.py` |
| DD07 | runway/caja negativa | warning/minor | diagnóstico liquidez | `rules.py` |
| DD08 | funding gap | warning/minor | diagnóstico financiamiento | `rules.py` |
| DD09 | EBITDA positivo año 3 | major | bloquea M4 canónico | `rules.py` |
| DD10 | crecimiento ingresos | major | bloquea M4 canónico | `rules.py` |
| DD11 | brecha capital trabajo | minor | recomienda financiamiento/recalibrar | `workflow.py` |
| DD12 | exit ROI 3x | warning | alerta venture | `rules.py` |
| DD13-DD17 | growth commitment warnings/infeasible | warning | no bloquea; diagnóstico tesis | `rules.py`, ADR 0014 |
| DD18 | conservative plan diagnostic | ok/warning | experimental, no bloqueante | `growth_diagnostics.py` |

## Veredictos

| Veredicto | M4 | Lectura |
|---|---|---|
| `passed` | corre | valoración final |
| `passed_with_warnings` | corre | final con advertencias |
| `requires_minor_adjustment` | corre | preliminar/warning |
| `requires_major_adjustment` | bloqueado | recalibrar antes de M4 |
| `rejected_for_stochastic` | bloqueado | error estructural/input no modelable |

## Qué DD No Hace

- No es due diligence legal/tributaria.
- No reemplaza decisión de inversión.
- No prueba que la startup sea invertible.
- No arregla automáticamente el YAML.
- No convierte resultados benchmark en validación de mercado.

## Speaker Summary

“DD es una capa de interpretación auditable. No cambia el modelo para forzar resultados: clasifica hallazgos, explica qué recalibrar y decide si el análisis estocástico se puede leer como final, preliminar o bloqueado.”

