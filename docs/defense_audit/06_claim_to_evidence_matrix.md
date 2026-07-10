# 06 Claim-To-Evidence Matrix

| Claim | Estado | Evidencia | Wording español | Pregunta comité | Respuesta recomendada |
|---|---|---|---|---|---|
| El sistema operacionaliza evaluación experta | seguro | `pipeline.py`, `due_diligence/`, `valuation.py` | “estructura un proceso experto reproducible” | ¿reemplaza al consultor? | No; ordena evidencia y deja decisión al experto. |
| Pipeline reproducible | seguro | `configs/`, `outputs/*/config.yaml`, tests | “mismo YAML reproduce artefactos” | ¿cómo audito? | Revisar config + CSV/JSON + manifest. |
| UI lee artefactos | seguro | `app.py`, `streamlit_pages/components.py` | “UI consume outputs, no es fuente de verdad” | ¿recalcula? | Presentación/consulta; cálculo core vive en módulos backend. |
| DD gates implementados | seguro | `docs/DUE_DILIGENCE.md`, `rules.py` | “DD clasifica riesgos y habilita/bloquea M4” | ¿es due diligence legal? | No, es due diligence financiero/metodológico. |
| EV/VAN calculado | seguro | `valuation.py`, `valuation_summary.json` | “calcula VAN DCF y referencias por múltiplos” | ¿múltiplos mercado? | No salvo evidencia externa; son referencia configurable. |
| Incertidumbre incorporada | cauteloso | `stochastic/`, ADR 0015 | “análisis técnico de robustez con escenarios” | ¿optimización robusta? | No min-max/DRO; es LHS/SAA/CVaR como aproximación. |
| Evolución Colab -> CLI -> UI | seguro | `legacy/`, `README.md`, `cli.py`, `app.py` | “migración desde notebook a pipeline” | ¿notebook sigue core? | No, es legado. |
| Soporta evolución SaaS | cauteloso | `END_TO_END_FLOW_CONTEXT.md` | “arquitectura prepara contratos para evolución” | ¿ya es SaaS? | No; falta auth, DB, jobs, multiusuario. |
| Acelera iteración | cauteloso | CLI/artifacts/tests | “reduce trabajo manual y hace corridas repetibles” | ¿medido? | No hay benchmark temporal formal; decir cualitativo. |
| Juicio humano sigue central | seguro | ADR 0014/0015/DD docs | “la decisión final queda bajo experto” | ¿automatiza inversión? | No. |
| Artefactos trazables | seguro | `formula_trace.json`, `artifacts_manifest.json` | “cada resultado tiene archivo fuente” | ¿total auditabilidad? | Auditabilidad técnica alta, no auditoría legal total. |
| Reportes descargables | seguro | `report.html`, optional PDF code | “HTML generado; PDF si backend disponible” | ¿PDF siempre? | No, depende WeasyPrint. |
| M4 no es plan oficial | seguro | ADR 0015 | “M4 es robustez, no plan oficial” | ¿por qué mostrarlo? | Como stress test de incertidumbre. |

