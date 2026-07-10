# Auditoría de reglas Due Diligence

Fecha: 2026-07-05 · Código: `src/adventure_capital/due_diligence/rules.py`,
`calibration/checks.py`, `configs/due_diligence.yaml` · ADR 0005/0009.
Tipos: **T** = consistencia técnica · **F** = plausibilidad financiera · **VC** = tesis venture.

## Matriz de reglas DD (propias)

| id | nombre | fórmula / condición | severidad actual | tipo | fuente | recomendación |
|---|---|---|---|---|---|---|
| DD01 | instance_valid | `validate_config` sin excepción | structural | T | esquema config | **bloquear** (correcto) |
| DD02 | unit_margin_positive | `ticket > c_u` por servicio | structural | T | economía unitaria computable | **bloquear** (correcto) |
| DD03 | financing_present | `VC > 0`, salvo `operating_company: true` → warning | structural / warning | F | reunión 2026-07-01 + fix 2026-07-03 | **bloquear con exención** (implementado; godemos ya se valoriza) |
| DD04 | churn_valid | `churn_anual ∈ [0,1]` | structural | T | definición | **bloquear** (correcto) |
| DD05 | churn_severity | max churn ≥ 0.95 → major; ≥ 0.60 → warning | major/warning | F | umbral experto | mantener; 0.60 discutible para servicios de baja frecuencia — **umbral configurable, ya lo es** |
| DD06 | breakeven_within_horizon | EBITDA acum ≥ 0; nunca → major; mes > 24 → warning | major/warning | VC | "plan auditable con punto de equilibrio" (Maureira) | mantener |
| DD07 | runway | caja < 0 en mes ≤ 6 → minor; después → warning | minor/warning | F | diagnóstico liquidez | mantener (nunca bloquea — correcto) |
| DD08 | funding_gap_severity | gap/VC ≥ 5 → minor; ≥ 0.5 → warning | minor/warning | F | diagnóstico | **cambiar base**: comparar contra **drawdown** (capital requerido real), no contra VC — VAN es lineal en VC y el gap/VC castiga tickets chicos legítimos (≤100k) |
| DD09 | ebitda_regime_by_year3 | EBITDA anual año 3 > 0 | major | VC | régimen de rentabilidad | mantener |
| DD10 | revenue_growth | ingresos último/primer año ≥ 1.5× | major | VC | perfil venture vs PYME | mantener; umbral configurable |
| DD11 | working_capital_financing_gap | gap sobre ticket cuando WC habilitado | minor | F | diagnóstico WC | mantener |
| DD12 | exit_roi | exit (mult. ingresos Y3) ≥ 3× post-money mín = max(VAN,0)+VC | warning | VC | regla 3× VC (reunión 2026-07-01; big-tech 3y) | mantener **warning, nunca estructural** (implementado 2026-07-03) |

## Reglas heredadas de Calibration (mapeadas, no duplicadas)

| id | nombre | tipo | severidad DD | nota |
|---|---|---|---|---|
| C01 | solver_status | T | **structural** (blocking_ids) | correcto: sin solución no hay nada que leer |
| C02 | seller_capacity_saturation | T | minor/warning | |
| C03 | sellers_no_growth_with_saturation | T | minor/warning | detecta el salto-meseta como síntoma |
| C04 | cash_floor | F | minor/warning | |
| C05 | total_ebitda | F | minor/warning | |
| C06 | npv | F | minor/warning | |
| C07 | gross_margin | F | minor/warning | benchmarks reales lo pasan trivialmente (margen 73–99.9%) |
| C08 | ltv_cac | F | minor/warning | ídem (25–80×) — umbral poco informativo con costos blended |
| C09 | mix_concentration | F | minor/warning | |
| C10 | retention | F | minor/warning | |
| C11 | document_completeness | T | minor/warning | |

## Pregunta central: ¿modelo de negocio malo o reglas demasiado restrictivas?

**Ninguna de las dos — era una regla mal basada + un caso base descalibrado.** Evidencia:

1. Las 4 instancias reales HOY: godemos `requires_minor_adjustment` (antes: rechazada
   por DD03 — regla, no negocio), entrena `passed_with_warnings`, kava/beloop corren
   M1–M3. Con la exención DD03, **ninguna instancia real queda bloqueada**.
2. El grid E2: el caso base con M=3 caía en DD09/DD10 por freno de crecimiento, no por
   reglas duras — con M=8 el mismo negocio pasa con warnings. Las reglas VC (DD06/09/10/12)
   miden lo que un VC mide; cuando fallan, el caso realmente no es venture-grade *bajo
   ese freno*.
3. El único ajuste de severidad recomendado: **DD08 debe medir drawdown, no gap/VC**
   (ver matriz). Todo lo demás distingue correctamente bloquear (T estructural) /
   advertir (F) / informar (diagnóstico liquidez).

Test de la distinción warning vs bloqueo: `tests/test_due_diligence.py::test_m4_gate_policy_all_verdicts`
(+ `test_dd03_*`, `test_exit_roi_*`).
