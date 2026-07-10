# FINAL COMMITTEE Q&A — Defensa Adventure Capital

Formato: pregunta → respuesta corta (decir) → respaldo (si profundizan) → evidencia.

---

## Bloque A — Alcance y propósito

**A1. ¿Esto reemplaza al consultor/evaluador?**
No. Estructura y hace trazable el juicio experto: estandariza cálculos, evidencia y alertas; la decisión queda bajo el experto.
Respaldo: el diseño lo refuerza — DD emite veredictos y recomendaciones, no decisiones de inversión; `docs/adr/0014-growth-commitment-hiring-friction.md` y `docs/adr/0015-m4-mvp-robustness-diagnostic.md` mantienen el juicio humano como ancla.
Evidencia: `docs/DUE_DILIGENCE.md`, `docs/adr/0014-growth-commitment-hiring-friction.md`, `docs/adr/0015-m4-mvp-robustness-diagnostic.md`.

**A2. ¿Es un SaaS?**
No; es un MVP metodológico local con arquitectura evolutiva. SaaS exige autenticación, base de datos, colas y operación cloud; documentado como roadmap.
Evidencia: `docs/END_TO_END_FLOW_CONTEXT.md`.

**A3. ¿Es due diligence "de verdad"?**
Es due diligence financiero-metodológica cuantitativa: calidad de inputs, coherencia de outputs, calibración y liquidez. No cubre legal ni comercial, y eso está declarado.
Evidencia: `docs/DUE_DILIGENCE.md`, slide 10.

**A4. ¿Qué tipo de startups soporta?**
Casos compatibles con el schema: servicios con ticket, recurrencia, churn y canales de adquisición parametrizables. No afirmo cobertura universal.
Evidencia: `src/adventure_capital/config.py`, `configs/*.yaml`.

## Bloque B — Modelo y optimización

**B1. ¿Por qué MILP?**
El plan mezcla decisiones discretas y continuas bajo restricciones de caja, capacidad y crecimiento. MILP entrega optimalidad verificable y diagnóstico de infactibilidad, que aquí es información de negocio.
Evidencia: `src/adventure_capital/model.py`, `tests/test_phase2.py`.

**B2. ¿Qué significa target-driven y por qué se cambió al final?**
La tesis de inversión fija el crecimiento objetivo (por defecto C36 ≥ 3·C12); el optimizador busca ejecución eficiente y factible. Se cambió porque la revisión final detectó que, con margen positivo, el modelo podía sobre-expandir adquisición: crecimiento especulativo sin ancla en tesis. La corrección fortalece la estandarización.
Evidencia: `docs/adr/0014-growth-commitment-hiring-friction.md`, `docs/analysis/final_growth_decision.md`, `tests/test_acquisition_envelope.py`.

**B3. ¿Por qué el optimizador no decide el crecimiento si tiene la información?**
Porque la ambición de crecimiento es un juicio de inversión, no un output del solver. El solver aporta factibilidad y eficiencia de capital dentro del envelope declarado.
Evidencia: `docs/adr/0014-growth-commitment-hiring-friction.md`.

**B4. ¿Qué pasa si el modelo es infeasible?**
Se reporta como diagnóstico: la tesis de crecimiento no se sostiene con los supuestos declarados. Es un resultado útil, no un error del sistema.
Evidencia: `docs/adr/0014-growth-commitment-hiring-friction.md`, DD reports con `requires_major_adjustment`.

**B5. ¿El VAN está calibrado? ¿Es realista?**
Es internamente consistente y trazable a supuestos declarados. El sistema no valida mercado; el gate de DD y el juicio experto cubren la interpretación. Los múltiplos son referencias configurables, no comparables de mercado.
Evidencia: `valuation.py`, `valuation_summary.json`, `07_red_flags_and_safe_wording.md`.

## Bloque C — Incertidumbre y robustez

**C1. ¿Hicieron optimización robusta?**
No en el sentido formal (min-max/DRO). M4 es análisis de robustez: escenarios LHS, SAA y CVaR como artefactos técnicos. M4 evalúa robustez, no define el plan oficial.
Evidencia: `docs/adr/0015-m4-mvp-robustness-diagnostic.md`, `src/adventure_capital/stochastic/`.

**C2. ¿Por qué el plan oficial no es el estocástico?**
Decisión metodológica documentada: el MVP fija una tesis determinista target-driven; M4 sirve para stress-testing. Adoptar la solución SAA como plan exigiría recourse y calibración de distribuciones que exceden el alcance.
Evidencia: `docs/adr/0015-m4-mvp-robustness-diagnostic.md`.

**C3. ¿Qué pasa si DD bloquea M4?**
El bloqueo es diseño: no se interpreta riesgo estocástico sobre un caso que exige recalibración. Se reporta el estado y las recomendaciones.
Evidencia: run `bench_godemos` con veredicto `rejected_for_stochastic` (`outputs/executions/run_20260701-115219_4a35e749/`).

## Bloque D — Validación y resultados

**D1. ¿Qué pruebas existen?**
`uv run pytest -q`: 186 passed, 3 skipped. Cubren modelo, valorización, DD, contratos de artefactos y envelope de crecimiento.
Evidencia: `tests/`, `17_presentation_evidence_pack.md`.

**D2. ¿Cuatro casos de benchmark bastan?**
Bastan para demostrar comportamiento y discriminación (VAN positivo con warnings vs VAN negativo con ajuste mayor); no afirmo validación estadística. Limitación declarada y parte del roadmap.
Evidencia: `docs/analysis/growth_commitment_benchmarks.md`.

**D3. ¿Dónde está el resultado final (gold)?**
Si existe al momento de la defensa: `outputs/executions/run_20260706-045427_28a63258`. Si no: "La estructura está preparada y hay ejecuciones históricas completas; el caso gold final se designa con el profesor guía y se genera con un comando reproducible."
Evidencia: `outputs/executions/`, `FINAL_PLACEHOLDERS_TO_FILL.md`.

**D4. ¿Hay datos reales?**
Hay configuraciones de casos reales de benchmark (godemos, beloop, entrena-en-casa, kavacomex) y ejecuciones completas. Los supuestos provienen del método del mandante; no hay integración con fuentes de mercado en vivo.
Evidencia: `benchmark_v0/`, `outputs/executions/`.

**D5. ¿Qué falla hoy?**
Ruff reporta 9 issues de lint preexistentes (no corregidos por restricción docs-only en la rama de defensa); el PDF del reporte depende de WeasyPrint instalado. Nada de eso afecta resultados del modelo.
Evidencia: `17_presentation_evidence_pack.md`.

## Bloque E — Proceso y herramientas

**E1. ¿Qué rol tuvo la IA en la tesis?**
Apoyó desarrollo, depuración y documentación. Las decisiones metodológicas, el alcance y la validación final permanecen bajo responsabilidad humana, documentadas en ADRs.
Evidencia: `13_ai_tools_and_agent_coordination.md`, `docs/adr/`.

**E2. ¿Por qué YAML y no una base de datos o formulario?**
YAML deja los supuestos legibles, versionables con git y reproducibles; el pipeline es reproducible desde YAML. DB llega con la evolución SaaS.
Evidencia: `configs/`, `config.py`.

**E3. ¿Cuánto tiempo ahorra frente al proceso manual?**
No hay benchmark temporal formal; el beneficio medible es reproducibilidad y trazabilidad: la misma configuración regenera el análisis completo sin trabajo manual. Afirmación cualitativa, declarada como tal.
Evidencia: `06_claim_to_evidence_matrix.md` (claim "acelera iteración": cauteloso).

## Top 5 riesgos de defensa (resumen ejecutivo)

| # | Riesgo | Respuesta segura |
|---|---|---|
| 1 | Comité asume que "resuelve la valorización" | "Valorización reproducible bajo supuestos declarados; interpretación bajo DD y juicio experto." |
| 2 | Gold run ausente al momento de defensa | Tener corrida gold generada antes; si no, mostrar ejecución histórica completa y explicar designación pendiente. |
| 3 | "¿Por qué cambió el modelo al final?" leído como error | Encuadrar como corrección que fortalece estandarización: impide crecimiento especulativo del solver (ADR 0014 Amendment 1). |
| 4 | Confusión M4 = plan oficial | Repetir framing ADR 0015: "M4 evalúa robustez, no define el plan oficial." |
| 5 | "Cuatro benchmarks no validan nada" | Conceder el límite: identifican brechas y soportan calibración; el aporte es la capacidad de discriminación demostrada. |
