# Plan de implementación — ley de crecimiento (REV 2, decisiones de Alonso resueltas)

Fecha: 2026-07-05 (rev 2, post-decisiones) · Reemplaza REV 1 del mismo día.
Evidencia: `threshold_analysis.md` (E1–E4), `growth_band_experiment.md`,
`growth_dynamics_final.md`, `objective_sweep.md`, `saa_here_and_now_final.md`.
**Estado: AUTORIZADO POR ALONSO — Sonnet implementa AHORA en branch `growth-law-adr14`,
`entrega-tesis` intocado.**

## 1. Recomendación revisada (decisiones finales)

**`growth_commitment` = PISO de tesis de inversión, no techo ni banda:**

- **vc_minimum (benchmark estándar): ×3 en 3 años sobre stock de clientes.**
  `C36 ≥ 3·C12`, con C12 = stock del plan consensuado en mes 12. Fuente: regla VC
  3× (reunión Maureira 2026-07-01, retorno big-tech 3 años). El ×2 anual queda
  DESCARTADO como default (era más agresivo: 4× en 2 años).
- **Forma: terminal + checkpoints anuales** (decisión Alonso):
  `C24 ≥ √3·C12` y `C36 ≥ 3·C12`. Sin piso mensual (evita infeasibilidad espuria
  por estacionalidad); auditable por año (lógica VC de hitos). Constantes
  precomputadas ⇒ 2 restricciones lineales, MILP intacto.
- **Sin restricciones de caja nuevas**: la única consideración es la existente
  (caja no baja de −VC cuando la política lo activa). Nada más.
- **plan_mom = diagnóstico/sugerencia, NUNCA default automático.** Si el MoM
  implícito del plan es sospechoso, NO se recorta ni se corrige con no-linealidades:
  se emite warning DD/calibración y se exige revisión humana.
- **custom = override experto (Alejandro)** con justificación obligatoria.
- **none = bottom-up puro** sin compromiso (valorización sin piso).
- **Infeasible = resultado válido de negocio**: "esta estructura no soporta la
  tesis ×3". Se acompaña SIEMPRE del diagnóstico estructurado (§5), jamás se trata
  como error del modelo.
- **Fricción de contratación opt-in**: `V_t ≤ V_{t−1} + h_v`, `L_t ≤ L_{t−1} + h_l`
  (t ≥ 13); h = plan de contratación del cliente. Onboarding vía
  `commercial_productivity_lag` existente.
- **Estocástico: piso sobre stock PLANEADO de primera etapa** (pre-eficiencia),
  manteniendo here-and-now único; se reporta `P(C36_realizado ≥ 3·C12)` como KPI
  ex-post (decisión Alonso).
- Ceiling log: guard-rail opcional; **nunca core**; default off intacto en este
  branch (sin flip).

## 2. Config schema EXACTO

```yaml
growth_commitment:
  enabled: false                 # opt-in estricto; default off = no-op total
  source: vc_minimum             # vc_minimum | plan_mom | custom | none
  multiple_3y: 3.0               # C36 >= multiple_3y * C12 (vc_minimum)
  checkpoints: annual            # annual -> C24 >= sqrt(m)*C12 y C36 >= m*C12
                                 # terminal -> solo C36
  floor_slack: 0.0               # tolerancia hacia abajo declarada: C_k >= (1-slack)*B_k
  custom_g_annual: null          # requerido si source: custom (crecimiento anual del stock)
  custom_justification: null     # requerido no-vacío si source: custom (si falta -> warning DD)

hiring:
  enabled: false                 # opt-in estricto
  max_new_sellers_per_month: 1   # h_v >= 0
  max_new_leaders_per_month: 1   # h_l >= 0
```

Validaciones (`validate_config`): `multiple_3y > 1`; `source` en enum; `custom` ⇒
`custom_g_annual > 0`; `floor_slack ∈ [0,1)`; `h_* ≥ 0` enteros; `checkpoints` en
enum. `plan_mom` como source: usa g del MoM del plan PERO exige que el warning W1/W2
(§4) no sea silenciado — el YAML lo elige explícitamente, el sistema no lo elige solo.

### Curva / puntos (formulación exacta, lineal-compatible)

```text
C12 = Σ_s C[s,12] — determinista dado A_base y churn (precomputable en instance.py
      con los mismos delta/phi del modelo; base.yaml: 55.8).
m   = multiple_3y (o (1+g)^2 si source custom/plan_mom, con g anual de la fuente)
Checkpoints (annual):  C24 >= (1-slack)·√m·C12   ·   C36 >= (1-slack)·m·C12
Interpolación implícita exponencial mensual (m^((t-12)/24)) SOLO como referencia
de reporting/sugerencias — no se impone mensualmente. Constantes precomputadas:
cero no-linealidades en el MILP.
```

## 3. Motor de sugerencias de g (calcular y REPORTAR, jamás elegir en silencio)

Computado en `instance.py`/calibración y emitido en artefacto
(`growth_suggestions.json`) + informe:

```text
g_vc_minimum   = multiple_3y^(1/2) − 1  anual        (×3 ⇒ 73.2%/año; 4.68%/mes)
g_plan_mom     = (A_base[12]/A_base[1])^(1/11) − 1   mensual, anualizado (base: 15.8%/mes ⇒ 4.8×/año)
g_required_rev = ((R_target_y3 / rev_anual_por_cliente) / C12)^(1/2) − 1  anual
                 SI el YAML declara target_revenue_y3 (clave nueva opcional);
                 rev_anual_por_cliente = annual_revenue_per_customer (unit_economics)
                 — aproximación de mix constante, declarada.
custom         = lo que fije el experto (con justificación).
```

UI podrá mostrar los candidatos para calibración (extensión futura, NO este branch).

## 4. Warnings DD/calibración nuevos (plan; implementación = reglas warning, nunca bloqueo)

| id | condición | mensaje/diagnóstico |
|---|---|---|
| W1 plan_mom sospechoso | g_plan_mom > 2·g_vc_minimum | "MoM del plan implica {x}×/año — revisar con el cliente antes de usarlo como compromiso" (NO se recorta) |
| W2 plan bajo tesis | g_plan_mom < g_vc_minimum | "el plan consensuado crece bajo la tesis ×3 — el compromiso exigirá acelerar sobre el plan" |
| W3 tesis infeasible | solver Infeasible con commitment on | resultado válido + adjuntar diagnóstico §5 |
| W4 custom sin justificación | source custom y justification vacía | "override experto sin justificación registrada" |
| W5 plan inconsistente | A_base con ceros/huecos que hacen C12≈0 o MoM no computable | "plan consensuado no permite anclar el piso" |

## 5. Rutina de diagnóstico de infactibilidad (determinista, automatizable, sin IA)

Patrón: relajaciones dirigidas una-a-la-vez sobre el mismo build (inyección
post-build ya validada en `growth_band_experiment.py`; precedente en core:
`elastic_floor` + `diagnose_financing_gap`, model.py:396+). Orden fijo, se corre la
secuencia completa y se reporta el CONJUNTO de relajaciones que restauran factibilidad:

| # | relajación (solo esa) | si restaura factibilidad ⇒ diagnóstico |
|---|---|---|
| R1 | hiring: h_v,h_l → +∞ (quitar fricción) | ritmo de contratación/onboarding insuficiente para la tesis |
| R2 | advertising: I_max×10, A_ad_cap×10 (si canal activo) | canal publicitario saturado — tope de gasto/cap limita la tesis |
| R3 | min_shares → 0 | mix comercial rígido — los mínimos por canal impiden el mix necesario |
| R4 | churn ×0.5 (recomputa delta/phi) | retención insuficiente: el stock decae más rápido de lo que se puede adquirir |
| R5 | RRHH y g_adm → 0 (contrafactual) | carga de costo fijo (solo informativo si no hay piso de caja activo) |
| R6 | c_u → 0 | estructura de costo operativo / margen bruto |
| R7 | piso de caja elástico (si liquidity policy activa; patrón elastic_floor) | capital insuficiente — brecha = valor del slack (runway) |
| R8 | el propio piso: multiple_3y → 1.0 | ninguna palanca alcanza: la tesis en sí es el binding (reportar el múltiplo máximo factible por bisección — opcional v2) |

Output `infeasibility_diagnosis.json`: `[{relaxation, feasible, objective?, diagnosis}]`
+ resumen legible. CAC/margen positivo con infeasibilidad ⇒ el diagnóstico distingue
costo fijo (R5), caja (R7), capacidad de adquisición (R1–R3) o churn (R4) — decisión 7
de Alonso. Diseño SaaS-ready: función pura config→JSON.

## 6. Tests EXACTOS (nuevos, branch growth-law-adr14)

```text
test_commitment_off_is_noop            # enabled false ⇒ VAN idéntico a solve sin claves (no golden)
test_commitment_checkpoints_hold       # on ⇒ C24 ≥ (1-slack)·√3·C12 y C36 ≥ (1-slack)·3·C12 (solución)
test_commitment_terminal_only_mode     # checkpoints: terminal ⇒ solo C36 restringido
test_commitment_infeasible_reported    # h=0 + vc_minimum en caso apretado ⇒ Infeasible limpio + W3, sin crash
test_hiring_friction_limits_jump       # V13 ≤ V12 + h_v; L13 ≤ L12 + h_l
test_hiring_off_is_noop
test_parity_det_stoch_first_stage      # mismos params ⇒ mismo V-path y piso activo en plan_total stoch
test_config_validation_commitment      # multiple≤1, source inválido, custom sin g, slack≥1, h<0 ⇒ ValueError
test_suggestions_values                # base.yaml: C12≈55.8, g_vc=73.2%±ε, g_mom=15.8%/mes±ε
test_diagnosis_routine_smoke           # caso infeasible sintético ⇒ JSON con ≥1 relajación feasible y diagnóstico esperado (R1)
```

Suite completa debe seguir verde (161 pass hoy) — commitment/hiring default off ⇒
cero goldens tocados.

## 7. Corridas benchmark requeridas (análisis, sin rebaseline)

1. 4 instancias × {commitment off (hoy), vc_minimum, vc_minimum+hiring h=1}.
2. **kavacomex: AMBOS modos** (decisión Alonso) — `none` para valorizar +
   `vc_minimum` esperando Infeasible → correr rutina §5 completa y tabular QUÉ
   palancas (h, churn, mix, caps) harían factible la tesis ×3 — entender dinámica
   de palancas.
3. Tabla deltas vs targets Excel con explicación por caso (no exigir ±20%).

## 8. Criterios de rebaseline + rollback (sin cambios de REV 1, endurecidos)

Rebaseline SOLO si: deltas benchmark explicados + paridad det/stoch verde +
artefactos válidos + **`final_growth_decision.md` dice APPROVED** (gate humano
explícito, decisión Alonso). Rollback = desactivar claves `growth_commitment`/`hiring`
(default off) o abandonar branch; `entrega-tesis` jamás se toca desde este trabajo.
Si la implementación se pone riesgosa: **detenerse y documentar el blocker** (orden
explícita).

## 9. Alcance Sonnet (autorizado AHORA, restricciones estrictas)

Branch `growth-law-adr14` · opt-in only · defaults off · sin UI · sin refactor amplio
· sin rebaseline automático · paridad det/stoch obligatoria · tests verdes · rollback
= claves off.

Orden de tareas: (1) config schema+validaciones+tests; (2) instance.py: C12, checkpoints,
sugerencias g + artefacto; (3) model.py: bloque commitment+hiring (después del bloque
ceiling, activo solo si enabled); (4) pre-feasibility warning W1–W5 en DD/calibración;
(5) stochastic/model.py: piso sobre plan de primera etapa + fricción en V/L first-stage;
(6) rutina diagnóstico §5 como `scripts/diagnose_infeasibility.py` (función importable,
SaaS-ready); (7) corridas §7 + tabla; (8) ADR 0014 + docs. NO tocar: valuation.py
(congelado), goldens, UI, defaults.

## 10. Checklist revisión Fable post-Sonnet

- [ ] off = no-op bit-a-bit (mismo VAN que HEAD sin claves).
- [ ] Piso stoch en PLANEADO; KPI P(C36_real ≥ 3·C12) reportado ex-post.
- [ ] W1–W5 emiten warning, jamás bloquean; W3 adjunta diagnóstico.
- [ ] kavacomex: ambos modos corridos; tabla de palancas de factibilidad presente.
- [ ] `V ≤ sup·L` intacto; monotonía intacta; sin despidos.
- [ ] Ningún golden ni default tocado; suite completa verde; tiempos (det ≤60s, stoch N=100 ≤420s).
- [ ] ADR 0014 registra: ×3/3años, checkpoints anuales, piso-planeado, infeasible-como-resultado.

## 11. Futuro (fuera de este branch)

Flip de default (post `final_growth_decision.md`); UI de calibración con sugerencias
g; bisección del múltiplo máximo factible (R8 v2); saturación publicitaria cóncava;
recourse/rolling horizon; DD08 drawdown; elicitación distribuciones.

## 12. Decisión

**READY TO IMPLEMENT — autorizado por Alonso (2026-07-05). Sonnet ejecuta §9 ahora.**
Bloqueantes humanos resueltos: benchmark ×3/3años con checkpoints anuales; piso
planeado en stoch; kavacomex ambos modos + análisis de palancas; timing = ahora.
