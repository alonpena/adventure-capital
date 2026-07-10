# Slide 11 — Crecimiento target-driven

Tiempo: 1:10.

Bullets:
- Tesis: triplicar stock de clientes entre mes 12 y mes 36 por defecto.
- `growth_commitment` es piso; `acquisition_envelope` es camino superior trazable.
- VAN y MoM son consecuencias del plan, no parámetros calibrados.
- Infeasible puede ser diagnóstico de negocio, no bug.

Visual recomendado: curva stock clientes con C12, C24, C36.

Speaker notes: “La diferencia clave frente a un ceiling arbitrario es trazabilidad: plan consensuado + tesis VC + churn + slack declarado.”

Evidencia: ADR 0014, `docs/analysis/final_growth_decision.md`, `tests/test_acquisition_envelope.py`.

