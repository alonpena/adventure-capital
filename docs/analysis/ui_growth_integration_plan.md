# Plan de integración UI + growth core

Fecha: 2026-07-06

## Objetivo

Hacer una demo integrada y trazable con:

1. Growth core target-driven (`investment_thesis` + `growth_commitment` + `acquisition_envelope source=vc_minimum`, `delta=0`).
2. Benchmark/calibración de instancias reales v1.
3. UI Streamlit capaz de ejecutar, navegar y presentar artefactos mínimos correctamente.
4. `report.html` existente como documento oficial, sin reabrir narrativa Jinja avanzada.

Prioridad: corrección, trazabilidad y estabilidad para presentación. Estética y narrativa avanzada quedan post-demo.

## Estado actual

### Growth core

Cerrado técnicamente:

- `acquisition_ceiling.enabled=false` en perfil demo.
- `acquisition_envelope.enabled=true`.
- `source=vc_minimum`.
- `slack_year2=0`, `slack_year3=0`.
- `investment_thesis.multiple=3.0`, `base_month=12`, `horizon_months=36`.
- `growth_commitment.multiple_3y` queda como alias legacy.
- `DD18` queda como diagnóstico advisory; `Conservative` no bloquea.
- Suite: `186 passed, 3 skipped`.

### M4 stochastic MVP decision

Decision recorded in `docs/adr/0015-m4-mvp-robustness-diagnostic.md`:

- deterministic target-driven outputs are the official growth plan and valuation;
- `report.html` must show deterministic plan first and an ex-post robustness section second;
- robustness section must include the VAN distribution across scenarios: E[VAN], percentiles/CVaR, P(VAN<0), funding gap, and growth-target hit probability when available;
- SAA optimization output (`saa_solution.json`) is a separate technical artifact, not the business-facing official plan;
- UI wording must say `Análisis de robustez` / `simulación LHS` and avoid implying the SAA strategy replaces the deterministic plan;
- existing M4 code stays in place for demo; no last-minute refactor to risk-neutral E[VAN] or ex-post-only mode.

### Benchmark instancias v1

Harness agregado:

```bash
uv run python scripts/benchmark_instances_v1.py \
  --input-dir /Users/apena/Desktop/instances_yaml_v1 \
  --output outputs/benchmark_instances_v1
```

Outputs:

- `outputs/benchmark_instances_v1/benchmark_instances_v1.csv`
- `outputs/benchmark_instances_v1/benchmark_instances_v1.md`

Hallazgos principales:

| Caso | Lectura |
|---|---|
| GoDemos | Mejor candidato de validación baseline. Año 1 cerca de Excel. |
| Entrena en Casa | Probable falta de base instalada (`initial_clients`) y ajuste ticket/costos. |
| Beloop | Año 1 útil; VAN diverge por setup/consultoría/downgrades no modelados. |
| KavaComex | Stress case; logística, ABC y freelance no están estructuralmente representados. |

Regla de calibración:

1. No calibrar VAN directo.
2. Calibrar revenue año 1 vía `ticket`/ARPU.
3. Calibrar EBITDA año 1 vía `c_u`, `c_min`, `g_adm`, `RRHH`.
4. Comparar VAN como consecuencia.
5. Unit economics altos se tratan como alerta de consistencia, no KPI final.

## Decisión UI

No hacer `git merge ui-pro` completo.

Razón: `ui-pro` mezcla capa visual con cambios destructivos o incompatibles:

- Borra docs/analysis y ADRs relevantes.
- Borra tests growth.
- Borra scripts de diagnóstico.
- Toca core (`config.py`, DD, stochastic, model, instance).
- Puede revertir decisiones recientes de growth core.

Sí hacer integración selectiva de capa UI.

## Cherry-pick/copy permitido desde `ui-pro`

Fuente:

```text
/Users/apena/gits/adventure-capital/.claude/worktrees/fervent-mahavira-606bfa
```

Archivos permitidos:

```text
.streamlit/config.toml
app.py
streamlit_pages/artifacts_page.py
streamlit_pages/components.py
streamlit_pages/due_diligence_page.py
streamlit_pages/executive_report_page.py
streamlit_pages/growth_plan_page.py
streamlit_pages/instance_manager_page.py
streamlit_pages/stochastic_page.py
streamlit_pages/styles.py
streamlit_pages/valuation_page.py
```

Docs opcionales:

```text
docs/AUDITORIA_UX_2026-07-05.md
```

ADR opcional solo si se revisa manualmente:

```text
docs/adr/0008-ui-architecture-consulting-tool.md
```

## No cherry-pick

No traer desde `ui-pro`:

```text
src/adventure_capital/*
tests/*
scripts/*
docs/analysis deletions
docs/adr/0014 deletions
benchmark_v0/*
CONTEXT.md
legacy/vim-xd.txt
```

Especialmente prohibido:

- Cambiar growth core.
- Cambiar defaults de `acquisition_envelope`.
- Borrar legacy bajo presión.
- Tocar `entrega-tesis`.
- Rebaseline golden outputs.

## Alcance UI F0 para demo

Implementar solo:

1. Nueva página `Artefactos`.
   - lista artefactos por etapa.
   - muestra `config.yaml` congelado.
   - botones descarga.
2. Header de caso.
   - instance name.
   - run id.
   - `config_hash`.
3. Captions de fuente.
   - ejemplo: `Fuente: valuation_summary.json · M2 — Valoración`.
4. Gate M4 en Due Diligence.
   - no en gestor.
   - si DD bloquea, mostrar razones.
   - si DD advierte, pedir confirmación.
   - label business-facing: `Análisis de robustez (LHS)`, not `plan estocástico oficial`.
   - caption required: `Simulación de incertidumbre sobre el plan determinista; no reemplaza el plan oficial del MVP.`
5. Informe ejecutivo.
   - iframe/`st.iframe` de `report.html`.
   - descarga HTML/PDF si existen.
   - generar reporte estándar queda en expander; no hacerlo obligatorio.
6. Styling mínimo estable.
   - identidad Memorando aceptable.
   - evitar rehacer Jinja/report template ahora.

## Fuera de alcance pre-demo

- Re-tematizar `report.html.j2`.
- Jinja narrative parametrizada avanzada.
- Formulario en 3 niveles.
- Agrupar historial por instancia.
- `artifacts_manifest.json` canónico emitido por pipeline.
- `initial_clients` como cohorte t=0.
- Remodelar KavaComex logística/ABC/freelance.
- Unit economics estructural por segmento.

## Plan de implementación

### Paso 0 — Commit base growth

Antes de integrar UI, commitear estado actual growth + benchmark:

```bash
git status --short
uv run pytest -q
uv run ruff check scripts/benchmark_instances_v1.py
git diff --check
git add configs/demo-growth-core.yaml scripts/benchmark_instances_v1.py src/adventure_capital/growth_diagnostics.py \
  src/adventure_capital/config.py src/adventure_capital/instance.py src/adventure_capital/reporting.py \
  src/adventure_capital/due_diligence/rules.py src/adventure_capital/due_diligence/workflow.py \
  scripts/growth_commitment_benchmarks.py tests/test_acquisition_envelope.py tests/test_growth_commitment.py \
  docs/DUE_DILIGENCE.md docs/adr/0014-growth-commitment-hiring-friction.md \
  docs/analysis/final_growth_decision.md docs/analysis/growth_commitment_benchmarks.md \
  docs/analysis/ui_growth_integration_plan.md
git commit -m "feat: target-driven growth core and benchmark harness"
```

### Paso 1 — Crear rama integración

```bash
git switch -c demo-integrated-growth-ui
```

### Paso 2 — Copia selectiva UI

Copiar solo archivos permitidos:

```bash
cp /Users/apena/gits/adventure-capital/.claude/worktrees/fervent-mahavira-606bfa/.streamlit/config.toml .streamlit/config.toml
cp /Users/apena/gits/adventure-capital/.claude/worktrees/fervent-mahavira-606bfa/app.py app.py
cp /Users/apena/gits/adventure-capital/.claude/worktrees/fervent-mahavira-606bfa/streamlit_pages/*.py streamlit_pages/
cp /Users/apena/gits/adventure-capital/.claude/worktrees/fervent-mahavira-606bfa/docs/AUDITORIA_UX_2026-07-05.md docs/AUDITORIA_UX_2026-07-05.md
```

No usar merge automático.

### Paso 3 — Validar imports y estilo

```bash
uv run python -m py_compile app.py streamlit_pages/*.py
uv run ruff check app.py streamlit_pages
uv run pytest -q
git diff --check
```

### Paso 4 — Smoke artifacts

```bash
uv run adventure-capital run \
  --config configs/demo-growth-core.yaml \
  --output outputs/demo-growth-core-ui-smoke
```

Verificar existencia:

```text
outputs/demo-growth-core-ui-smoke/report.html
outputs/demo-growth-core-ui-smoke/optimized_results.csv
outputs/demo-growth-core-ui-smoke/valuation_summary.json
outputs/demo-growth-core-ui-smoke/unit_economics.csv
outputs/demo-growth-core-ui-smoke/due_diligence_report.json
outputs/demo-growth-core-ui-smoke/growth_suggestions.json
```

### Paso 5 — Smoke UI manual

```bash
uv run streamlit run app.py
```

Checklist manual:

- Gestor carga.
- Se puede cargar YAML.
- Se puede crear instancia.
- Se puede ejecutar M1-M3.
- Due Diligence muestra gate M4.
- Informe ejecutivo muestra `report.html`.
- Plan de crecimiento muestra tablas/gráficos.
- Valoración muestra DCF/unit economics.
- Artefactos muestra `config.yaml`, CSV, JSON y descargas.

### Paso 6 — Commit integración UI

```bash
git add .streamlit app.py streamlit_pages docs/AUDITORIA_UX_2026-07-05.md
git commit -m "feat(ui): integrate traceable demo views over growth artifacts"
```

## Fallback

Si UI integration falla:

1. No mergear.
2. Usar branch growth core por CLI.
3. Presentar `report.html` abierto en navegador + benchmark markdown + CSV.
4. `entrega-tesis` sigue fallback final.

## Narrativa para presentación

- Modelo reemplaza prorrateo manual por optimización auditable.
- Tesis de inversión fija crecimiento objetivo (`×3` default).
- Modelo optimiza ejecución/costos para alcanzar la tesis.
- VAN y MoM son consecuencias.
- Benchmark v1 separa calibración año 1 de valorización.
- M4 es análisis oficial de robustez dentro del `report.html`: distribución de VAN (E[VAN], percentiles/CVaR, probabilidad de VAN negativo) y brecha de caja bajo escenarios LHS; no reemplaza el plan determinista oficial del MVP. La optimización SAA queda como artefacto técnico separado.
- UI demuestra trazabilidad: YAML congelado → ejecución → artefactos → reporte.

## Trabajo futuro documentado

1. `initial_clients` como cohorte t=0.
2. Unit economics por segmento y no solo blended.
3. KavaComex: logística por botella/caja/contenedor + freelance sobre margen.
4. Beloop: setup one-shot, consultoría, downgrades y células DaaS.
5. `artifacts_manifest.json` canónico del pipeline.
6. Jinja narrative parametrizada enriquecida en `report.html`.
7. `investment_thesis.multiple` como variable de sensibilidad/escenario (downside/base/upside), no como variable del solver en el MVP.
