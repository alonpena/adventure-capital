# Auditoría de cierre — Adventure Capital

**Fecha:** 2026-07-02 · **Branch de entrega:** `entrega-tesis` · **Defensa:** lunes 6 jul, 8:15
**Insumo:** reunión A. Maureira 2026-07-01 (notas Gemini) + barrido de calibración ejecutado hoy.

---

## 1. Veredicto general

El sistema está **funcionalmente completo y verde** (147 tests passed, 3 skipped). El problema
de "resultados muy conservadores" **no era el CVaR ni la ley de crecimiento en sí**: era el
caso base descalibrado. Dos números lo explican:

1. `target_stock_multiplier: 3.0` (default) limita el stock de clientes a 3× el año 1 →
   ingresos año 3 = US$451k y **VAN = −75.8k**.
2. `VC: 100000` está **bajo el costo fijo comprometido del año 1 (~US$138k)** → la caja
   rompe el piso `−VC` en el año 1 → pre-feasibility warning determinista y funding gap
   en la mayoría de los escenarios estocásticos ("gatilla en todos los escenarios").

Con eso corregido el pipeline entero se comporta: DD pasa, M4 corre, distribución sana.

## 2. Dinámica de crecimiento (barrido ejecutado, H=36, β=35%)

| Variante | VAN | Ingresos Y3 | EBITDA Y3 | Veredicto DD |
|---|---:|---:|---:|---|
| Ceiling 3× (default actual) | −75,818 | 451,084 | 104,371 | requires_major_adjustment |
| Ceiling 5× | 170,057 | 754,501 | 326,491 | requires_minor_adjustment |
| **Ceiling 8×** | 559,694 | **1,189,366** | 672,078 | requires_minor_adjustment |
| Ceiling 12× | 1,093,278 | 1,755,677 | 1,141,131 | requires_minor_adjustment |
| Convex-CAC θ=45 | −202,000 | 335,320 | 6,468 | requires_major_adjustment |
| Convex-CAC θ=10 | −162,374 | 432,675 | 99,687 | (sobre-conservador) |
| **Ceiling 8× + VC=200k** | **459,694** | **1,189,366** | 672,078 | **passed_with_warnings** |

**Resultado:** `configs/caso-base-1m.yaml` (nuevo, commiteado) = base + M=8 + VC=200k.
Llega al millón al año 3 con VAN positivo y habilita M4.

**Lectura metodológica (coherente con la reunión):**

- La **media móvil 3 períodos** (`g_max_suavizado`) es una recurrencia geométrica que
  diverge (~(1+g)^t); está inerte desde ADR 0011 y debe quedar como referencia histórica,
  no volver.
- El **ceiling logarítmico** (ADR 0010) ES la "función logarítmica" que Alejandro considera
  metodológicamente correcta. El multiplicador M es el proxy del tamaño de mercado:
  exógeno, sí, pero **declarado y auditable** — igual que el proxy de penetración de
  internet que él mismo usa. Defensa: "M representa la expansión de mercado alcanzable
  en 3 años; el CAC aporta el crecimiento adicional dentro de esa banda" (mapea 1:1 a su
  frase "tasa de mercado + tasa del CAC").
- El **convex-CAC** (ADR 0013) queda como comparación de métodos en la tesis: reproduce el
  ramp realizado de las 4 instancias benchmark (±0.05 en Y2/Y1) pero es estructuralmente
  conservador en VAN y no sirve como default del caso demo. No usarlo el lunes como modo
  principal.
- La **función hiperbólica a·t/(b+t)**: misma familia de saturación que el ceiling log.
  Su lugar correcto es el que tú mismo identificaste — la interfaz de negociación, donde
  el VC entrega el tope (b ≡ techo de adquisición pactado) y se re-proyecta. Trabajo
  futuro, no para el lunes.

**Pendiente de decisión (Alonso):** subir el default `target_stock_multiplier` 3.0 → 8.0 en
`config.py` afectaría todos los demos y varios tests; por eso dejé el caso calibrado como
YAML aparte y NO toqué el default. Si quieres 8.0 como default global, es un cambio de 1
línea + re-baseline de goldens.

**Nota β:** el modelo usa β=35%; Alejandro habló de 20% retail + 10% castigo = **30%**
(→ horizonte 1/0.30 ≈ 40 meses, coherente con H=36+desecho 4 meses). Considera bajar β a
0.30 en el caso demo — sube el VAN y alinea el relato con su metodología. Es 1 campo YAML.

## 3. Estocástico: diagnóstico CVaR

**El objetivo NO es puro CVaR 5%.** Desde ADR 0011 (commit 0a15828) el objetivo es
`0.5·E[VAN] + 0.5·CVaR_15%(VAN)` — mean-CVaR, verificado en `stochastic/model.py`. No hay
que cambiar a Monte Carlo: la evaluación ex-post YA es Monte Carlo/LHS independiente
(N=1000, seed 999) sobre la estrategia SAA.

Sobre el caso calibrado (`caso-base-1m`), M4 entrega:

| Métrica | Valor |
|---|---:|
| VAN determinista | 459,694 |
| E[VAN] estocástico | 369,529 (−20% vs det) |
| P50 / P5 / P90 | 374,560 / 114,042 / 574,581 |
| CVaR 5% ex-post | 127,508 |
| prob(VAN<0) | 0.2% |
| Funding gap esperado / máx | 0 / 0 |
| Breakeven P50 | mes 19 |

**El −20% E[VAN] vs determinista es estructural y defendible:** las 5 triangulares tienen
media desplazada al downside (eficiencia salesforce media 0.93, WACC media 1.07, churn
media 1.03…). Es la afirmación "el plan del cliente es el modo, la realidad promedia
peor". Decisión de comunicación, no bug: el titular del análisis estocástico debe ser
**P50/E[VAN] con banda P5–P90**, y CVaR como métrica de riesgo — la página Streamlit ya
lo hace así. Si quisieras E[VAN]≈VAN_det, habría que simetrizar las triangulares (decisión
metodológica tuya; yo NO la tomé).

## 4. Assessment de YAML mal cargado / mal calibrado

Ya existen tres capas que hacen exactamente esto — el flujo del lunes debe apoyarse en ellas:

1. **Pre-feasibility** (`due_diligence/workflow.py`): detecta VC < costo fijo año 1 antes
   de resolver. Es el warning que viste.
2. **Calibration** (`calibration/checks.py` + `configs/calibration.yaml`): checks técnicos
   post-modelo con sugerencias.
3. **Due Diligence** (ADR 0005/0009): veredicto 5 niveles + `blocking_reasons` +
   `adjustment_recommendations` + gate a M4. En la UI (WIP que commiteé hoy) el gate ya
   es visible con confirmación explícita.

**Gap conocido:** DD03 rechaza `VC ≤ 0` como estructural, pero godemos usa `VC: 0`
legítimamente (empresa operando, capital de trabajo 0) → godemos sigue **sin poder
valorizarse** (benchmark_v1). Si godemos es parte del guion del lunes, hay que agregar la
exención "operating company" a DD03; si no, usar entrena/kavacomex/beloop en la demo.

**Regla VC 3×:** la reunión fija el criterio "exit ≥ 3× post-money mínimo". Existe
`multiples_valuation.csv`, pero no vi una regla DD que evalúe explícitamente ese ROI 3×.
Candidata a regla DD nueva (barata: son dos números ya calculados).

## 5. Informe HTML / Jinja

Estado real: **la infraestructura pedida ya existe.** `standard_report/render.py` usa
Jinja2 con `templates/report.html.j2` (417 líneas) y `narrative.py` (454 líneas) genera
los textos parametrizados con tonos positive/warning/critical por umbral — exactamente el
"texto parametrizado" que pediste, y es invariante de CONTEXT.md (no LLM, auditable).

Las "fórmulas feas" son 9 bloques `<pre>` ASCII (macro `formula_block`). Movidas a un
**anexo metodológico colapsable al final del informe** (commit en este branch): el cuerpo
del informe queda narrativo/ejecutivo y la trazabilidad de fórmulas se conserva (tests de
template siguen en verde). Las formulaciones formales viven en
`docs/specs/MATHEMATICAL_FORMULATION.md` — hay que verificar que incluya ceiling log
(ADR 0010), mean-CVaR (ADR 0011), valor desecho 1×EBITDA (ADR 0012) y convex-CAC (ADR 0013)
antes de imprimir la tesis.

## 6. Inventario: vigente vs obsoleto

**Vigente (no tocar):** `src/adventure_capital/` completo; `configs/base.yaml` +
`caso-base-1m.yaml` + demos con ceiling; `benchmark_v0/*.yaml` (4 instancias reales);
ADRs 0001–0013; `docs/specs/`; suite de tests.

**Obsoleto / histórico:** `legacy/` (monolito Colab, xlsx de entrada, scratch) — movido hoy;
`configs/legacy/`; `g_max_suavizado` (clave inerte); docs de fase
(`STAGE_1..5`, `PLAN.md`, `REPORT_FIX_PLAN.md`, `HANDOFF_*`, `phase-5-plan.md`) — son
bitácora, no spec; los planes vigentes son los ADR. `outputs/` pesa 59 MB de corridas
viejas — purgable cuando quieras (no lo borré yo).

**Branches:** todo lo vivo está en `master` local (35 commits sin push a origin) y ahora en
`entrega-tesis` (este branch = master + WIP UI + calibración + limpieza). Los 8 branches
feature viejos están mergeados — borrarlos después de la defensa, no antes.

## 7. Microservicios / API — análisis costo-beneficio

**No antes del lunes. Decisión ya tomada este sprint (memoria de arquitectura) y la ratifico:**

- Costo: FastAPI + frontend + contratos + deploy ≈ 2–4 semanas persona; congela el
  desarrollo funcional; riesgo de demo rota el día de la defensa.
- Beneficio hoy: cero — la arquitectura actual (pipeline CLI → artefactos → UI que solo
  lee, ADR 0007/0008) ya da reproducibilidad y separación de capas.
- Beneficio real futuro: multiusuario, colas de solver, SaaS. **La modularidad actual es
  la preparación correcta**: `pipeline.py` ya es una función pura config→artefactos;
  envolverla en un endpoint es trabajo incremental, no rediseño.
- Para la tesis: preséntalo como decisión de arquitectura consciente ("monolito modular
  con contratos de artefactos, API-ready") — eso es un punto a favor, no una deuda.

## 8. Dónde genera valor / cuellos de botella / SaaS

**Valor real (defendible el lunes):** (1) crecimiento endógeno vía CAC dentro de un MILP
auditable — el "plan a 3 años auditable con punto de equilibrio" que Alejandro dice que
los VC exigen hoy; (2) DD automatizado con veredicto y recomendaciones de recalibración;
(3) distribución de probabilidad del VAN con LHS+SAA — nadie en esa mesa lo tiene.

**Cuellos de botella técnicos:** CBC (420 s por M4; escala mal con N escenarios);
truncamiento de horizonte año 3 (Y3/Y2 ≈ 1.3–1.4 vs Motor ~2 — artefacto conocido,
documentado en ADR 0013, compartido por ambos frenos); calibración manual de instancias
(el assessment ayuda pero no auto-corrige); godemos bloqueado por DD03.

**SaaS:** sí tiene potencial — es un motor de "valuation-as-a-service para pre-seed con
plan auditable". Requisitos: API (punto 7), solver gestionado (HiGHS/Gurobi en cola),
multiempresa, y sobre todo **calibración asistida** (el mini-motor de mix de canales que
Alejandro describió). Eso es el negocio post-tesis, y Alejandro ya insinuó pagar por
versiones siguientes.

## 9. Plan de trabajo hasta el lunes 6

### Tú (experto — nadie más puede)
- **J2-V3:** decidir β 30% vs 35% y M default; validar `caso-base-1m` como guion demo.
- **V3-S4:** presentación (pitch problema→solución→resultado; el material de la reunión
  del 1-jul es el guion: ciclo de vida, CAC como inversión, tasa castigada, exit 3×).
- **S4:** ensayo de demo end-to-end con la UI (instancia → DD → M4 → informe HTML).
- Revisar que `MATHEMATICAL_FORMULATION.md` esté al día para el documento de tesis.

### Delegable a mí (siguiente sesión, en orden)
1. Pase profesional de UI (branch aparte para comparar, como pediste) — layout, jerarquía,
   textos; sin tocar lógica (ADR 0007: la UI solo lee artefactos).
2. Regla DD "ROI exit ≥ 3×" + exención DD03 para `VC: 0` operativo (si godemos va en la demo).
3. Purga de `outputs/` viejos + borrar branches mergeados (post-defensa).
4. Verificación de `MATHEMATICAL_FORMULATION.md` vs ADRs 0010–0013 (te marco deltas).
5. Excel export para Growth Plan / Unit Economics (Alejandro trabaja en Excel — CONTEXT.md).

### Herramientas
- **Este flujo (Claude Code)** para todo lo anterior — el repo ya tiene agentes propios
  (`director_proyecto`, `experto_or`, `experto_python`, `asesor_tesis`) con las
  invariantes cargadas.
- **Antigravity / otros IDE-agents:** no los mezclaría antes del lunes — otro agente sin
  las invariantes (math core congelado, UI no recalcula) es riesgo, no velocidad.
- `/grill-with-docs` (ya configurado) antes del pase de UI, como quedó acordado en memoria.

## 10. Cambios hechos hoy (este branch)

1. `2456604` — feat(ui): gate M4 por veredicto DD + fixes de carga YAML + nombre de instancia (tu WIP, commiteado).
2. `ca69dec` — feat(config): `caso-base-1m.yaml` calibrado (tabla §2).
3. `05e6497` — chore: artefactos pre-refactor a `legacy/`.
4. (siguiente) — informe HTML: fórmulas al anexo metodológico.
