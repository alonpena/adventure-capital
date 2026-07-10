# 07 Red Flags And Safe Wording

| Claim riesgoso | Por qué riesgoso | Wording seguro | Evidencia/nota |
|---|---|---|---|
| complete SaaS | no hay auth/DB/jobs/cloud | “MVP local con arquitectura evolutiva” | `END_TO_END_FLOW_CONTEXT.md` |
| fully automated valuation | requiere criterio experto | “valorización reproducible bajo supuestos declarados” | `valuation.py` |
| eliminates bias | no demostrado | “reduce ambigüedad y documenta supuestos” | artefactos |
| total auditability | legal/contable no cubierta | “trazabilidad técnica de inputs y outputs” | `formula_trace.json` |
| robust optimization | no es min-max/DRO | “análisis de robustez / SAA técnico” | ADR 0015 |
| CVaR fully implemented como plan oficial | M4 no es plan oficial | “CVaR/mean-CVaR como artefacto técnico de M4” | `stochastic/model.py` |
| market-calibrated multiples | comparables no provistos | “múltiplos configurables de referencia” | `valuation.py` |
| real-time recalculation | UI local/síncrona | “ejecuciones reproducibles bajo demanda” | `workflow_registry.py` |
| production-ready | faltan operaciones SaaS | “MVP metodológico defendible” | repo docs |
| replaces consultant | contradice DD/human judgment | “asiste al consultor con evidencia” | DD docs |
| AI built thesis | metodológicamente riesgoso | “IA apoyó código/documentación; validación humana” | ver archivo 13 |
| all startup types supported | schema acotado | “modelo parametrizable para casos compatibles” | `config.py` |
| legally valid due diligence | fuera de alcance | “due diligence financiero-operacional preliminar” | `docs/DUE_DILIGENCE.md` |

