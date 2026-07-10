# FINAL DIAGRAMS — Defensa Adventure Capital

Mermaid limpio, convertible a PPT (formas simples, sin estilos exóticos). Colores según gramática visual del deck: azul/teal = sistema, ámbar/rojo = gates/riesgo, gris = artefactos, verde = evidencia validada.

Para renderizar a PNG/SVG (requiere `mmdc`, no instalado hoy):
```bash
npx -y @mermaid-js/mermaid-cli -i docs/defense_audit/FINAL_DIAGRAMS.md -o docs/defense_audit/diagrams/
```

---

## Diagrama 1 — Flujo metodológico (Slide 5)

```mermaid
flowchart LR
    A[YAML<br/>supuestos] --> B[Validación<br/>config.py]
    B --> C[Instancia mensual<br/>instance.py]
    C --> D[MILP determinista<br/>target-driven<br/>model.py]
    D --> E[Valorización DCF<br/>unit economics<br/>valuation.py]
    E --> F{Due diligence<br/>gate}
    F -->|habilita| G[M4 robustez<br/>stochastic/]
    F -->|bloquea| H[Recalibrar<br/>supuestos]
    D --> I[(Artefactos<br/>CSV / JSON / HTML)]
    E --> I
    F --> I
    G --> I
    I --> J[UI Streamlit<br/>+ report.html]

    style A fill:#ECECEC,stroke:#6B6B6B
    style F fill:#FFF3E0,stroke:#C77D00
    style H fill:#FDECEA,stroke:#7A1F1F
    style I fill:#ECECEC,stroke:#6B6B6B
    style J fill:#ECECEC,stroke:#6B6B6B
    style D fill:#E3F0F4,stroke:#1F6F8B
    style E fill:#E3F0F4,stroke:#1F6F8B
    style G fill:#E3F0F4,stroke:#1F6F8B
```

**Nota PPT:** en PowerPoint dibujar como pipeline horizontal de 9 nodos; DD como rombo ámbar; artefactos como cilindro gris.

---

## Diagrama 2 — Arquitectura modular en capas (Slide 7)

```mermaid
flowchart TB
    subgraph L1[Entrada — supuestos versionables]
        C1[configs/*.yaml]
    end
    subgraph L2[Core financiero — fuente de verdad]
        C2[config.py · instance.py · model.py]
        C3[valuation.py · unit_economics.py · results.py]
    end
    subgraph L3[Juicio y robustez]
        C4[due_diligence/ — gate]
        C5[stochastic/ — M4 robustez técnica]
    end
    subgraph L4[Presentación — solo lectura de artefactos]
        C6[standard_report/ · report.html]
        C7[app.py · streamlit_pages/]
    end
    O[(outputs/executions/&lt;run&gt;/)]

    L1 --> L2 --> O
    O --> L3 --> O
    O --> L4

    style L1 fill:#ECECEC,stroke:#6B6B6B
    style L2 fill:#E3F0F4,stroke:#1F6F8B
    style L3 fill:#FFF3E0,stroke:#C77D00
    style L4 fill:#ECECEC,stroke:#6B6B6B
    style O fill:#ECECEC,stroke:#6B6B6B
```

**Nota PPT:** cuatro bandas horizontales; flechas unidireccionales; texto clave "la UI no recalcula" junto a la banda de presentación.

---

## Diagrama 3 — Mapa input → output de artefactos (Slide 8)

```mermaid
flowchart LR
    subgraph IN[Supuestos]
        Y[config.yaml]
    end
    subgraph MODEL[Outputs del modelo]
        MI[model_instance.json]
        OR[optimized_results.csv<br/>plan mensual canónico]
    end
    subgraph DERIV[Juicio y valor]
        VS[valuation_summary.json]
        UE[unit_economics.csv]
        DD[due_diligence_report.md]
        ST[stochastic_summary.csv]
    end
    subgraph OUT[Entregables]
        RH[report.html / report.pdf]
        FT[formula_trace.json]
        AM[artifacts_manifest.json]
        UI[Páginas Streamlit]
    end

    Y --> MI --> OR
    OR --> VS
    OR --> UE
    OR --> DD
    DD -->|gate| ST
    VS --> RH
    UE --> RH
    DD --> RH
    OR --> FT
    RH --> UI
    AM --> UI

    style IN fill:#ECECEC,stroke:#6B6B6B
    style MODEL fill:#E3F0F4,stroke:#1F6F8B
    style DERIV fill:#FFF3E0,stroke:#C77D00
    style OUT fill:#ECECEC,stroke:#6B6B6B
```

**Nota PPT:** tres/cuatro columnas con nombres de archivo reales en tipografía mono; flechas rectas.

---

## Diagrama 4 — Demo path en UI (Slide 12)

```mermaid
flowchart LR
    S1[1. Seleccionar<br/>ejecución] --> S2[2. Informe<br/>ejecutivo]
    S2 --> S3[3. Plan de<br/>crecimiento]
    S3 --> S4[4. Valoración]
    S4 --> S5[5. Due<br/>diligence]
    S5 --> S6[6. Robustez<br/>M4]
    S6 --> S7[7. Artefactos<br/>descargables]

    style S5 fill:#FFF3E0,stroke:#C77D00
    style S6 fill:#FFF3E0,stroke:#C77D00
    style S7 fill:#ECECEC,stroke:#6B6B6B
    style S1 fill:#E3F0F4,stroke:#1F6F8B
    style S2 fill:#E3F0F4,stroke:#1F6F8B
    style S3 fill:#E3F0F4,stroke:#1F6F8B
    style S4 fill:#E3F0F4,stroke:#1F6F8B
```

**Nota PPT:** cinta horizontal de 7 pasos bajo el screenshot de UI; paso activo resaltado durante la demo.

---

## Diagrama 5 — Objetivo → evidencia → lectura defendible (Slide 6)

```mermaid
flowchart LR
    O1[Formalización de datos] --> E1[config.yaml<br/>artifacts_manifest.json] --> L1[Supuestos trazables]
    O2[Due diligence cuantitativo] --> E2[due_diligence_report.md] --> L2[No reemplaza DD legal/comercial]
    O3[Plan de crecimiento] --> E3[optimized_results.csv<br/>ADR 0014] --> L3[Plan oficial determinístico]
    O4[Valorización y unit economics] --> E4[valuation_summary.json<br/>unit_economics.csv] --> L4[Valor trazable a supuestos]
    O5[Robustez] --> E5[stochastic_summary.csv<br/>ADR 0015] --> L5[Robustez técnica, no plan oficial]
    O6[Informe automático] --> E6[report.html<br/>report.pdf si backend disponible] --> L6[Entregable auditable]
    O7[Validación] --> E7[pytest: 186 passed, 3 skipped<br/>benchmark_v0] --> L7[Reproducibilidad técnica]

    style O1 fill:#E3F0F4,stroke:#1F6F8B
    style O2 fill:#E3F0F4,stroke:#1F6F8B
    style O3 fill:#E3F0F4,stroke:#1F6F8B
    style O4 fill:#E3F0F4,stroke:#1F6F8B
    style O5 fill:#E3F0F4,stroke:#1F6F8B
    style O6 fill:#E3F0F4,stroke:#1F6F8B
    style O7 fill:#E3F0F4,stroke:#1F6F8B
    style E2 fill:#FFF3E0,stroke:#C77D00
    style E5 fill:#FFF3E0,stroke:#C77D00
    style L1 fill:#ECECEC,stroke:#6B6B6B
    style L2 fill:#ECECEC,stroke:#6B6B6B
    style L3 fill:#ECECEC,stroke:#6B6B6B
    style L4 fill:#ECECEC,stroke:#6B6B6B
    style L5 fill:#ECECEC,stroke:#6B6B6B
    style L6 fill:#ECECEC,stroke:#6B6B6B
    style L7 fill:#ECECEC,stroke:#6B6B6B
```

**Nota PPT:** si el diagrama queda denso, convertirlo a tabla nativa 7 filas × 4 columnas. La tabla debe conservar los mismos artefactos y lecturas.

| Objetivo | Evidencia | Artefacto | Lectura defendible |
|---|---|---|---|
| Formalización de datos | YAML/configuración estándar | `config.yaml`, `artifacts_manifest.json` | Supuestos trazables |
| Due diligence cuantitativo | Gate financiero/metodológico | `due_diligence_report.md` | No reemplaza DD legal/comercial |
| Plan de crecimiento | Target-driven growth (ADR 0014) | `optimized_results.csv` | Plan oficial determinístico |
| Valorización/unit economics | DCF + métricas unitarias | `valuation_summary.json`, `unit_economics.csv` | Valorización trazable a supuestos |
| Robustez | M4 / escenarios (ADR 0015) | `stochastic_summary.csv` o evidencia de bloqueo DD | Robustez técnica, no plan oficial |
| Informe automático | Reporte HTML/PDF | `report.html` (`report.pdf` si WeasyPrint) | Entregable auditable y descargable |
| Validación | Tests + benchmark | `pytest`: 186 passed, 3 skipped; `benchmark_v0` | Reproducibilidad técnica |

**Nota PPT:** columna "Lectura defendible" en gris; sin checks verdes salvo evidencia ejecutada (tests, corridas existentes).
