# 04 Valuation And Risk Audit

## Modelo Determinista

| Bloque | Implementación | Evidencia |
|---|---|---|
| adquisición | `A[s,t]`, meses 1-12 fijos, 13-H optimizados | `model.py`, `instance.py` |
| stock clientes | supervivencia por cohorte `phi` | `instance.generate_instance()` |
| recurrencia | ventana `delta` + `alpha` | `instance.py`, `results.py` |
| ingresos | `ticket * Q[s,t]` | `model.py` |
| CAC | sueldos, comisiones, advertising, third-party | `model.py`, `results.py` |
| costos op | max(variable, piso capacidad) | ADR 0001, `model.py` |
| RRHH/admin | parámetros mensuales | `config.py`, `model.py` |
| caja | acumulada desde `VC + EBITDA` | `model.py` |
| growth commitment | piso target-driven sobre stock | ADR 0014, `model.py` |
| acquisition envelope | cota superior trazable al plan/tesis/churn | ADR 0014, `instance.py`, `model.py` |

## Fórmulas Slide-Ready

| Concepto | Fórmula defensa | Nota |
|---|---|---|
| Clientes activos | `C[s,t] = Σ phi[s,c,t] * A[s,c]` | cohortes por servicio |
| Servicios vendidos | `Q[s,t] = A[s,t] + R[s,t]` | nuevos + recurrentes |
| Ingresos | `I[s,t] = ticket[s] * Q[s,t]` | ticket constante por servicio |
| EBITDA | ingresos - costos op - CAC - admin - RRHH | pre-tax operativo |
| VAN | `-VC + Σ FC_neto descontado + valor terminal VP` | `valuation.py` |
| Growth floor | `C36 >= multiple * C12` | target-driven, VC x3 por defecto |
| Envelope | `Σ A[s,t] <= U_t` | trazable a plan/tesis/churn |

## Riesgo / M4

M4 implementa LHS, escenarios, SAA y métricas de distribución. Por ADR 0015 debe presentarse como análisis de robustez del MVP, no como plan oficial.

Wording seguro: “El plan oficial del MVP es determinista y target-driven; M4 entrega una primera aproximación de robustez bajo incertidumbre.”

