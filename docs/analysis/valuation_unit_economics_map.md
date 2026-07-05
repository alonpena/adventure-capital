# Mapa de valorización y unit economics (caja negra abierta)

Fecha: 2026-07-05 · Fuentes: `model.py`, `valuation.py` (`calculate_dcf`,
`calculate_multiples_valuation`), `unit_economics.py`, `results.py`,
`due_diligence/rules.py`. Unidades: USD y meses salvo indicación.
Verificación aritmética (run m8-vc200): VAN 459,694 = vp_flujos 386,288 +
vr_pv 273,406 − VC 200,000 ✓.

| métrica | fórmula | archivo | input YAML | output | lectura financiera |
|---|---|---|---|---|---|
| Clientes activos | `C_{s,t} = Σ_cohortes δ·φ (supervivencia churn) · A_{s,cohorte}` | model.py (delta/phi precomputados en instance.py) | `A_base`, `churn_anual` | optimized_results.csv `Clientes_activos` | base instalada que genera recurrencia |
| Servicios totales | `Q_{s,t} = A_{s,t} + R_{s,t}` (nuevos + recurrentes) | model.py:231 | `frecuencia`, `alpha` | `Servicios_totales` | volumen vendido del período |
| Ventas recurrentes | `R_{s,t} = Σ_cohortes δ·φ·α·A` en ventana de recompra | model.py:224-230 | `alpha`, `frecuencia` | `Ventas_recurrentes` | ingreso que no requiere CAC nuevo |
| Ingresos | `I_{s,t} = ticket_s · Q_{s,t}` | model.py:232 | `ticket` | `Ingresos`; dcf_annual `Ingresos` | línea de ventas |
| Costo operacional | `≥ c_u·Q` y `≥ c_min·escalones`; escalones: `Q ≤ u_max·n` | model.py:233-235 | `c_u`, `c_min`, `u_max` | `Costo_operacional` | costo variable con piso por capacidad (ADR 0001) |
| Gross profit unitario | `Σ_s (ticket−c_u)·(12/freq)` /cliente-año | unit_economics.py:32 | ticket, c_u, frecuencia | unit_economics.csv | margen antes de adquisición |
| CAC fuerza de ventas | `rem_v·V + rem_l·L + (com_v+com_l)·ticket·ventas_sf` | model.py:256-263 | `rem_v/rem_l/com_v/com_l` | `salesforce_cac_cost` | costo del canal directo |
| CAC publicidad | `I_ad` con recta `A_ad = a + b·I_ad` (ADR 0006) | model.py (bloque ad) | channels.advertising | `advertising_cac_cost` | canal continuo |
| CAC terceros | `commission·ticket·A_tp` (ventana comisión) | model.py:264-269 | channels.third_party | `third_party_cost` | canal por comisión |
| CAC total | suma de los 3 canales | model.py:270-276 | — | `CAC`, `total_acquisition_cost` | inversión en crecimiento (la que Maureira "suma de vuelta" para comparar con empresa tradicional) |
| CAC por cliente (anual) | `Σ CAC / Σ nuevos clientes` | unit_economics.py:48 | — | `cac_per_customer` | costo de adquirir uno |
| G. administración | constante `g_adm` /mes | model.py:282 | `g_adm` | `G_adm` | estructura |
| RRHH | escalera anual `RRHH_mensual[año]` | model.py:283 | `RRHH_mensual` | `RRHH` | costo comprometido — define umbral VC* = 12·(g_adm+RRHH₁) |
| EBITDA | `I − Costo_op − CAC − sat − g_adm − RRHH` | model.py:277-284 | — | `EBITDA` | resultado operativo |
| Caja | `Caja_1 = VC + EBITDA_1`; `Caja_t = Caja_{t-1} + EBITDA_t` | model.py:291-294 | `VC` | `Caja` | piso −VC (working capital) |
| Capital requerido | `VC + |min_t Caja_t|` (drawdown) | scripts/threshold_analysis.py | — | threshold_grid.csv `min_cash` | el "dinero" de las 3 dimensiones del capital de trabajo (clientes/tiempo/dinero) |
| Impuesto | `≥ tax·EBITDA, ≥ 0` (lineal) | model.py:345 | `tax` | dcf `Impuesto` | simplificación declarada |
| FC descontado | `FC_neto / (1+β_m)^t`, `β_m = (1+β)^{1/12}−1` | valuation.py | `beta` | `FC_desc` | β=0.35 actual; reunión sugiere 0.30 |
| Valor residual (desecho) | `1× EBITDA anualizado último mes`, descontado a t=H (ADR 0012) | valuation.py:100-103 | `parametros.terminal…` | `vr_nominal`, `vr_pv` | cola post-horizonte conservadora |
| **VAN** | `−VC + Σ FC_desc + VR_vp` | valuation.py:105 | — | summary.json `van` | pre-money por DCF; **lineal en VC** (probado) |
| Post-money mínimo | `max(VAN,0) + VC` | due_diligence/rules.py (DD12) | — | due_diligence_report | piso de negociación (reunión 2026-07-01) |
| **Exit** | `mult_ingresos · Ingresos_año3` (default 1.5×) | valuation.py:140-180 | `parametros.mult_ingresos` | multiples_valuation.csv | valor hipotético año 3; DD12 exige ≥ 3× post-money |
| LTV | `Σ_s ticket·(12/freq)·gm / churn_anual₁` | unit_economics.py:37 | ticket, c_u, churn | `annual_ltv` | valor de vida del cliente (anualizado) |
| LTV/CAC | `LTV / CAC_por_cliente` | unit_economics.py:75 | — | `ltv_cac` | calidad de adquisición; C08 |
| ARPU | ingresos período / clientes activos | results.py | — | `arpu` (stochastic + UE csv) | ticket efectivo |
| ARR (proxy) | ingresos recurrentes / ingresos totales | results.py | — | `ARR_pct` | recurrencia del negocio |
| Breakeven (clientes) | `costos fijos año1 / contribución` con `contribución = GP − CAC` | unit_economics.py:82-83 | — | `breakeven_customers` | los "cuántos clientes" |
| Breakeven (mes) | primer t con EBITDA acumulado ≥ 0 | rules.py:287-289 | — | DD06, liquidity | los "cuánto tiempo" |
| Payback | mes con `Caja ≥ VC` (ticket recuperado); clientes `VC/contribución` | unit_economics.py:85-87 | — | `payback_month` | recuperación del ticket |
| Runway | meses de caja restantes a burn corriente | unit_economics.py:58 | — | `runway_months` | supervivencia |

Nota UI: la UI **no** recalcula nada de esto (ADR 0007) — lee estos artefactos.
El informe HTML muestra las definiciones en el Anexo metodológico (fórmulas movidas
del cuerpo el 2026-07-02).
