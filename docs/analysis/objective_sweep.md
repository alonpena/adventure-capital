# Sweep de función objetivo estocástica

Seed: `configs/caso-base-1m.yaml` · SAA N=40 (seed fija: mismo set de escenarios) · ex-post N=200 independiente · `scripts/objective_sweep.py`

## Auditoría de distribuciones (triangulares actuales, defaults.py)

| multiplicador | min | modo | max | **media** |
|---|---:|---:|---:|---:|
| churn_multiplier | 0.8 | 1.0 | 1.3 | **1.033** |
| salesforce_efficiency | 0.6 | 1.0 | 1.2 | **0.933** |
| advertising_efficiency | 0.5 | 1.0 | 1.3 | **0.933** |
| third_party_efficiency | 0.7 | 1.0 | 1.2 | **0.967** |
| wacc_multiplier | 0.7 | 1.0 | 1.5 | **1.067** |

Media ≠ 1.0 = sesgo incorporado del generador de escenarios (optimismo del plan
del cliente vs realidad promedio). Esto — no el CVaR — desplaza E[VAN] respecto
del VAN determinista.

## Resultados por objetivo  (max λ·E[VAN] + (1−λ)·CVaR_α)

| α | λ | status | E[VAN] ex-post | P5 | P50 | CVaR_α ex-post | P(VAN<0) | adquisición plan m13+ |
|---:|---:|---|---:|---:|---:|---:|---:|---:|
| 0.15 | 0.0 | Optimal | 367,763 | 115,045 | 374,689 | 132,645 | 0.5% | 565 |
| 0.15 | 0.5 | Optimal | 367,763 | 115,045 | 374,689 | 132,645 | 0.5% | 565 |
| 0.15 | 1.0 | Optimal | 367,763 | 115,045 | 374,689 | 132,645 | 0.5% | 565 |
| 0.05 | 0.5 | Optimal | 367,763 | 115,045 | 374,689 | 54,391 | 0.5% | 565 |
| 0.3 | 0.5 | Optimal | 367,763 | 115,045 | 374,689 | 186,455 | 0.5% | 565 |
