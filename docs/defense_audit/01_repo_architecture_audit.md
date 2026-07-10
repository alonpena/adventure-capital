# 01 Repo Architecture Audit

## Estado de Rama

| Campo | Valor |
|---|---|
| Rama de trabajo | `defense-slide-material` |
| Base | `demo-integrated-growth-ui` |
| Motivo | rama más reciente; rama directa no disponible por otro worktree |
| Working tree previo | limpio antes de crear `docs/defense_audit/` |
| Audit docs previos | no presentes como archivos versionados en esta rama; se usaron repo/docs actuales como fuente |

## Mapa Del Repositorio

| Carpeta/archivo | Rol | Estado defensa |
|---|---|---|
| `src/adventure_capital/` | código fuente principal | core |
| `configs/` | instancias YAML y thresholds | core |
| `reports/` | YAML y schemas de reporte | core reporte |
| `docs/adr/` | decisiones técnicas | evidencia metodológica |
| `docs/analysis/` | auditorías/experimentos/benchmarks | evidencia secundaria |
| `tests/` | regresión y smoke tests | evidencia de confiabilidad |
| `outputs/` | instancias/ejecuciones generadas | evidencia demo si se elige run |
| `benchmark_v0/`, `benchmark_v1/` | benchmarks y artefactos históricos | evidencia, no core |
| `legacy/` | notebook Colab original | no presentar como core |
| `app.py`, `streamlit_pages/` | UI Streamlit local | demo/UI |

## Arquitectura Actual

```mermaid
flowchart LR
  YAML[configs/*.yaml] --> Config[config.py]
  Config --> Inst[instance.py]
  Inst --> MILP[model.py PuLP/CBC]
  MILP --> Results[results.py]
  Results --> Val[valuation.py]
  Results --> UE[unit_economics.py]
  Val --> Art[CSV/JSON artifacts]
  UE --> Art
  Art --> DD[due_diligence]
  DD --> M4[stochastic M4 if allowed]
  Art --> Report[reporting/standard_report/simple_report]
  Report --> UI[Streamlit reads artifacts]
```

## Superficies de Ejecución

| Superficie | Archivo | Uso |
|---|---|---|
| Python API | `pipeline.run_pipeline()` | notebooks/scripts; no escribe si no hay `output_dir` |
| CLI | `src/adventure_capital/cli.py` | instancias, ejecuciones, reportes, calibración |
| UI | `app.py` | gestor de instancias/ejecuciones y exploración de artefactos |

## Wording Seguro

“La arquitectura actual es un pipeline local reproducible y auditable, con UI Streamlit sobre artefactos. No es una plataforma SaaS productiva todavía.”

## Estado De Auditoría Arquitectura Previa

El brief mencionaba `docs/architecture/*` y `diagrams/architecture_mermaid.md`, pero en la rama latest auditada no aparecen como archivos versionados. No se asumieron como autoridad. Esta carpeta `docs/defense_audit/` reconstruye el material desde el estado actual de `src/`, `docs/`, `configs/`, `tests/`, `app.py`, `streamlit_pages/`, `outputs/` y ADRs.
