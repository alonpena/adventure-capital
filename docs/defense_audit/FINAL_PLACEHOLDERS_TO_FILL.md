# FINAL PLACEHOLDERS TO FILL — Defensa Adventure Capital

Estado actualizado al 2026-07-06 después de integrar `b8f0398` en `defense-slide-material`.

## Estado actual

La corrida gold ya existe y los placeholders principales del deck fueron reemplazados en los archivos `FINAL_*.md`.

| Campo | Valor |
|---|---|
| Gold instance | `configs/gold/gold-b2b-saas.yaml` |
| Gold run | `outputs/executions/run_20260706-045427_28a63258` |
| VAN | USD 4,583,212 |
| Revenue Y3 | USD 4,503,277 |
| EBITDA Y3 | USD 3,557,712 |
| DD verdict | `passed_with_warnings` |
| HTML | `outputs/executions/run_20260706-045427_28a63258/report.html` |
| PDF | `outputs/executions/run_20260706-045427_28a63258/report.pdf` |
| Benchmark path | `docs/analysis/growth_commitment_benchmarks.md` |

## Único pendiente real

| Pendiente | Acción |
|---|---|
| Screenshot UI | Capturar manualmente y guardar en `docs/defense_audit/assets/ui_informe_ejecutivo.png` |

Comando para lanzar UI:

```bash
cd /Users/apena/gits/adventure-capital
uv run streamlit run app.py --server.port 8508
```

Usar ejecución:

```text
outputs/executions/run_20260706-045427_28a63258
```

## Verificación rápida

```bash
cd /Users/apena/gits/adventure-capital
grep -rn "{{" docs/defense_audit/FINAL_*.md
open outputs/executions/run_20260706-045427_28a63258/report.html
open outputs/executions/run_20260706-045427_28a63258/report.pdf
```

## Regenerar PPTX después de cambios

```bash
cd /Users/apena/gits/adventure-capital
pandoc docs/defense_audit/FINAL_SLIDES.md -o docs/defense_audit/FINAL_SLIDES.pptx
```

## Nota

`outputs/` está ignorado por Git. Los artefactos gold existen localmente, pero no quedan versionados salvo configs y código. Para reproducirlos, usar `configs/gold/gold-b2b-saas.yaml` y ejecutar flujo completo.
