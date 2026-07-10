# 14 Modeling Decisions, Trade-Offs And Simplifications

| Decisión | Problema | Alternativa | Decisión | Riesgo | Wording seguro |
|---|---|---|---|---|---|
| Cost floor | costo op no lineal | fijo+variable | max(variable, piso) | simplifica capacidad | “piso operacional por escalón” |
| YAML | inputs dispersos | UI/DB | YAML versionable | UX menos amigable | “fuente reproducible” |
| CBC/PuLP | solver accesible | Gurobi/CPLEX | open-source | performance | “MVP reproducible” |
| DCF EBITDA proxy | FCF detallado no modelado | flujo completo | EBITDA-impuesto | simplificación financiera | “proxy explícito” |
| Múltiplos | comparables faltan | mercado externo | referencia configurable | no market-calibrated | “referencia, no comparable” |
| Growth commitment | crecimiento arbitrario | ceiling exógeno | piso x3 + envelope | depende supuestos | “target trazable” |
| M4 | incertidumbre | robust optimization formal | LHS/SAA/robustez | interpretación compleja | “artefacto técnico” |
| Streamlit | demo rápida | SaaS | UI local artifact-driven | no producción | “consulting tool local” |

Fuentes: ADR 0001-0015, `docs/analysis/final_growth_decision.md`, `docs/analysis/growth_commitment_benchmarks.md`.

