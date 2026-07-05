# SAA here-and-now — formulación final para la tesis

Fecha: 2026-07-05 · Código: `stochastic/{scenarios,model,evaluate,results}.py` ·
ADR 0004/0009/0011 · Evidencia: `objective_sweep.md` + timings de hoy.

## Formulación (lo que se defiende el lunes)

```text
Escenario s:      ξ_s = (churn_mult, sf_eff, ad_eff, tp_eff, wacc_mult) ~ LHS
                  sobre triangulares independientes; probabilidad p_s = 1/N.

Primera etapa     x = plan comercial único here-and-now:
(no anticipativa) A_plan[c,s,t] por canal, V_t, L_t, I_ad_t   (meses 13..H)

Segunda etapa:    y_s = escalones operativos, ingresos, EBITDA, caja, VAN_s
(recourse)        dado x y ξ_s (adquisición realizada = eficiencia_s · plan).

Objetivo:         max  λ·Σ p_s·VAN_s + (1−λ)·CVaR_α(VAN)      [λ=1 ⇒ max E[VAN] puro]

Validación:       out-of-sample — la estrategia x* se evalúa en N_test escenarios
                  LHS INDEPENDIENTES (seed distinta) ⇒ distribución honesta del VAN.
```

Todo esto YA está implementado; `max E[VAN]` es el caso `mean_cvar_lambda: 1.0`
(clave de config, sin tocar código).

## Factibilidad computacional (medida hoy, caso-base-1m, CBC)

| N_train | solve | eval N=500 | E[VAN] ex-post | P5 |
|---:|---:|---:|---:|---:|
| 20 | 11.7 s | 1.1 s | 369,166 | 103,446 |
| 50 | 10.6 s | 0.9 s | 369,166 | 103,446 |
| 100 | 27.6 s | 0.4 s | 369,166 | 103,446 |

- Prototipable sin romper core: solo claves `stochastic:` del YAML.
- Plan ex-post IDÉNTICO para N=20/50/100 y para todo (λ,α) probado
  (`objective_sweep.md`): con el freno de crecimiento activo la primera etapa está
  en la cota en todos los escenarios ⇒ el problema es casi de evaluación, no de
  optimización bajo riesgo. Defensa: "resultado robusto al objetivo y al tamaño
  muestral SAA".

## Comparación

| enfoque | juicio |
|---|---|
| Determinista + LHS ex-post | = evaluar el plan determinista en escenarios; más simple, pero el plan no considera incertidumbre ex-ante. Diferencia práctica hoy ≈ 0 (plan en la cota), diferencia conceptual importa para la tesis |
| **max E[VAN] (λ=1)** | formulación académica limpia pedida; **recomendada como formulación de presentación** — y demostrado que coincide con la actual |
| mean-CVaR λ=0.5 (default) | mantiene métrica de riesgo en el objetivo; inerte en la práctica; NO cambiar default sin ADR — no hace falta: λ es config |
| Chance constraints / P(exit≥3×) | binarias por escenario, caro; queda como métrica ex-post y extensión |

## Recomendación

Presentar la formulación como **SAA here-and-now con objetivo mean-riesgo
paramétrico** (λ=1 caso neutral, λ<1 aversión): cubre lo que pide el comité Y lo
implementado, con la inercia empírica como resultado de robustez. Out-of-sample
LHS N=1000 ya es el default del pipeline.
