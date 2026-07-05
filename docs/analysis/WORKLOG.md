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

**Nota para el próximo agente (Sonnet):** ejecutar SOLO §10 del plan, en branch
`growth-law-adr14`, sin tocar `entrega-tesis`, sin flip de defaults, sin rebaseline
(criterios §9). Checklist de revisión posterior: §11.

## Pendientes conocidos POST-lunes (no de este turno)

- ADR 0014 + implementación producción de `growth_commitment` (piso) + `hiring`
  (fricción) en model.py + paridad stochastic/model.py + claves YAML + goldens.
- Elicitación distribuciones con Maureira (prioridad: salesforce_efficiency 77% de
  varianza, wacc 21%) — ver `distribution_assumptions.md`.
- DD08: base de comparación → drawdown (no gap/VC).
- Mitigación truncamiento año 3 (término de cola).
- Sesión UI (`ui-pro` corre en sesión aparte — no mezclar hasta cerrar modelo).
