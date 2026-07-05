# Auditoría de función objetivo estocástica

Fecha: 2026-07-05 · Evidencia: `objective_sweep.md` (sweep empírico λ×α),
correlaciones N=1000 (run m8-vc200), ADR 0009/0011. **No se cambia el default sin ADR.**

## Comparación de alternativas

| opción | estado | evidencia / juicio |
|---|---|---|
| A. Determinista + MC/LHS ex-post | **ya existe** — es la Fase B del pipeline (eval N=1000, seed independiente) | no es alternativa al SAA: es su evaluación honesta out-of-sample |
| B. max E[VAN] (λ=1) | probado en sweep | **plan idéntico al actual** — no recupera nada |
| C. mean-CVaR λ=0.5, α=0.15 (default, ADR 0011) | vigente | **empíricamente inerte sobre el plan** (5 combinaciones λ×α → mismo plan de 1ª etapa, misma distribución ex-post). Coherente, tunable, defendible académicamente |
| D. max E[VAN] − ρ·E[funding_gap] | no implementado | lineal, implementable barato; hoy redundante: en caso bien capitalizado gap=0 en todos los escenarios; útil si se baja VC al rango realista ≤100k → candidato a extensión, requiere ADR |
| E. max P(exit ≥ 3× post-money) | no implementado | objetivo de probabilidad ⇒ binarias por escenario (chance constraint) — MILP mucho más caro; **mejor como KPI ex-post**: `P(exit ≥ 3× postmoney)` se calcula gratis en la evaluación (exit y post-money ya están por escenario). Recomendado reportarlo, no optimizarlo |
| F. SAA N=100 train + N=1000 test LHS | **ya es el default** (`saa_scenario_count=100`, `evaluation_scenario_count=1000`, seeds 12345/999) | mantener; diagnóstico de sobreajuste in-sample vs ex-post ya recomendado en ADR 0011 |

## ¿CVaR vuelve el modelo demasiado conservador? — NO (probado)

Las 5 combinaciones (λ ∈ {0,0.5,1} × α ∈ {0.05,0.15,0.30}) sobre el MISMO set SAA
producen plan idéntico (565 adq m13+) y E[VAN]/P5/P50/P(VAN<0) idénticos. Con el freno
de crecimiento activo la primera etapa está en la cota en todo escenario: las
preferencias de riesgo no tienen dónde elegir. La percepción "CVaR conservador" venía
de: (1) caso base descalibrado (VC bajo drawdown → gap en la mayoría de escenarios),
(2) titular comunicando CVaR en vez de P50, (3) distribuciones sesgadas (abajo).

## ¿Distribuciones sesgadas? — SÍ (ver `distribution_assumptions.md`)

Medias de multiplicadores: eficiencias 0.93–0.97, churn 1.03, WACC 1.07 →
E[VAN] ≈ −20% vs determinista POR CONSTRUCCIÓN, antes de cualquier objetivo.

## ¿Qué variables dominan la varianza? (corr con VAN, N=1000)

| variable | corr | corr² (~share de varianza) |
|---|---:|---:|
| **salesforce_efficiency** | **+0.875** | **0.766** |
| **wacc_multiplier** | **−0.463** | **0.215** |
| churn_multiplier | −0.120 | 0.014 |
| third_party_efficiency | +0.051 | 0.003 |
| advertising_efficiency | −0.029 | 0.001 |

Dos variables explican ~98% de la varianza del VAN. Consecuencia práctica: la sesión
de elicitación con Maureira debe gastar el tiempo en **productividad comercial** y
**tasa de descuento**; las demás distribuciones son de segundo orden.

## Recomendación para la tesis

1. **Mantener mean-CVaR (λ=0.5, α=0.15)** como objetivo: teóricamente coherente
   (Rockafellar–Uryasev), y su elección demostrada inocua — argumento FUERTE de
   defensa: "el resultado es robusto a la elección del objetivo".
2. **Titular con P50 y banda P5–P90**; CVaR como métrica de riesgo; agregar KPI
   ex-post `P(exit ≥ 3× post-money)` (opción E como métrica, no objetivo).
3. Opción D queda como extensión futura si se opera con VC en rango realista.
4. Cualquier cambio de default → ADR nuevo (0014+), no antes del lunes.
