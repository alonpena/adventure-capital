# Slide 07 — Metodología propuesta

Tiempo: 1:00.

Bullets:
- YAML declara supuestos: servicios, costos, canales, inversión, tesis.
- Preprocesamiento genera cohortes, churn, recurrencia y descuento.
- MILP optimiza plan de crecimiento bajo restricciones operacionales.
- Post-solve calcula VAN, múltiplos de referencia y unit economics.

Visual recomendado: diagrama pipeline de 5 bloques.

Speaker notes: “El solver no inventa supuestos; busca el plan factible/óptimo bajo supuestos declarados.”

Evidencia: `config.py`, `instance.py`, `model.py`, `valuation.py`, `unit_economics.py`.

