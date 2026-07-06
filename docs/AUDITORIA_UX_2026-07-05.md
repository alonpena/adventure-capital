# Auditoría UX — Adventure Capital UI (Streamlit)

**Fecha:** 2026-07-05 · **Branch:** `ui-pro` · **Autor:** sesión Claude Code (revisión senior UI/UX)
**Alcance:** flujo completo gestor → ejecución → DD → M4 → informe; trazabilidad de inputs/outputs;
congruencia con ADRs 0007/0008. No cubre lógica de modelo (congelada).
**Método:** recorrido de flujo con ejecuciones reales (`run_20260624-042322_c54fa2f1`), heurísticas de
Nielsen (visibilidad de estado, correspondencia sistema-mundo real, reconocimiento sobre recuerdo),
lectura de artefactos en disco, contraste contra CONTEXT.md y ADRs.

---

## 1. Inventario de vistas (qué hay en cada una hoy)

| Vista | Propósito | Lee (artefactos) | Decisión que habilita | Veredicto UX |
|---|---|---|---|---|
| **Gestor de Instancias** | Landing. Crear instancia (config congelada), listar, ejecutar, borrar. Contiene además el gate DD→M4. | `outputs/instances/*/metadata.json`, `instance.yaml`; escribe vía `workflow_registry` | Definir el caso; disparar M1–M3; confirmar/abortar M4 | ⚠️ Sobrecargada: formulario de ~30 campos + lista + gate M4 en una sola página |
| **Informe Ejecutivo** | Documento oficial del caso (report.html en iframe) + descargas + generación de reporte estándar | `report.html`, `report_data.json`, `report.pdf` | Entregar/presentar al cliente | ✅ Correcta tras pase `ui-pro`; generación de reporte importa `standard_report` (permitido por ADR 0008 §7) |
| **Plan de Crecimiento** | Plan Consensuado (m1–12) vs Proyecciones (m13–36), gráfico combinado, desglose por canal | `optimized_results.csv`, `fixed_cashflow.csv`, `growth_plan_summary.json`, `postprocessed_results/accelerated_growth_plan/*` | Validar la trayectoria operativa | ✅ Contenido correcto; falta fuente visible por bloque |
| **Valoración** | DCF, múltiplos, unit economics, trazabilidad de fórmulas | `valuation_summary.json`, `dcf_annual_summary.csv`, `dcf_cashflow.csv`, `unit_economics.csv`, `multiples_valuation.csv`, `formula_trace.json` | Sostener el número de valorización | ✅ La única vista con trazabilidad real (formula_trace); el patrón debería exportarse a las demás |
| **Due Diligence** | Veredicto + hallazgos + palancas | `due_diligence_report.json`, `assessment_summary.json`, `postprocessed_results/due_diligence/*` | Decidir si correr M4 / recalibrar | ✅ Completa; badge de veredicto sin traducir (`passed_with_warnings`) |
| **Análisis de Escenarios** | Titular E[VAN]/P50 + banda de riesgo CVaR + histograma | `stochastic_diagnostics.json`, `stochastic_scenarios.csv`, `stochastic_summary.csv`, `assessment_summary.json` | Leer riesgo de la inversión | ✅ Correcta tras pase `ui-pro` |

**No existe** vista de: artefactos del caso (manifest), configuración congelada de la ejecución
(`config.yaml` del run), ni sensibilidad WACC×múltiplo (`sensitivity_wacc_multiple.csv` se genera y
nadie la muestra — solo aparece dentro del report.html estándar).

---

## 2. Flujo real vs. modelo mental

Pipeline real y sus artefactos (cadena de trazabilidad que **ya existe en disco**):

```
instancia (instance.yaml + metadata.json, config_hash)
  └─ ejecución (execution.json: instance_id, config_hash, stages)
       ├─ M1 determinista → optimized_results.csv, fixed_cashflow.csv, model_instance.json
       ├─ M2 valoración  → valuation_summary.json, dcf_*.csv, unit_economics.csv, formula_trace.json
       ├─ M3 due diligence → due_diligence_report.json, calibration_report.json
       ├─ M4 estocástico (gated) → stochastic_*.csv/json, saa_solution.json
       ├─ M5 reporte → report_data.json, report.html, report.pdf
       └─ postprocessed_results/ (derivado, ADR 0007, con postprocessed_manifest.json)
```

El modelo mental del usuario es ese pipeline. La UI lo insinúa (stepper M1→M5 en sidebar, `ui-pro`)
pero **la cadena instancia→ejecución→artefacto→informe no es navegable ni visible**: desde una
ejecución no se puede ver qué instancia la produjo ni qué YAML congelado la definió.

---

## 3. Hallazgos y propuestas

### P0-1 · Trazabilidad de inputs/outputs (el gap principal)

**Hallazgo.** La propuesta de valor declarada (CONTEXT.md: *"the UI demonstrates reproducibility and
traceability"*) no está en pantalla:

- Ningún KPI declara su artefacto fuente.
- `execution.json` ya guarda `instance_id` y `config_hash`, pero la UI no los muestra ni enlaza.
- El `instance.yaml` congelado (el **input** exacto) solo es visible desde el Gestor, no desde el run.
- No hay manifest de artefactos canónicos (solo `postprocessed_manifest.json`, parcial).
- El directorio real contiene 36 archivos planos con ruido: `due_diligence.txt` **y**
  `due_dilligence.txt` (duplicado con typo), `error_log.txt`, `dashboard.png` (legacy),
  `summary.json` vs `growth_plan_summary.json` (ambigüedad de nombres).

**Propuesta.**
1. **Página "Artefactos del caso"** (o expander al pie del Informe Ejecutivo): tabla
   etapa → archivo → descripción → tamaño → botón de descarga, generada leyendo el directorio y un
   diccionario estático de descripciones en la UI (no requiere tocar pipeline, respeta ADR 0007).
2. **Caption de fuente por bloque** en cada vista: `fuente: valuation_summary.json · M2`. Costo
   trivial (los readers ya saben qué archivo leyeron).
3. **Cabecera del caso** muestra `config_hash` y enlaza a la instancia congelada (view de
   `instance.yaml` en expander).
4. (Pipeline, post-demo, fuera de la UI): emitir `artifacts_manifest.json` canónico al cierre de cada
   etapa y limpiar los archivos legacy/typo. Requiere tocar `postprocess.py` — **no antes del lunes**.

### P0-2 · Jerarquía de parámetros en el formulario de instancia

**Hallazgo.** ~30 campos planos con vocabulario del modelo (`g_max_suavizado`, `c_min`, `alpha`,
`rem_v`, `ciclo_op` como CSV a mano). Todos con el mismo peso visual: el usuario no distingue
**perillas de negocio** (las que Alejandro movería: precio, churn, VC, beta, meta) de **supuestos
técnicos** (que casi nunca se tocan). Listas de 12 valores en campos de texto separados por coma =
error de tipeo silencioso.

**Propuesta.** Reorganizar en tres niveles de revelación progresiva:
1. **Caso** — nombre, horizonte, capital VC, tasa de descuento. Siempre visible.
2. **Negocio** — servicios (precio, frecuencia, churn, recompra), canales activos y sus rangos.
   Visible, con unidades y ayuda por campo (`beta: tasa anual, 0.35 = 35%`).
3. **Supuestos técnicos** — colapsados con defaults visibles (suavizado, costos operativos, solver,
   lag de productividad). Etiqueta de negocio primero, símbolo del modelo entre paréntesis.

Riesgo medio (los widgets del formulario tienen estado frágil — hubo fixes recientes de YAML reload).
**Recomendado post-demo.**

### P0-3 · Gestor sobrecargado y gate M4 descontextualizado

**Hallazgo.** El gate DD→M4 (`_render_m4_gate`) se renderiza **encima del Gestor**, no en el contexto
del run que lo produjo. Tras ejecutar M1–M3 el usuario ve el veredicto flotando sobre un formulario
de creación — mezcla dos tareas mentales distintas ("configurar un caso nuevo" vs "decidir sobre este
resultado").

**Propuesta.** Al terminar M1–M3 navegar directo a la página **Due Diligence** del run y mostrar el
gate ahí (banner con veredicto + botones Continuar M4 / Solo determinista). El Gestor queda solo para
crear/listar. Cambio de navegación acotado; testeable con AppTest. **Candidato a F0 si se aprueba.**

### P1-4 · Historial de ejecuciones plano

**Hallazgo.** Radio con 20 ejecuciones mezcladas; múltiples runs del mismo caso (`bench_beloop` ×3)
indistinguibles salvo por timestamp. No agrupa por instancia.

**Propuesta.** Agrupar por caso: selectbox de caso → runs de ese caso debajo. Mantiene el fix de
preservación de selección. Post-demo (riesgo de regresión en navegación la víspera).

### P1-5 · Vocabulario y copy

- `passed_with_warnings`, `Optimal`, `Ex Post Lhs` sin traducir en badges/KPIs → etiqueta en español
  con término técnico en tooltip/caption (ADR 0008 §9 ya lo pide para M4).
- Canal "salesforce" se lee como Salesforce™ → "Fuerza de ventas" en etiquetas (el YAML no cambia).
- Excel se descarga con hojas `Sheet_1..n` (valuation.xlsx) → nombres reales de tabla.
- Mensajes de error crudos (`traceback` en `st.code`) visibles para el cliente → mensaje de negocio +
  detalle en expander.
- Pase con skill `design:ux-copy` sobre etiquetas, empty states y CTAs al implementar la nueva identidad.

### P2 · Menores

- `dashboard.png`, `financial_report.md`, `stochastic.txt` legacy en el run: confunden el manifest.
- `saa_solution.json` y `sensitivity_wacc_multiple.csv` generados y nunca expuestos (la sensibilidad
  merece sección en Valoración, post-demo).
- `st.file_uploader` con texto superpuesto en dark theme (bug cosmético de CSS actual).
- Falta favicon/título de pestaña con nombre del caso.

---

## 4. Congruencia con ADRs (grill)

| ADR | Estado | Nota |
|---|---|---|
| 0007 postprocessed view | ✅ intacto | UI lee artefactos; nada recalcula. Las propuestas P0-1..P1-4 son solo presentación. |
| 0008 flujo de entrada ("Configuración → Run → Informe") | ⚠️ divergió | El flujo real es Instancias → Run → gate M4 → Informe. La divergencia es *mejor* que el ADR (registro de instancias congeladas), pero el ADR no se actualizó. Documentar en el propio 0008 o anexo. |
| 0008 §6 identidad visual ("match report.html: #0B1020, #F59E0B") | ⚠️ **en revisión** | El usuario pidió explícitamente evitar la estética "AI dashboard" oscura-con-ámbar. Si se elige una dirección clara (ver brief), corresponde **enmendar el ADR**, no violarlo en silencio: la paridad pasa a ser de *identidad* (tipografía, acento, tono) y no de paleta literal. El report.html podría re-tematizarse en F1 con el mismo sistema. |
| 0008 §3 tabs Bloomberg-moderate | ✅ compatible | La densidad propuesta se mantiene en cualquiera de las tres direcciones. |

Sin otras incongruencias: nada de lo pedido contradice invariantes (math core congelado, UI no
recalcula, artefactos como única fuente).

---

## 5. Plan por fases

| Fase | Cuándo | Contenido | Riesgo |
|---|---|---|---|
| **F0** | hoy (pre-demo, en `ui-pro`) | Identidad visual elegida; captions de fuente por bloque; cabecera con config_hash + instancia congelada; gate M4 movido a página DD (si se aprueba); fix uploader | Bajo — solo presentación, `entrega-tesis` queda de fallback |
| **F1** | semana post-defensa | Formulario en 3 niveles; agrupación de runs por caso; página Artefactos completa; sección sensibilidad; pase ux-copy completo; re-tematizar report.html; enmienda ADR 0008 | Medio |
| **F2** | futuro (tesis: trabajo futuro) | `artifacts_manifest.json` canónico emitido por pipeline; limpieza de artefactos legacy; narrativa cualitativa IA | Pipeline |

## 6. Preguntas abiertas (para decisión del dueño)

1. Dirección visual (A/B/C del brief) — define enmienda de ADR 0008 §6.
2. ¿Implementar F0 hoy o congelar `entrega-tesis` para la demo y todo post-demo?
3. Alcance de trazabilidad en F0: ¿página Artefactos + captions, o solo captions?
4. ¿El gate M4 se mueve a la página Due Diligence (P0-3) antes de la demo?
