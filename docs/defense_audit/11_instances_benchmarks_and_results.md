# 11 Instances Benchmarks And Results

## Instancias

| Instancia | Fuente | Tipo | Uso slide |
|---|---|---|---|
| `configs/base.yaml` | repo | demo/base | explicar pipeline |
| `configs/aijourney.yaml` | repo | demo/caso | alternativa smoke |
| `configs/demo-growth-core.yaml` | repo | core growth demo | explicar target-driven |
| `benchmark_v0/*.yaml` | benchmark | casos comparativos | evidencia metodología |
| `outputs/executions/*` | generado | corridas históricas | demo si se valida ruta |

## Benchmarks Growth Core

Fuente: `docs/analysis/growth_commitment_benchmarks.md`.

| Caso | VAN core demo | Ing Y3 | DD gate | Lectura |
|---|---:|---:|---|---|
| godemos | 942,635 | 1,038,995 | requires_minor_adjustment | caso más limpio con ajuste menor |
| entrena-en-casa | -69,622 | 304,266 | requires_major_adjustment | no cumple escala |
| beloop | 1,973,394 | 2,618,430 | passed_with_warnings | caso fuerte con caveat downgrades |
| kavacomex | -416,453 | 217,140 | requires_major_adjustment | muestra diagnóstico negativo |

## Regla Para Defensa

Usar benchmarks como evidencia de comportamiento del sistema, no como resultado final de tesis salvo que Alonso designe uno como gold.

