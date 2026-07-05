# WORKLOG — cierre de lógica de modelo (goal activo, pre-defensa lunes 6-jul)

Bitácora para retomar el trabajo con contexto completo. Actualizar el estado de cada
ítem al terminarlo (✅ ok / ⚠️ parcial / ❌ falló + nota). Branch: `entrega-tesis`.
Goal de sesión: mecanismo de crecimiento defendible (no ceiling ×8 como core) +
formulación estocástica defendible; si no es factible antes del lunes, documentar
ideal + fallback estable. Restricciones: no UI, no microservicios, no refactor
grande, no calibrar para cuadrar resultados, `uv run pytest -q` verde.

## Contexto mínimo para retomar

- Evidencia base: `threshold_analysis.md` (E1 Unbounded sin freno; E4 fricción de
  contratación acota), `growth_band_experiment.md` (banda mín+holgura: 5 variantes;
  ganadora band-min-hire VAN 3.83M; band-min-only Unbounded), `objective_sweep.md`
  (objetivo estocástico inerte; distribuciones sesgadas son la causa),
  `due_diligence_audit.md` (matriz DD01–DD12), `valuation_unit_economics_map.md`.
- Scripts reproducibles: `scripts/threshold_analysis.py`, `scripts/objective_sweep.py`,
  `scripts/growth_band_experiment.py`.
- Timings SAA (hoy): N=20/50/100 → 11.7/10.6/27.6 s solve; eval 500 ≈ 1 s; plan
  ex-post idéntico entre N y entre (λ,α) — plan en la cota del freno.
- Decisión de fondo ya tomada: ideal = mínimo VC (2×/año, fuente Motor/Maureira) +
  fricción de contratación (h del cliente), SIN techo numérico; fallback lunes =
  ceiling declarado como benchmark. NO implementar la ley nueva en producción antes
  de la defensa (requiere paridad estocástica + ADR 0014 + re-baseline goldens).

## Plan de cierre (este turno)

| # | tarea | estado | notas |
|---|---|---|---|
| 1 | `growth_dynamics_final.md` — mecanismos A + evidencia banda B + decisión | ✅ | tabla completa; slack fijo marcado "supuesto de tesis" |
| 2 | `recourse_extension.md` — qué adapta, info por período, por qué correcto, por qué no lunes | ✅ | |
| 3 | `saa_here_and_now_final.md` — formulación + timings + comparación | ✅ | max E[VAN] = `mean_cvar_lambda: 1.0` (solo config) |
| 4 | `exit_proxy_non_arbitrary.md` — opciones de exit, decisión DCF-core | ✅ | DCF/VR 1×EBITDA core; múltiplos = contraste VC + sensibilidad; tabla de opciones con veredicto |
| 5 | Verificar hitos (criterio 10): breakeven/payback/exit con clientes+dinero+mes en outputs | ⚠️ | mes y dinero directos en artefactos; "clientes en mes de breakeven/payback" existe en optimized_results.csv pero NO como campo propio de summary/informe — gap documentado en exit_proxy §Hitos, fix 1 línea post-lunes |
| 6 | `final_modeling_decisions.md` — implementado / fallback / demo / futuro / riesgos / repro | ✅ | incluye verificación de cumplimiento del goal punto por punto |
| 7 | `uv run pytest -q` verde + commit | ✅ | 161 passed, 3 skipped (36.8 s) |
| 8 | Actualizar este WORKLOG con resultados | ✅ | este archivo |

## Qué salió bien / mal (para el próximo agente)

- **Bien:** banda mín+holgura inyectable post-build sin tocar core (patrón: `build_model`
  → añadir restricciones al `bundle["problem"]` → `solve_model`); reutilizable para
  prototipar cualquier freno. SAA barato (≤30 s hasta N=100).
- **Mal / sorpresas:** (1) banda 2×/año como TECHO destruye upside (VAN 2.5k) — no
  proponer banda-techo con g conservador; (2) `evaluate_strategy` espera
  `solved["strategy"]`, no `solved` (KeyError A_sf_plan si te equivocas);
  (3) `run_pipeline` con `output_dir` corre consistency checks que EXPLOTAN con
  soluciones unbounded — para experimentos de status usar `build_model`+`solve_model`
  directo; (4) ceiling default-on: variantes "sin freno" requieren
  `acquisition_ceiling: {enabled: false}` explícito.
- **No hecho a propósito:** implementación producción de piso+fricción (necesita
  paridad estocástica; improvisarla el fin de semana rompería estabilidad — goal lo
  permite explícitamente como "ideal documentado + fallback estable").

## Plan turno 2026-07-05 AM (goal: PLAN ONLY, no implementar)

| # | tarea | estado | notas |
|---|---|---|---|
| P1 | Auditoría YAMLs benchmark: params sospechosos, clasificar benchmark/demo/stress/excluir | ✅ | los 4 válidos y con targets documentados en el propio YAML. godemos+entrena = benchmark+demo; **beloop = excluir de demo** (downgrades no modelados → +469% VAN, documentado en el YAML); kavacomex = stress clave del piso (ramp real 0.99 → piso 2× puede ser Infeasible). Hacks visibles: `sup: 99` (sin líderes), metas ajustadas |
| P2 | Spot-check artefactos | ✅ | 3 corridas: 8 artefactos presentes, `consistency all_passed=True`, estocástico ausente con razón explícita ("not executed. Reason: requires_major…") — manejo limpio verificado |
| P3 | `implementation_plan_growth_law.md` — plan 14 puntos | ✅ | ley recomendada = D (piso VC + fricción, sin techo); curva especificada (P0=m12 consensuado, P1=año 3 tesis, g de fuente declarada VC/MoM/custom, PISO no banda); decisión: **NOT READY hoy sin autorización de Alonso, READY como plan**; bloqueante humano (g por instancia, kavacomex), no técnico; rollback = opt-in default-off + branch aparte |
| P4 | Actualizar WORKLOG | ✅ | este archivo |

**Nota para el próximo agente (Sonnet):** ejecutar SOLO §9 del plan REV 2, en branch
`growth-law-adr14`, sin tocar `entrega-tesis`, sin flip de defaults, sin rebaseline
(criterios §8). Checklist de revisión posterior: §10.

## Rev 2026-07-05 PM — decisiones de Alonso (plan REV 2, autorización de implementación)

- **Cambiado:** benchmark vc_minimum = **×3 en 3 años** (C36 ≥ 3·C12), NO ×2 anual;
  **PISO con checkpoints anuales** (C24 ≥ √3·C12, C36 ≥ 3·C12), sin piso mensual;
  sin restricciones de caja nuevas; plan_mom = diagnóstico (sin clamps, sin
  no-linealidades — si es sospechoso: warning W1 + revisión humana); custom con
  justificación obligatoria (W4); **Infeasible = resultado válido de negocio** con
  diagnóstico estructurado §5 (8 relajaciones dirigidas → diagnóstico, sin IA).
- **Decisiones humanas resueltas:** forma del piso (checkpoints anuales); piso stoch
  sobre stock PLANEADO; kavacomex = ambos modos + análisis de palancas de
  factibilidad; timing = **AHORA** (Sonnet autorizado, restricciones estrictas §9).
- **Blockers restantes:** ninguno de decisión. Gate de rebaseline = humano
  (`final_growth_decision.md` APPROVED).
- **Estado: READY TO IMPLEMENT — Sonnet lanzado en worktree `growth-law-adr14`.**

## Pendientes conocidos POST-lunes (no de este turno)

- Elicitación distribuciones con Maureira (prioridad: salesforce_efficiency 77% de
  varianza, wacc 21%) — ver `distribution_assumptions.md`.
- DD08: base de comparación → drawdown (no gap/VC).
- Mitigación truncamiento año 3 (término de cola).
- Sesión UI (`ui-pro` corre en sesión aparte — no mezclar hasta cerrar modelo).

## Rev 2026-07-05 — implementación `growth_commitment` + `hiring` (Sonnet, branch `growth-law-adr14`)

**Estado: IMPLEMENTADO. Suite completa verde (171 passed, 3 skipped; era 161/3 — 10 tests
nuevos, cero goldens tocados). `entrega-tesis` intocado (verificado: HEAD sin cambios,
branch de trabajo creado con `git checkout -b growth-law-adr14` desde `entrega-tesis`).**

Implementado (orden del plan §9):

1. `config.py`: claves `growth_commitment`/`hiring` + validaciones completas (source
   enum, multiple_3y>1, floor_slack∈[0,1), custom exige g_annual, hiring h>=0,
   coexistencia ceiling/commitment con error claro si el ceiling < el compromiso).
2. `instance.py`: `C12` precomputado (mismo phi/survival que el ceiling, sin solve),
   `checkpoint_targets` (B_24=√m·C12, B_36=m·C12), `compute_growth_suggestions`
   (g_vc_minimum, g_plan_mom_acquisition, g_plan_mom_stock — corrección: se reportan
   AMBOS, el stock MoM es el comparable porque el piso ata sobre stock —, g_required_rev
   si el YAML declara `target_revenue_y3`).
3. `model.py`: bloques aditivos condicionados a `enabled` (piso en `sum_s C[s,checkpoint]`,
   fricción en V/L); `H` < checkpoint levanta `ValueError` claro en vez de fallar en
   silencio.
4. `due_diligence/rules.py`: W1-W5 como DD13-DD17 (WARNING únicamente, nunca bloqueo),
   funciones puras importables; NO wireadas en el chain automático de
   `run_due_diligence` (la trampa conocida: `run_pipeline`+`output_dir` explota con
   solves no-Optimal, y un commitment infeasible es un resultado válido esperado —
   evitar ese choque quedó documentado como trabajo futuro explícito, no forzado).
5. `stochastic/model.py`: paridad — fricción en V/L de primera etapa (idéntica forma),
   piso sobre el stock PLANEADO (pre-eficiencia, `plan_total` con `phi` de la instancia
   base, no de ningún escenario). Paridad V-path verificada empíricamente (escenario
   único determinista, mismo objetivo/mismo V-path que el modelo determinista). KPI
   ex-post `P(C36_real >= multiple_3y*C12)` vía el mecanismo existente de milestones
   (`prob_hit_final_active_clients_{milestone}`), sin artefacto nuevo.
6. `scripts/diagnose_infeasibility.py`: rutina R1-R8 (fricción, publicidad, mix,
   churn, costo fijo, costo unitario, piso de caja, el múltiplo mismo) como función
   pura config→JSON + CLI, mismo patrón de inyección que
   `scripts/growth_band_experiment.py`.
7. `tests/test_growth_commitment.py`: los 10 tests exactos del plan §6, todos en H=36
   (los checkpoints m24/m36 lo exigen; solve ~0.1s, muy por debajo del budget de 60s —
   no hizo falta el fallback H=26).
8. `scripts/growth_commitment_benchmarks.py` + `docs/analysis/growth_commitment_benchmarks.md`:
   4 instancias × {off, vc_minimum, vc_minimum+hiring h=1}; kavacomex además `none` +
   rutina R1-R8 completa (corrida SIEMPRE, no solo si infeasible, per instrucción).
   **Hallazgo principal**: `off` == `vc_minimum` en las 4 instancias — el ceiling
   default (ADR 0010, x3/slack 0.15) ya despeja el piso x3 con holgura en las 4, incluso
   con hiring h=1; kavacomex (esperado como candidato a Infeasible, ramp real ~0.99x)
   también resultó Optimal por la misma razón. Corrida de contraste (ceiling
   desactivado) confirma que el piso solo nunca acota por arriba (`Unbounded` en las 4,
   comportamiento esperado ADR 0010/0013) — nunca se subió el multiplicador del ceiling
   como parte de esta feature (instrucción explícita).
9. `docs/adr/0014-growth-commitment-hiring-friction.md`: decisión completa, incluye
   las 3 correcciones del supervisor (semántica ×3/3años explícita; stock MoM +
   acquisition MoM ambos reportados; ceiling nunca core, verificado con ceiling off).

**No hecho a propósito / limitación documentada**: W1-W5 no están wireadas en el chain
automático `run_due_diligence`/`run_assessment` (razón: trampa conocida de
`run_pipeline`+`output_dir` con solves no-Optimal). Quedan como funciones puras
importables, cubiertas por tests directos — endurecer ese chain para tolerar
Infeasible-con-commitment es trabajo futuro explícito, no un blocker de esta entrega.

**Rollback**: desactivar `growth_commitment.enabled`/`hiring.enabled` (o ausentar las
claves) — sin código a revertir, el no-op está verificado por test
(`test_commitment_off_is_noop`, `test_hiring_off_is_noop`).

## Rev 2026-07-05 tarde — diagnóstico Unbounded + benchmarks destino + cableo W1-W5

| tarea | estado | notas |
|---|---|---|
| Diagnóstico camino Unbounded (goal audit) | ✅ | **el modo destino (piso+fricción+ceiling off) NO es Unbounded: Optimal en las 4 instancias, h=1 y h=2** — la tabla Unbounded previa era piso SIN fricción. Camino unbounded real y único: **third_party sin cota propia** (tp-only Unbounded con y sin comisión; sf acota vía fricción, ad vía I_max+cap). Cash≥0 duro = Infeasible (esperado). Ver `unbounded_path_diagnosis.md` + `scripts/unbounded_path_matrix.py` |
| Benchmarks modo destino | ✅ | tabla en diagnosis §0; VAN escala ~lineal en h (h = palanca declarada del cliente); kavacomex destino h=1: VAN +620k vs −378k con ceiling |
| Cableo W1-W5 a DD | ✅ | workflow.py: W1/W2/W4/W5 pre-modelo + W3/DD17 en camino normal (chain sobrevive vía C01) Y en camino de excepción (re-solve + reporte limpio). Test nuevo. Suite **172 passed, 3 skipped**. Nota: W1/W2 disparan solo con `source: plan_mom` (scoping de Sonnet, mantenido) |
| Fix mínimo tp propuesto (NO implementado) | ⏳ | opción segura pre-lunes: validación config; estructural post-defensa: `A_tp_cap` espejo de `A_ad_cap` (diagnosis §5-6) |
