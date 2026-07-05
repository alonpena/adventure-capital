# Decisión final ley de crecimiento — revisión de supervisor (Fable)

Fecha: 2026-07-05 · Branch revisado: `growth-law-adr14` (commits e6e7c6e + fa8f7b3)
· Revisor: Fable (supervisor) · Implementador: Sonnet · **Gate de rebaseline: este
doc debe decir APPROVED, firmado por Alonso.**

## Veredicto: **PARTIAL — mantener experimental, fallback (`entrega-tesis`) intacto**

Mecanismo correcto, verificado y seguro (opt-in, no-op probado). NO listo para
declararse core ni para demo activa por los 3 gaps de abajo. Nada bloquea la
defensa del lunes: el fallback no fue tocado.

## Checklist de revisión (verificación INDEPENDIENTE, no auto-reporte)

| # | check | resultado |
|---|---|---|
| 1 | `uv run pytest -q` en worktree | ✅ **171 passed, 3 skipped** (corrido por el revisor; baseline 161) |
| 2 | No-op con claves off | ✅ tests `*_off_is_noop` con asserts de objetivo idéntico + columnas Adq/Vendedores iguales |
| 3 | Commitment determinista | ✅ `test_commitment_checkpoints_hold`: C24 ≥ √3·C12, C36 ≥ 3·C12 verificados en solución |
| 4 | Commitment estocástico stock-planeado | ✅ código en `stochastic/model.py:240-251` (floor sobre plan primera etapa) + `test_parity_det_stoch_first_stage` (V-path idéntico) |
| 5 | Fricción de contratación | ✅ `test_hiring_friction_limits_jump` (V13 ≤ V12+h, L13 ≤ L12+h) |
| 6 | Infeasible → diagnóstico limpio, sin crash | ✅ `test_commitment_infeasible_reported` + `test_diagnosis_routine_smoke` (R1 restaura, JSON estructurado) |
| 7 | Benchmarks 4 instancias | ✅ corridos ×{off, vc_minimum, +hiring}; tabla honesta con binding-check; kavacomex ambos modos + R1-R8 |
| 8 | Integridad artefactos | ✅ corrida godemos con commitment ON: `consistency all_passed=True`, VAN coherente, `growth_suggestions.json` emitido con MoM de adquisición Y de stock |
| 9 | final_growth_decision.md | ✅ este documento |
| 10 | Rollback documentado | ✅ aquí (faltaba en ADR 0014 — gap menor, ver abajo): **rollback = `growth_commitment.enabled: false` y `hiring.enabled: false` (o borrar las claves). Cero efecto residual (no-op bit-a-bit probado). Abandono total = no mergear `growth-law-adr14`.** |

Guardrails 1-10 de Alonso: cumplidos. `entrega-tesis` verificado intocado (HEAD
`dd0cc08`, working tree limpio; los dirs `diagrams/` y `docs/architecture/`
untracked son de otra sesión de las 08:29, previos a Sonnet). Sin UI, sin goldens,
sin flips de default, sin refactor (diff 100% aditivo, 13 archivos).

## Hallazgo estructural del benchmark (importa para la decisión de core)

En las 4 instancias reales, `vc_minimum` == `off` numéricamente: **el ceiling
default (×3, slack 0.15) ya supera los checkpoints del compromiso** (~2.4-2.9× en
m24, ~3.1-3.5× en m36). El piso es correcto pero redundante mientras el ceiling
default-on comparta el múltiplo ×3. Piso sin ceiling = Unbounded en las 4
(esperado: el piso nunca acota por arriba).

## Gaps que impiden PASS (ninguno bloquea el lunes)

1. **El modo destino (piso + fricción, ceiling OFF) no fue corrido sobre los 4
   benchmarks.** Es la combinación que reemplazaría al ceiling como core (evidencia
   solo en base.yaml, `growth_band_experiment.md`: Optimal, VAN 3.83M). Sin esa
   tabla no se puede decidir el flip de default.
2. **W1-W5 no cableados al flujo automático de DD** (funciones puras testeadas,
   pero `run_due_diligence` revienta con solves no-Optimal — trampa conocida).
   Follow-up documentado por Sonnet en ADR/WORKLOG.
3. Rollback ausente del ADR 0014 (subsanado en este doc; añadir al ADR en el
   follow-up).

## Próximos pasos (post-defensa, en este orden)

1. Correr 4 benchmarks × {piso+fricción h∈{1,2}, ceiling off} + tabla.
2. Cablear W1-W5 a DD (endurecer `run_due_diligence` ante Infeasible esperado).
3. Añadir sección rollback al ADR 0014.
4. Con (1)-(3): Alonso decide flip de default + rebaseline (criterios plan §8).

## Firma

- Revisor (Fable): PARTIAL, 2026-07-05.
- Alonso: ☐ APPROVED PARA REBASELINE / ☐ MANTENER EXPERIMENTAL — pendiente.
