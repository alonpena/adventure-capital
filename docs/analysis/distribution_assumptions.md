# Supuestos distribucionales del módulo estocástico

Fecha: 2026-07-05 · Código: `stochastic/defaults.py` (M4_DEFAULTS.distributions) ·
Muestreo: LHS sobre triangulares independientes (`scenarios.py`).

## Estado actual — TODAS marcadas "supuesto no validado"

| variable | dist | min | mode | max | media | sesgo vs determinista | fuente |
|---|---|---:|---:|---:|---:|---|---|
| churn_multiplier | triangular | 0.8 | 1.0 | 1.3 | 1.033 | +3.3% churn | **supuesto no validado (asignado por IA)** |
| salesforce_efficiency | triangular | 0.6 | 1.0 | 1.2 | 0.933 | −6.7% productividad | **supuesto no validado (asignado por IA)** |
| advertising_efficiency | triangular | 0.5 | 1.0 | 1.3 | 0.933 | −6.7% | **supuesto no validado (asignado por IA)** |
| third_party_efficiency | triangular | 0.7 | 1.0 | 1.2 | 0.967 | −3.3% | **supuesto no validado (asignado por IA)** |
| wacc_multiplier | triangular | 0.7 | 1.0 | 1.5 | 1.067 | β 35% → media 37.3% | **supuesto no validado (asignado por IA)** |

Efecto compuesto: E[VAN] estocástico ≈ −20% vs VAN determinista por construcción.
Prioridad de elicitación (por dominancia de varianza, ver `stochastic_objective_audit.md`):
salesforce_efficiency ≫ wacc_multiplier ≫ resto.

## Versión A — simétrica (media = 1.0; "el plan del cliente es insesgado")

E[VAN] ≈ VAN determinista; el estocástico informa SOLO dispersión y riesgo de cola.

```python
"distributions": {
    "churn_multiplier":       {"min": 0.8, "mode": 1.0, "max": 1.2},
    "salesforce_efficiency":  {"min": 0.8, "mode": 1.0, "max": 1.2},
    "advertising_efficiency": {"min": 0.8, "mode": 1.0, "max": 1.2},
    "third_party_efficiency": {"min": 0.8, "mode": 1.0, "max": 1.2},
    "wacc_multiplier":        {"min": 0.85, "mode": 1.0, "max": 1.15},
}
```

## Versión B — downside declarado ("el plan del cliente es el MODO optimista")

Mantiene el sesgo actual (o el elicitado) pero se DECLARA en el informe:
"los escenarios asumen que la realidad promedia X% bajo el plan"; titular = P50 con
banda P5–P90, nunca comparar E[VAN] contra VAN determinista sin esa nota.

## Camino correcto (post-lunes)

`STOCHASTIC_DISTRIBUTIONS_JUSTIFICATION.md` ya especifica Beta-PERT por variable con
min/mode/max por elicitación experta. Sesión de 15 min con Maureira fija
salesforce_efficiency y wacc; el resto puede quedar simétrico (impacto < 2% varianza).
Cambio de defaults ⇒ ADR + re-baseline de goldens estocásticos.
