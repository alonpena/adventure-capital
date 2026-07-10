# Lecturas — dinámicas subyacentes del modelo (clase, no instancia)

Fecha: 2026-07-03. Interpretación de `threshold_analysis.md` y `objective_sweep.md`
(regenerables con `scripts/threshold_analysis.py` y `scripts/objective_sweep.py`).
Esto responde "¿qué recomendaciones generales se pueden dar?" con evidencia, no con
calibración de instancias.

## 1. El crecimiento NO es endógeno en la clase actual — probado

Sin freno externo (ceiling off, convex off) el MILP es **`Unbounded`** (E1). Causa
estructural: margen marginal por cliente positivo y constante (costos ~lineales,
c_u≈0 en benchmarks), canales lineales, y **cero fricción de contratación**. En esta
clase, *algo* tiene que acotar; la discusión correcta es **qué cota tiene significado
de negocio**:

| freno | naturaleza | resultado |
|---|---|---|
| media móvil (`g_max_suavizado`) | tasa; recurrencia geométrica | diverge dentro del MILP (por eso Unbounded era el síntoma); como relato sí captura "naturaleza startup" |
| ceiling log × M (ADR 0010) | nivel; proxy mercado ex-ante | acota, pero M es el driver del valor — objeción válida |
| convex-CAC θ (ADR 0013) | costo marginal creciente | acota solo con θ enorme; sobre-conservador; **documentado como no-funciona para demo** |
| **fricción de contratación `V_t ≤ V_{t-1} + h`** (E4) | **parámetro del negocio** | **Unbounded → Optimal con h=1**; rampa orgánica 2→26 vendedores, VAN 1.9M (h=1) / 3.6M (h=2) |

**Recomendación:** la ley de crecimiento defendible es la fricción de contratación
(+ `commercial_productivity_lag` > 0 para rampa de productividad de vendedores
nuevos). Es auditable ("¿cuántos vendedores puedes contratar y formar por mes?"),
resuelve el salto-y-meseta (contrata todos los meses), y hace el crecimiento función
del modelo comercial, no de un multiplicador de mercado ex-ante. El ceiling queda
como guard-rail de mercado opcional, no como driver. Nota honesta: el VAN escala con
`h` (la cota siempre muerde porque la economía dice "crece"); h es la ambición de
contratación declarada por el cliente — igual que `A_base` año 1 — no un número
nuestro.

## 2. Salto-y-meseta de vendedores — explicado

En las 8 celdas del grid: V da un salto único en mes 13 (2→3/6/9/12 según M) y queda
plano 24 meses. No es bug: sin fricción de contratación el solver salta al máximo que
el ceiling permite y ahí se queda. Con convex-θ alto ni salta (2→2: lo que viste como
"quedamos con los del plan consensuado"). Con `h` (E4) desaparece.

## 3. Umbrales de capital (VC) — la lógica de negocio se sostiene

- Capital realmente requerido = VC + |min caja| ≈ **US$112–113k, casi invariante a VC
  y a M** (el drawdown lo fija la estructura de costos año 1: 12·(g_adm+RRHH₁)=138k
  menos margen bruto año 1).
- El VAN es **lineal en VC** (VAN(VC=50k) = VAN(VC=100k) + 50k, exacto): mientras el
  piso de caja no muerda, el plan óptimo no cambia. Subir VC a 200k ayer fue
  apaciguar la regla DD, no arreglar el modelo — objeción tuya correcta, corregida:
  el caso demo debe declarar VC ≤ ~100–120k y la regla DD debe evaluar drawdown, no
  VC vs costo fijo bruto.
- Con tickets pre-seed realistas (≤100k) el caso base ES financiable si la estructura
  RRHH año 1 baja ~10–20% o el margen año 1 lo cubre.

## 4. "VAN ≥ 1× ingresos año 3" — inalcanzable en esta clase; el benchmark correcto es otro

VAN/Ingresos_Y3 llega a lo sumo a **0.65** (M=12). Causas estructurales: β=35%
mensualizado descuenta ~2.5%/mes, VC se resta, y el horizonte trunca las colas de
recurrencia (ADR 0013). No es la instancia. Dos salidas coherentes con la reunión
del 1-jul:

- El criterio VC de Alejandro **no es sobre el VAN**: es **exit (múltiplo de
  ingresos año 3) ≥ 3× post-money**. Con multiplo 1.5×: exit = 1.78M vs post-money
  ~0.6M → ratio ~3 ✓. Ese sí es alcanzable y ya está calculado en
  `multiples_valuation.csv`. Úsalo como titular; el VAN DCF queda como piso
  conservador.
- Si igual quieres VAN≈ingresos: β 30% (reunión) + valor de desecho bien poblado +
  tail de recurrencia post-horizonte. Cada uno mueve el ratio ~0.1–0.2.

## 5. Estocástico: el objetivo NO es el problema — probado

Las 5 combinaciones (λ ∈ {0, 0.5, 1} × α ∈ {0.05, 0.15, 0.30}) producen **el mismo
plan de primera etapa (565 adq m13+) y la misma distribución ex-post** (E[VAN]
367,763; P5 115,045; P(VAN<0) 0.5%). Con el freno de crecimiento activo, la primera
etapa está en la cota para todo escenario → las preferencias de riesgo no tienen
dónde elegir. Cambiar CVaR por E[VAN] o por Monte Carlo puro no movería un dólar.

**La conservadurización real está en las distribuciones** (`stochastic/defaults.py`),
que tienen sesgo downside incorporado y **fueron asignadas sin respaldo empírico**:

| multiplicador | media | efecto |
|---|---:|---|
| salesforce_efficiency | 0.933 | −7% clientes esperados |
| advertising_efficiency | 0.933 | −7% |
| churn_multiplier | 1.033 | +3% churn |
| wacc_multiplier | 1.067 | β 35% → media 37.3% |

Decisión metodológica (tuya, no mía): (a) **simetrizarlas** (media = 1.0) → E[VAN] ≈
VAN determinista y el estocástico solo informa dispersión; o (b) mantener sesgo pero
**declararlo** ("el plan del cliente es el modo; la media de la realidad es peor") y
titular con P50 + banda P5–P90. El doc `STOCHASTIC_DISTRIBUTIONS_JUSTIFICATION.md`
ya propone Beta-PERT con parámetros por elicitación — con Alejandro es una sesión de
15 min fijar min/mode/max defendibles por variable.

## 6. CVaR en una frase (para la defensa)

CVaR_α(VAN) = promedio del VAN en el α% peor de los escenarios. No es el peor caso
(eso es min-max); es "si nos toca la cola mala, ¿cuánto vale en promedio?". Con
λ=0.5 el objetivo pondera mitad valor esperado, mitad cola mala. Y por §5, en este
modelo su elección es empíricamente inocua: se reporta como métrica de riesgo, no
gobierna el plan.
