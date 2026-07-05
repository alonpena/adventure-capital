# Growth commitment + hiring — benchmark runs (ADR 0014)

4 instancias `benchmark_v0/*.yaml` x {off, vc_minimum, vc_minimum+hiring h=1}. kavacomex corre además `none` (bottom-up puro) y la rutina completa de diagnóstico R1-R8. Targets = los declarados en el propio YAML (ver `YAML_EXTRACTION_SUMMARY.md`, tolerancia ±20% documentada por el founder, no exigida aquí como gate — se explica el delta por caso).

`vc_minimum`: `growth_commitment.enabled=true, source=vc_minimum, multiple_3y=3.0, checkpoints=annual` (C24>=sqrt(3)*C12, C36>=3*C12) significa: **triplicar el stock de clientes entre el fin del año 1 consensuado (mes 12) y el fin del año 3 (mes 36)**. El log ceiling (ADR 0010, default-on x3/slack 0.15) queda activo en todos los modos de la tabla principal — nunca se sube su multiplicador como parte de esta feature (corrección Alonso: el x8/el ceiling no es core; el piso debe funcionar con el ceiling desactivado, ver sección de contraste abajo). `vc_minimum+hire`: además `hiring.enabled=true, h_v=h_l=1`.

**Columna `piso` (binding check)**: indica si el checkpoint del compromiso (C24/C36) es la restricción activa (`binding`, el stock queda pegado al piso) o si el plan ya lo supera por otras razones (`holgado`, con margen).

| instancia | modo | status | VAN | Δ vs target VAN | Ing Y1 | Ing Y3 | stock m12/m24/m36 | piso | min caja |
|---|---|---|---:|---:|---:|---:|---|---|---:|
| godemos | off | Optimal | 1,178,372 | -41% | 172,392 | 1,330,510 | 309/895/1,079 | n/a (piso off) | -26,478 |
| godemos | vc_minimum | Optimal | 1,178,372 | -41% | 172,392 | 1,330,510 | 309/895/1,079 | m24 holgado / m36 holgado | -26,478 |
| godemos | vc_minimum+hire h=1 | Optimal | 1,071,941 | -47% | 172,392 | 1,151,667 | 309/738/962 | m24 holgado / m36 holgado | -26,478 |
| entrena-en-casa | off | Optimal | 34,331 | -98% | 75,235 | 397,804 | 86/241/282 | n/a (piso off) | 12,620 |
| entrena-en-casa | vc_minimum | Optimal | 34,331 | -98% | 75,235 | 397,804 | 86/241/282 | m24 holgado / m36 holgado | 12,620 |
| entrena-en-casa | vc_minimum+hire h=1 | Optimal | 34,331 | -98% | 75,235 | 397,804 | 86/241/282 | m24 holgado / m36 holgado | 12,620 |
| beloop | off | Optimal | 3,157,381 | +64% | 238,597 | 3,657,384 | 55/159/188 | n/a (piso off) | 181,668 |
| beloop | vc_minimum | Optimal | 3,157,381 | +64% | 238,597 | 3,657,384 | 55/159/188 | m24 holgado / m36 holgado | 181,668 |
| beloop | vc_minimum+hire h=1 | Optimal | 2,809,193 | +46% | 238,597 | 3,337,449 | 55/146/175 | m24 holgado / m36 holgado | 181,668 |
| kavacomex | off | Optimal | -378,136 | -121% | 46,608 | 254,250 | 92/256/300 | n/a (piso off) | -165,618 |
| kavacomex | vc_minimum | Optimal | -378,136 | -121% | 46,608 | 254,250 | 92/256/300 | m24 holgado / m36 holgado | -165,618 |
| kavacomex | vc_minimum+hire h=1 | Optimal | -378,136 | -121% | 46,608 | 254,250 | 92/256/300 | m24 holgado / m36 holgado | -165,618 |
| kavacomex | none (bottom-up) | Optimal | -378,136 | -121% | 46,608 | 254,250 | 92/256/300 | n/a (piso off) | -165,618 |

## Hallazgo principal: `off` == `vc_minimum` en las 4 instancias

Ninguna de las 4 instancias muestra diferencia entre `off` y `vc_minimum` en la tabla de arriba (columna `piso` = `holgado` en todos los casos). Causa: el log ceiling por defecto (ADR 0010, `target_stock_multiplier=3.0`, `slack=0.15`, activo en TODOS los modos salvo el contraste explícito de abajo) ya produce, por sí solo, un stock que supera holgadamente el piso del compromiso: en las 4 instancias el ratio `off` natural es ~2.4-2.9x en m24 (> el umbral sqrt(3)~=1.73x) y ~3.1-3.5x en m36 (> el umbral 3.0x), incluso con `hiring h=1`. El compromiso (`growth_commitment`) es matemáticamente correcto y verificado por los tests unitarios (`tests/test_growth_commitment.py`), pero en estos 4 casos concretos **es redundante frente al ceiling por defecto**, no porque el mecanismo no funcione, sino porque el ceiling default-on ya implica un piso igual o mayor. Esto NO es una falla de la feature: es el resultado correcto de que ambos frenos comparten el mismo múltiplo x3 por default.

## Contraste: piso aislado (ceiling desactivado, NO es un modo default)

Para demostrar que el mecanismo del piso funciona de forma independiente (y que no es un techo — la parte superior queda libre), se corrió `vc_minimum` con `acquisition_ceiling.enabled=false` en las 4 instancias. Sin ningún freno superior, las 4 resultan `Unbounded` (comportamiento documentado y esperado, ADR 0010/0013: sin ceiling ni convex-CAC, la adquisición no tiene techo). Esto confirma que el piso NUNCA acota el crecimiento por arriba — solo por abajo — y que necesita, como siempre, algún freno superior (ceiling, convex-CAC, capacidad o caja) para acotar la solución.

| instancia | vc_minimum + ceiling OFF | status |
|---|---|---|
| godemos | piso aislado (sin ceiling) | **Unbounded** |
| entrena-en-casa | piso aislado (sin ceiling) | **Unbounded** |
| beloop | piso aislado (sin ceiling) | **Unbounded** |
| kavacomex | piso aislado (sin ceiling) | **Unbounded** |

## Lectura por caso

- **godemos**: caso más limpio (PRIORITY 1). VC=0 (operating_company), unit economics casi sin costo — el ceiling por defecto ya lleva el plan muy por encima del piso x3 (holgado en ambos checkpoints).
- **entrena-en-casa**: EBITDA año 1 negativo en el Excel (test de caja); el ceiling por defecto sigue dominando sobre el piso del compromiso en este benchmark.
- **beloop**: enterprise sticky (churn 0%) + downgrades de plan no modelados (ver YAML_EXTRACTION_SUMMARY) — el piso no cambia el resultado porque el ceiling ya domina; el downgrade no modelado sigue siendo el gap estructural conocido, independiente de esta feature.
- **kavacomex**: ramp real Motor ~0.99x (casi plano, ver ADR 0013) — se esperaba que fuera el candidato más probable a Infeasible bajo `vc_minimum` (WORKLOG P1), pero con los parámetros por defecto de `benchmark_v0/kavacomex.yaml` resultó **Optimal**: el ceiling default (x3/slack 0.15) sigue dominando incluso en este caso de ramp casi plano, porque el ceiling actúa sobre el stock consensuado del propio plan (que ya es mayor que el ramp manual del Excel). La rutina de diagnóstico R1-R8 se corrió de todas formas (ver abajo) para dejar la herramienta verificada end-to-end; con el estado base Optimal, todas las relajaciones reportan `feasible=True` trivialmente (nada que restaurar). El test unitario `test_diagnosis_routine_smoke` cubre el caso genuinamente infeasible (ceiling sin slack + hiring congelado en 0) con la rutina completa.

## Rutina de diagnóstico R1-R8 — kavacomex (vc_minimum)

Estado base: **Optimal**.

Base status: Optimal. Relajaciones que restauran factibilidad por sí solas: R1, R4, R5, R6, R8.

| relajación | aplica | factible | diagnóstico |
|---|---|---|---|
| R1: hiring friction removed (h_v, h_l -> +inf) | True | True | ritmo de contratación/onboarding insuficiente para la tesis |
| R2: advertising cap/investment x10 (only if advertising active) | False | None | no aplica a esta instancia (canal/piso no activo) |
| R3: channel min_share -> 0 (commercial mix unlocked) | False | None | no aplica a esta instancia (canal/piso no activo) |
| R4: churn x0.5 (retention doubled) | True | True | retención insuficiente: el stock decae más rápido de lo que se puede adquirir |
| R5: RRHH and g_adm -> 0 (fixed-cost counterfactual, informative only) | True | True | carga de costo fijo (solo informativo si no hay piso de caja activo) |
| R6: c_u -> 0 for all services (operating cost counterfactual) | True | True | estructura de costo operativo / margen bruto |
| R7: elastic working-capital floor (cash floor relaxed) | False | None | no aplica a esta instancia (canal/piso no activo) |
| R8: growth_commitment.multiple_3y -> 1.0 (the thesis itself) | True | True | ninguna palanca alcanza: la tesis en sí es el binding (múltiplo máximo factible no calculado en v1) |

Nota: base ya Optimal bajo `benchmark_v0/kavacomex.yaml` con parámetros por defecto — no hay infactibilidad que diagnosticar en esta corrida específica. La rutina R1-R8 sigue siendo válida y se verifica de forma independiente en `tests/test_growth_commitment.py::test_diagnosis_routine_smoke` sobre un caso sintético construido para ser genuinamente Infeasible (ceiling sin slack + hiring congelado en 0 nuevas contrataciones/mes).

