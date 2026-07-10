# FINAL ASSET CHECKLIST — Defensa Adventure Capital

## Estado de tooling (verificado 2026-07-06)

| Herramienta | Estado | Uso |
|---|---|---|
| `pandoc` | ✅ `/opt/homebrew/bin/pandoc` | genera `FINAL_SLIDES.pptx` desde Markdown |
| `marp` / marp-cli | ❌ no instalado | render alternativo de `FINAL_SLIDES.md` |
| `quarto` | ❌ no instalado | — |
| `mmdc` (mermaid-cli) | ❌ no instalado | render de diagramas a PNG/SVG |
| `python-pptx` | ❌ no instalado | — |

Render diagrams sin instalar globalmente (descarga puntual vía npx, pedir aprobación si se considera dependencia):
```bash
npx -y @mermaid-js/mermaid-cli -i docs/defense_audit/FINAL_DIAGRAMS.md -o docs/defense_audit/diagrams/
```

Regenerar PPTX tras editar `FINAL_SLIDES.md`:
```bash
pandoc docs/defense_audit/FINAL_SLIDES.md -o docs/defense_audit/FINAL_SLIDES.pptx
```

Render Marp (si se instala):
```bash
npx -y @marp-team/marp-cli docs/defense_audit/FINAL_SLIDES.md -o docs/defense_audit/FINAL_SLIDES.html
```

## Top 5 visuales para construir en PPT (a mano, calidad > generación)

1. **Matriz objetivo → evidencia** (slide 6) — tabla nativa PPT 7×4; es el corazón del deck. Fuente: `FINAL_DIAGRAMS.md` Diagrama 5.
2. **Pipeline metodológico de 9 nodos** (slide 5) — formas simples horizontales; DD como rombo ámbar. Fuente: Diagrama 1.
3. **Curva stock de clientes con C12/C24/C36 + envelope** (slide 9) — graficar desde `optimized_results.csv` del gold run (o `configs/demo-growth-core.yaml` como fallback).
4. **Arquitectura en 4 capas** (slide 7) — bandas horizontales con directorios reales en mono. Fuente: Diagrama 2.
5. **Tabla benchmark con semáforo DD** (slide 13) — 4 filas; VAN negativos en oxblood, misma dignidad visual que positivos.

## Top 5 screenshots para capturar

1. **UI: informe ejecutivo de la ejecución gold** → `[PENDIENTE: capturar screenshot UI — sugerido docs/defense_audit/assets/ui_informe_ejecutivo.png]` (slide 12, principal).
2. **UI: página de due diligence con veredicto visible** (slide 10, respaldo de gate real).
3. **UI: página de artefactos con lista de descargas** (slide 12/demo paso 7).
4. **`report.html` abierto en navegador** (slide 12; demuestra entregable sin UI).
5. **Terminal: `uv run pytest -q` con `186 passed, 3 skipped`** (slide 13; evidencia verde literal).

Guardar en `docs/defense_audit/assets/` con nombres descriptivos (`ui_informe_ejecutivo.png`, `ui_due_diligence.png`, `ui_artefactos.png`, `report_html.png`, `pytest_pass.png`).

## Checklist pre-defensa

- [ ] Corrida gold generada y placeholders reemplazados (`FINAL_PLACEHOLDERS_TO_FILL.md`).
- [ ] `FINAL_SLIDES.pptx` regenerado con valores reales.
- [ ] 5 screenshots capturados en `docs/defense_audit/assets/`.
- [ ] Diagramas 1–4 renderizados o reconstruidos en PPT.
- [ ] UI probada con la ejecución gold (demo path completo ensayado 2 veces).
- [ ] `report.html` del gold run abre correctamente en el navegador de la sala.
- [ ] Plan B de demo (archivos directos) verificado sin UI.
- [ ] `FINAL_COMMITTEE_QA.md` releído; top 5 riesgos memorizados.
- [ ] Verificar tabla benchmark del deck contra `docs/analysis/growth_commitment_benchmarks.md`.
- [ ] Tiempo ensayado: exposición ≤ 15 min + demo 2–3 min.
