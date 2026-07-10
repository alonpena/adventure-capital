# FINAL DEMO SCRIPT — Defensa Adventure Capital (2–3 min)

## Preparación previa (antes de la defensa)

1. Ejecutar corrida gold si no existe (ver `FINAL_PLACEHOLDERS_TO_FILL.md`):
   ```bash
   uv run adventure-capital instances create --config configs/gold/gold-b2b-saas.yaml --name "gold-final"
   uv run adventure-capital executions run --instance <instance_id> --yes
   ```
2. Levantar UI antes de entrar a la sala:
   ```bash
   uv run streamlit run app.py
   ```
3. Tener abiertos en pestañas de respaldo (por si la UI falla):
   - `outputs/executions/run_20260706-045427_28a63258/report.html` en navegador.
   - Carpeta `outputs/executions/run_20260706-045427_28a63258/` en Finder.
4. Verificar que la ejecución gold aparece en la lista de ejecuciones de la UI.

## Demo path (7 pasos, espejo del Diagrama 4)

**Paso 1 — Seleccionar ejecución (15s).**
En la UI, seleccionar `configs/gold/gold-b2b-saas.yaml` / `outputs/executions/run_20260706-045427_28a63258`.
Decir: "Cada ejecución congela su configuración: este `config.yaml` es el contrato de supuestos del caso — servicios, ticket, churn, costos, inversión y tesis de crecimiento."

**Paso 2 — Informe ejecutivo (20s).**
Abrir la vista de informe ejecutivo / `report.html`.
Decir: "Esto no es una pantalla recalculando: es una vista generada desde artefactos. Si la UI desaparece, este HTML y sus fuentes siguen en disco."

**Paso 3 — Plan de crecimiento (25s).**
Mostrar tabla/curva desde `optimized_results.csv`.
Decir: "Este es el plan mensual canónico del solver: adquisición, clientes activos, ingresos, CAC, EBITDA y caja. El crecimiento cumple la tesis declarada — el optimizador no lo inventó."

**Paso 4 — Valoración (25s).**
Mostrar `valuation_summary.json` / vista DCF.
Decir: "El VAN se deriva del plan operacional y los supuestos financieros declarados: flujos descontados más valor de desecho. Nada se ingresa a mano."

**Paso 5 — Due diligence (25s).**
Abrir `due_diligence_report.md` / vista DD.
Decir: "Aquí está el veredicto: `passed_with_warnings`. Este archivo dice si el caso habilita análisis estocástico, qué exige recalibrar y con qué severidad. Es el gate metodológico."

**Paso 6 — Robustez (20s).**
Si M4 corrió: mostrar `stochastic_summary.csv` (percentiles VAN, P(VAN<0)).
Decir: "M4 es robustez técnica bajo escenarios: muestra la distribución del VAN, no reemplaza el plan oficial determinista."
Si DD bloqueó M4: mostrar el estado bloqueado.
Decir: "El bloqueo es diseño: no se interpreta riesgo estocástico sobre un caso que exige recalibración."

**Paso 7 — Artefactos (20s).**
Abrir la página de artefactos / carpeta de la ejecución.
Decir: "Todo lo mostrado es descargable: CSV, JSON, HTML, más `formula_trace.json` y `artifacts_manifest.json` para auditoría. Esta carpeta es la tesis en forma ejecutable."

## Plan B (sin UI)

Si Streamlit falla: mismo guion sobre archivos directamente.
1. `outputs/executions/run_20260706-045427_28a63258/config.yaml` (supuestos)
2. `report.html` (informe)
3. `optimized_results.csv` (plan)
4. `valuation_summary.json` (VAN)
5. `due_diligence_report.md` (veredicto)
6. `stochastic_summary.csv` si existe (robustez)
7. listado de la carpeta (artefactos)

## Reglas durante la demo

- No editar YAML en vivo (riesgo de corrida larga o infeasible en escenario no ensayado).
- No abrir ejecuciones no ensayadas.
- Si preguntan por recalcular en vivo: ofrecer el comando (`uv run adventure-capital executions run --instance ... --yes`) y explicar que una corrida toma tiempo de solver; no lanzarla salvo que el comité insista y el tiempo lo permita.
