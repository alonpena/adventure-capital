# Corridas finales para UI — 2026-07-06

Usar en Streamlit:

```bash
cd /Users/apena/gits/adventure-capital
uv run streamlit run app.py --server.port 8508
```

## Recomendadas para demo

| Uso | Run | Estado | DD | M4 | VAN | Ingresos Y3 | Artefactos |
|---|---|---|---|---|---:|---:|---|
| Principal demo sobria | `run_20260706-080129_abfe9a6a` | completed | passed_with_warnings | completed | USD 1,084,768 | USD 1,964,469 | simple + standard + PDF |
| Caso ventas ~1MM | `run_20260706-080403_3bed9f18` | completed | passed_with_warnings | completed | USD 459,694 | USD 1,189,366 | simple + standard + PDF |
| Gold grande | `run_20260706-080500_28a63258` | completed | passed_with_warnings | completed | USD 4,583,212 | USD 4,503,277 | simple + standard + PDF |

## DD showcase

| Uso | Run | Estado | DD | M4 | Artefactos |
|---|---|---|---|---|---|
| DD pass | `run_20260706-081205_28a63258` | completed | passed_with_warnings | completed | simple + standard + PDF |
| DD liquidez | `run_20260706-081432_95bc9386` | completed | requires_minor_adjustment | completed | simple + standard + PDF |

## Benchmarks UI

| Caso | Run | Estado | DD | M4 | Nota |
|---|---|---|---|---|---|
| GoDemos | `run_20260706-081650_807210cf` | blocked | rejected_for_stochastic | blocked | simple + PDF; sin estándar por artefactos core faltantes |
| Entrena | `run_20260706-081651_a0fcddfc` | completed | passed_with_warnings | completed | simple + standard + PDF |
| GoDemos sin M4 | `run_20260706-082151_807210cf` | blocked | rejected_for_stochastic | blocked | simple + PDF; sin estándar por artefactos core faltantes |
| Beloop sin M4 | `run_20260706-082152_71a735f8` | completed | passed_with_warnings | pending | simple + standard + PDF |
| KavaComex sin M4 | `run_20260706-082155_e32c5cf5` | completed | passed_with_warnings | pending | simple + standard + PDF |

## Nota

Los reportes estándar fueron generados como `standard_report.html`; el informe ejecutivo simple queda en `report.html`. `report.pdf` corresponde al estándar cuando existe `standard_report.html`; en GoDemos corresponde al simple por falta de artefactos core para estándar.
