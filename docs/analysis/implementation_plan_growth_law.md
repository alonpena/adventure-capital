# Plan de implementación — ley de crecimiento (PLAN ONLY, sin código aún)

Fecha: 2026-07-05 AM · Goal: backend core antes de UI; determinista y estocástico con
LA MISMA ley; ceiling ×8 inaceptable como core. Evidencia previa citada, no repetida:
`threshold_analysis.md` (E1–E4), `growth_band_experiment.md`, `objective_sweep.md`,
`growth_dynamics_final.md`, `due_diligence_audit.md`, `saa_here_and_now_final.md`.

## 0. Respuestas previas al código (preguntas 1–12 del goal)

1. **Ley actual:** ceiling logarítmico sobre stock (ADR 0010, default-on,
   `instance.py:77-103`, aplicado en `model.py` y `stochastic/model.py:169-177`).
   Convex-CAC opt-in (ADR 0013). Media móvil inerte.
2. **Dónde se restringe el crecimiento:** t≤12 adquisición exógena (`A_base`);
   t≥13: ceiling (nivel), capacidad salesforce `Σsf ≤ meta·V_{t-lag}` + `V ≤ sup·L`
   + monotonía V/L (`model.py:248-289`), publicidad `A_ad = a+b·I, I∈[I_min,I_max],
   ≤ A_ad_cap` (`model.py:180-196`), shares por canal, escalones `u_max`, caja.
3. **Por qué sin freno = Unbounded:** valor marginal por cliente positivo constante
   (c_u≈0 real), contratación sin costo de ajuste ni límite de ritmo, canales
   lineales ⇒ LP empuja A→∞. Falta el costo/fricción de CRECER, no un techo de mercado.
4. **Ya existe en código:** ceiling ✓; ad min/max gasto ✓ (I_min/I_max, t≥13);
   ad eficiencia min/max ✗ determinista (b constante — la eficiencia varía solo en
   escenarios estocásticos) pero cap A_ad_cap ✓; min/max shares ✓ (+ validación
   Σmin≤1 del 2026-07-05); monotonía salesforce ✓ (sin despidos); caja ✓.
5. **Falta para crecimiento tipo startup:** (a) fricción de contratación/onboarding
   (ritmo máximo + lag de productividad — el lag YA existe como parámetro, default 0);
   (b) piso de compromiso de crecimiento (benchmark VC); (c) opcional: saturación
   cóncava de publicidad.
6. **YAMLs bien cargados/calibrados:** ver §5 — estructura válida los 4; calibración
   con supuestos blend documentados en cada YAML; beloop mal especificado (downgrades).
7. **DD warnings:** mayormente señal real de negocio o de freno (no reglas excesivas);
   detalle §6.
8. **Candidatas:** §2.
9. **Paridad det/estocástico:** §3.2 paso 4.
10. **Tests pre-rebaseline:** §3.4.
11. **Artefactos:** §7 (spot-check hoy: 3 corridas completas, `all_passed=True`,
    estocástico ausente manejado con razón explícita — verificado).
12. **Sonnet vs futuro:** §10/§12.

## 1. Ley recomendada: IMPLEMENTAR (post-decisión, pre-rebaseline controlado)

**`growth_commitment` (piso) + `hiring` (fricción) — candidata D del goal, SIN techo
numérico.** Ceiling queda como guard-rail OPCIONAL (default off tras migrar) —
candidata A = fallback de emergencia. Justificación: única combinación probada
(Optimal, upside intacto VAN 3.83M, rampa orgánica, min caja −11.9k) cuyos dos
parámetros tienen dueño de negocio: g (tesis de inversión) y h (plan de contratación).

### Ajuste de la curva mínima (especificación exacta)

```text
Puntos de anclaje:
  P0 = (m12, C12)      C12 = stock de clientes del plan consensuado en el mes 12
                       (determinista dado A_base y churn; base.yaml: 55.8)
  P1 = (m36, C36_obj)  C36_obj = C12·(1+g_anual)^2   [tesis de inversión año 3]

Fuentes admisibles de g_anual (en orden de preferencia, declarada en YAML):
  a) tesis VC pactada: 2.0 (duplicar cartera/año — Motor godemos realizado + regla Maureira)
  b) MoM implícito del propio plan consensuado: g_mom = (A12/A1)^(1/11)−1 anualizado
     (base.yaml: 15.8%/mes ⇒ 4.8×/año)
  c) parámetro explícito del cliente

Curva: B_t = C12·(1+g_m)^(t−12),  g_m = (1+g_anual)^(1/12)−1,  t = 13..H
Rol:   PISO (floor). stock_t ≥ B_t. NO es techo ni banda.
Techo: NINGUNO numérico — acotan fricción de contratación + caja + capacidad + canales.
Slack: al piso, tolerancia hacia ABAJO opcional δ (stock_t ≥ (1−δ)·B_t), default 0;
       si se usa, δ se declara supuesto. Variantes techo (fija/anual/MoM) EVALUADAS y
       DESCARTADAS con evidencia (matan upside; `growth_band_experiment.md`).
Fricción: V_t ≤ V_{t−1} + h_v;  L_t ≤ L_{t−1} + h_l;  t ≥ 13
       h_v = plan de contratación del cliente (YAML, como A_base); default propuesto 1.
       Onboarding: usar commercial_productivity_lag existente (recomendar 1–2 meses).
```

## 2. Matriz de candidatas (A–G)

| cand. | fórmula | sentido | params | arbitrar. | costo impl. | costo paridad stoch | comportamiento esperado benchmarks | recomendación |
|---|---|---|---|---|---|---|---|---|
| A ceiling log (actual) | stock ≤ curva log → M·C12 | proxy mercado | M, slack | alto (VAN~lineal en M) | 0 | 0 (ya en paridad) | reproduce hoy; Y3 sobre-crece vs Excel (+74/334%) | **fallback emergencia**, default off tras migrar |
| B mín + slack techo dinámico | B_t ≤ stock ≤ B_t(1+δ_t) | banda compromiso | g, δ_t | medio (δ) | ~20 líneas | medio | probado: mata upside salvo δ del MoM | rechazar como core; δ-MoM documentado |
| C mín + caps pub + caja + mix | piso + frenos existentes | "lo que ya hay + piso" | g | bajo | ~15 líneas | bajo | **Unbounded en salesforce-only** (band-min-only) — solo acota si publicidad/capacidad activas y apretadas | rechazar como core general |
| **D mín + fricción contratación** | §1 | piso VC + ritmo real de crecer | g, h_v, lag | **bajo** | ~30 líneas det | ~30 líneas (espejo en first-stage V/L, que ya existen en SAA) | godemos/entrena: rampa continua, VAN entre convex y ceiling; kavacomex (ramp plano 0.99): piso 2× puede ser INFEASIBLE → g por instancia o δ>0 — riesgo conocido | **CORE** |
| E mín + convex-CAC | piso + premium θ·k | saturación económica | g, θ | alto (θ*45–300) | 0 (existe) | pendiente ADR 0013 paso 5 | sobre-conservador | rechazar; comparación tesis |
| F CAC por tramos (general) | curvas por canal | saturación por canal | tabla tramos | medio | alto | alto | n/a | futuro |
| G híbrida (D + guard-rail A opcional) | D + stock ≤ ceiling(M_grande) | piso+fricción con paracaídas | D + M | bajo si M solo guard-rail documentado | D + 0 | D + 0 | como D con cota de cordura | aceptable si el comité exige techo explícito |

## 3. Pasos exactos de implementación (Sonnet, post-defensa o si Alonso lo autoriza hoy)

1. **Config** (`config.py`): claves `growth_commitment: {enabled, annual_growth,
   source: vc|mom|custom, floor_slack}` y `hiring: {max_new_sellers_per_month,
   max_new_leaders_per_month}`; validaciones (g>0, h≥0, source∈enum). DEFAULTS:
   commitment off, hiring off (opt-in primero; flip de default = decisión aparte).
2. **Instance** (`instance.py`): precomputar `C12` (determinista desde A_base+churn —
   reusar delta/phi), curva `B_t`, exponer `growth_commitment` + `hiring` en instance.
3. **Determinista** (`model.py`): bloque nuevo tras el ceiling —
   `Σ_s C[s,t] ≥ (1−δ)·B_t` y `V_t ≤ V_{t−1}+h_v`, `L_t ≤ L_{t−1}+h_l` (t≥13),
   activos solo si enabled. Mutuamente exclusivo con convex? NO — ortogonal; sí
   validar que commitment+ceiling simultáneos exijan ceiling ≥ piso (infeasibility
   temprana con mensaje claro).
4. **Paridad estocástica** (`stochastic/model.py`): mismas restricciones sobre
   first-stage `V/L/plan_total`; stock por escenario: piso aplica al stock PLANEADO
   (pre-eficiencia) para mantener first-stage único — documentar elección en ADR.
5. **ADR 0014**: decisión, fuentes de g, elección de piso-planeado vs realizado,
   kavacomex caveat.
6. **Pre-feasibility** (`due_diligence/workflow.py`): chequeo barato
   `B_H alcanzable con h_v·meta` → warning si no (evita Infeasible ciego).

## 4. Tests a agregar/actualizar (antes de cualquier rebaseline)

- Nuevos: commitment respeta piso (stock_m24 ≥ B_24); Infeasible claro si g imposible
  con h dado; hiring friction limita salto (V_13 ≤ V_12+h); paridad: det y stoch
  producen mismo V-path año 2 con mismos params; validaciones config (g≤0, h<0,
  ceiling < piso). Extender `test_model_behavior.py` (patrón ya establecido).
- Actualizar: goldens/smoke que asuman ceiling default-on SI se flippea el default
  (NO flippear en el mismo PR que introduce la ley — dos pasos).
- Verde previo obligatorio: `uv run pytest -q` (hoy: 161 pass / 3 skip).

## 5. Auditoría YAML benchmarks (hecha hoy — leídos los 4)

| instancia | estructura | params sospechosos | causa de warnings DD | uso |
|---|---|---|---|---|
| godemos | ✓ (targets y simplificaciones documentadas en el YAML) | `sup: 99` (hack "sin líderes"); `meta 15` ajustada (nominal 5); c_u 0.10 casi cero (blend) | VC=0 → DD03-warning (exención, correcta); DD12 1.7×<3× = señal real | **benchmark + demo** (corre desde 2026-07-03) |
| entrena | ✓ | `meta 20` para 1 vendedor (no restrictiva por diseño); c_min 8000 alto vs c_u 10 | EBITDA yr1 negativo (real, target también) | **benchmark + demo** (passed_with_warnings) |
| beloop | ✓ | downgrades Enterprise→Pro NO modelados (documentado) → +469% VAN vs target; Enterprise churn 0 | modelo sobre-crece por especificación, no por regla | **stress test / EXCLUIR de demo** |
| kavacomex | ✓ | c_u 97 vs ticket 140 (margen bruto ~31%, el único caso costo-intensivo); ramp real plano (0.99) | conservador legítimo | **benchmark + stress para el piso** (piso 2× puede ser infeasible — caso de prueba clave) |

Carga: los 4 pasan `validate_config`; la UI preserva campos extra (fix 7320aba).

## 6. Clasificación DD (plan de severidades, no implementación)

Matriz completa en `due_diligence_audit.md`. Resumen: DD01/02/04 + C01 = validación
técnica dura (bloquear, correcto); DD05/07/08/11 + C04–C10 = plausibilidad financiera
(advertir); DD06/09/10/12 = tesis VC (advertir/major, correcto); DD03 = dura con
exención declarativa (correcto desde 2026-07-03). Por qué muchos casos warn: los
warnings observados son señal (EBITDA yr1 negativo real, exit 1.7×<3× real, breakeven
tardío bajo freno apretado) — no reglas excesivas. Único cambio planificado: DD08
base = drawdown (no gap/VC). Ningún cambio de severidad se implementa este fin de semana.

## 7. Chequeos de artefactos (spot-check hoy + lista para corrida final)

Verificado hoy en 3 corridas (godemos-dd12, m8-vc200, base-default): 8 artefactos
esperados presentes, `consistency_report.all_passed=True`, dcf 3 años, estocástico
ausente manejado con razón explícita ("not executed. Reason: …"). Para la corrida
final de demo: mismos chequeos + informe HTML render (executive page) + breakeven/
payback/exit visibles (gap conocido: "clientes en mes de breakeven" no está en
summary — documentado, no bloqueante).

## 8. Grilla de sensibilidad requerida (diseño; ejecutar post-decisión de ley)

Palancas (1-D, ±2 niveles c/u sobre caso demo; herramienta: extender
`threshold_analysis.py`, mismo patrón): VC {50k,100k,150k}; ticket ×{0.8,1.2};
churn ×{0.8,1.3}; alpha {0.7,0.95}; com_v/rem_v ×{1,2}; I_max ×{0.5,2} y b ×{0.7,1.3}
(si ad activa); meta ×{0.75,1.25}; min_shares {0,0.3}; beta {0.30,0.35}; h {1,2,3};
lag {0,2}; δ piso {0,0.1}. Outputs por celda (todos ya extraíbles): clientes m36,
ingresos Y3, EBITDA Y3, VAN, min caja+mes (capital requerido), breakeven (mes/
clientes/EBITDA acum), payback (mes/clientes/VC), exit proxy + post-money + ROI
(DD12 evidence), V/L path, veredicto DD, artefactos ok. ~26 solves ≈ 15 min.

## 9. Criterios de rebaseline de goldens + rollback

Rebaseline SOLO si: (1) ADR 0014 aceptado por Alonso; (2) tests nuevos §4 verdes;
(3) paridad det/stoch demostrada; (4) 4 benchmarks corridos con la ley nueva y
deltas vs targets Excel tabulados (no exigir ±20% — exigir EXPLICACIÓN de cada
delta); (5) commit separado solo-goldens con tabla antes/después en el mensaje.
**Rollback:** la ley entra opt-in con default off ⇒ rollback = no activar la clave
(cero riesgo); si se flippeó default: revert del commit de flip + goldens (por eso
van separados). Branch de trabajo aparte (`growth-law-adr14`), `entrega-tesis`
intocado hasta merge post-defensa.

## 10. Qué implementa Sonnet (lista de tareas, en orden)

1. §3.1 config + validaciones + tests de validación.
2. §3.2 instance (C12, B_t) + test unitario de la curva (C12 base = 55.8 ± redondeo).
3. §3.3 bloque determinista + tests de comportamiento §4.
4. §3.6 pre-feasibility warning.
5. §3.4 paridad estocástica + test de paridad.
6. Corridas benchmark ×4 + tabla deltas (sin tocar goldens).
7. NADA de UI, NADA de flip de defaults, NADA de rebaseline sin §9.

## 11. Checklist de revisión Fable post-Sonnet

- [ ] Piso aplica a stock PLANEADO en stoch (first-stage única) y está en el ADR.
- [ ] Ceiling+commitment simultáneos validados (mensaje de infeasibilidad claro).
- [ ] kavacomex: comportamiento del piso 2× (¿infeasible? → ¿mensaje/δ?).
- [ ] Ningún golden tocado fuera del commit de rebaseline.
- [ ] `V_t ≤ sup·L_t` sigue activo (fricción no rompe span).
- [ ] Tiempos de solve (≤ 60 s det, ≤ 420 s stoch N=100).
- [ ] Paridad: mismo V-path det vs stoch bajo params idénticos.

## 12. Futuro (no Sonnet ahora)

Recourse/rolling horizon (`recourse_extension.md`); saturación publicidad cóncava;
CAC por tramos general (F); elicitación distribuciones; DD08 drawdown; múltiplos
comparables con fuente; mini-optimizador de mix.

## 13. Incluido / Excluido / Diferido

- **Incluido (este plan):** ley D, paridad, tests, sensibilidad, auditoría YAML/DD/artefactos, rollback.
- **Excluido:** UI/CSS/informe, microservicios, SaaS, BrightData.
- **Diferido:** flip de default, rebaseline, §12.

## 14. Decisión

**NOT READY para implementar HOY (sábado) sin autorización de Alonso — READY como
plan.** Bloqueante único: decisión humana (g por instancia vs global; aceptar
infeasibilidad de kavacomex o δ>0), no técnica. Esfuerzo estimado: 0.5–1 día Sonnet +
revisión §11. **Para el lunes el fallback estable ya está definido y probado**
(ceiling declarado benchmark, suite verde, artefactos consistentes). Si Alonso
autoriza hoy: ejecutar §10 en branch aparte SIN tocar `entrega-tesis`; si no,
ejecutar post-defensa. No se finge nada: la ley ideal está cuantificada
(`growth_band_experiment.md`) pero NO implementada en producción.
