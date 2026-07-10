# Pre-UI validation and calibration plan

Fecha: 2026-07-06

## Objetivo

Antes de integrar UI, cerrar una capa mínima de validación numérica:

1. Benchmarks reales v1 ya corridos contra Excel/transcript.
2. Agregar AiJourney y caso de asesorías como casos adicionales.
3. Calibrar Entrena en Casa como caso base simple.
4. Crear pruebas ad hoc de sanidad por arquetipo comercial.
5. Separar validación de año 1 vs. validación de método target-driven.

## Principio metodológico

No calibrar VAN directo.

Orden de calibración:

1. Fuente: Excel + transcript.
2. A_base meses 1-12 sagrado.
3. Revenue año 1: calibrar `ticket` / ARPU blended.
4. EBITDA año 1: calibrar `c_u`, `c_min`, `g_adm`, `RRHH`.
5. Unit economics: revisar LTV/CAC como alerta, no como KPI final.
6. VAN: consecuencia. Comparar y explicar divergencia por growth law, terminal value y estructura no modelada.

## Estado benchmark v1 actual

Archivo:

```text
outputs/benchmark_instances_v1/benchmark_instances_v1.md
```

Lectura:

| Caso | Estado |
|---|---|
| GoDemos | Baseline válido. Raw YAML queda dentro de tolerancia ±20% en Revenue Y1, EBITDA Y1 y VAN. |
| Entrena en Casa | No válido aún. Revenue Y1 -28%, EBITDA demasiado negativo. Probable falta de base instalada y/o ticket/c_min. |
| Beloop | Año 1 útil; VAN no comparable por setup/consultoría/downgrades no modelados. |
| KavaComex | Stress case; año 1 cerca, VAN no comparable por logística/freelance/ABC no modelados. |

## AiJourney

Archivo Excel encontrado:

```text
/Users/apena/Desktop/Proyecto Adventure Capital/Planillas/Planilla Evaluación AiJourney (1).xlsx
```

Existe config previa:

```text
configs/aijourney.yaml
```

Uso recomendado:

- Tratar como caso SaaS/servicios AI de ticket alto y churn alto.
- Primero correr `configs/aijourney.yaml` en raw y target_core.
- Luego extraer targets del Excel:
  - Revenue Y1
  - EBITDA Y1
  - VAN / post-money usado por Alejandro
  - VC / capital de trabajo
  - beta/tasa descuento
  - churn
  - A_base
- Comparar config actual vs Excel.
- Si no calza, crear `instances_yaml_v1/aijourney.yaml` calibrado, no sobrescribir `configs/aijourney.yaml`.

## Caso asesorías

Archivo:

```text
/Users/apena/Desktop/Proyecto Adventure Capital/Planillas/3) Planilla Modelamiento con asesorías.xlsx
```

Uso recomendado:

- Crear caso `asesorias.yaml` o `consulting-advisory.yaml`.
- Arquetipo: servicios profesionales / consultoría.
- Debe validar capacidad y costos fijos, no sólo SaaS.
- Modelar simple:
  - 1 servicio `Asesoria_Blended`.
  - `ticket` = revenue Y1 / client-months.
  - `frecuencia` según recurrencia real (mensual/trimestral/anual).
  - `c_u` = costo variable delivery por cliente/mes o por hora blended.
  - `c_min` = capacidad mínima equipo/consultores si aplica.
  - `meta` = clientes por vendedor si hay fuerza comercial; si no, mantener conservador.
- No inventar VAN: target desde Excel.

## Entrena en Casa: calibración rápida

Benchmark actual raw:

- Revenue Y1 modelo: 125,268
- Revenue Y1 Excel: 173,000
- Gap: -28%
- Ticket actual: 238.1

Escalamiento revenue-only aproximado:

```text
ticket_new = 238.1 * 173000 / 125268 ≈ 328.8
```

Después de ajustar ticket:

- Recalcular EBITDA Y1.
- Si EBITDA queda demasiado alto vs target -17,800, aumentar costo operacional (`c_min` o `c_u`) hasta cerrar EBITDA Y1.
- Si sigue bajo revenue por stock, registrar necesidad de `initial_clients`.

No implementar `initial_clients` en este paso. Sólo diagnosticarlo.

## Sanity matrix por arquetipo

Crear script `scripts/scenario_sanity_matrix.py` o extender benchmark harness.

Arquetipos mínimos:

| Arquetipo | Base sugerida | Qué valida |
|---|---|---|
| B2B SaaS sales-led | Beloop/AiJourney simplificado | ticket alto, churn bajo/medio, CAC vendedor, RRHH alto |
| B2C subscription | GoDemos simplificado | volumen, churn alto, ticket bajo, margen alto |
| Services/consulting | Asesorías / Entrena | capacidad operativa, costos fijos, margen por delivery |
| Advertising-led | demo-advertising-only | recta publicitaria, CAC variable |
| Mixed channels | demo-mixed-channels | salesforce + ads + third-party |
| Capital-constrained | demo-working-capital | cash floor/funding gap |
| Target-driven growth | demo-growth-core | ratio m36/C12 ≈ tesis múltiplo |

Overlays a probar:

1. Pricing: `ticket` × {0.8, 1.0, 1.2}.
2. Churn: `churn_anual` × {0.5, 1.0, 1.5}, capped < 1.
3. Comercial productivity: `meta` × {0.5, 1.0, 1.5}.
4. VC: `VC` × {0.5, 1.0, 2.0}.
5. Thesis multiple: `investment_thesis.multiple` × {2, 3, 5} under target_core.
6. Channels:
   - salesforce only
   - advertising only
   - mixed
   - third-party capped if active

Métricas a capturar:

- status
- VAN
- total revenue
- total EBITDA
- revenue Y1/Y3
- EBITDA Y1/Y3
- min_cash
- final_cash
- stock_m36/C12
- acquisition total
- LTV/CAC
- CAC/customer
- DD verdict

Checks de sanidad esperados:

- Ticket ↑ => VAN no debería bajar, salvo restricciones/costos proporcionales dominantes.
- Churn ↑ => VAN debería bajar o clientes finales bajar.
- VC ↑ => min_cash mejora; VAN puede cambiar sólo por capital de trabajo/valuation treatment.
- Meta ↑ (más productividad) => CAC por cliente baja o adquisición factible mejora.
- Target multiple ↑ => stock_m36/C12 sube, cash pressure sube, VAN puede subir o bajar según economics.
- Advertising-only no debe romper si config active/caps válidos.
- Third-party activo requiere cap para evitar unbounded.

## Criterio de cierre antes de UI

Mínimo suficiente:

1. Benchmark v1 CSV/MD existe.
2. AiJourney raw + target_core corrido o documentado como pending por extracción Excel.
3. Asesorías YAML creado o documentado como pending por extracción Excel.
4. Entrena calibration proposal generado (`ticket≈328.8` starting point) y corrida.
5. Sanity matrix corre en 5-7 arquetipos sin crash.
6. GoDemos queda caso principal de validación.

## Qué se puede afirmar

Válido:

- El motor corre casos reales y produce artefactos trazables.
- GoDemos reproduce Excel dentro de tolerancia y sirve como validación principal.
- Target-core logra tesis ×3 de forma acotada y auditable.
- Los otros casos exponen brechas estructurales esperables, no bugs silenciosos.

No válido:

- “Todos los casos reproducen Excel.”
- “Target-core debe igualar VAN Excel.”
- “LTV/CAC actual es KPI definitivo.”
- “Beloop/Kava validan VAN.”

## Trabajo futuro

- `initial_clients` como cohorte t=0.
- Unit economics por segmento.
- Setup one-shot y downgrades para Beloop.
- Logística/freelance/ABC para KavaComex.
- Asesorías con horas/capacidad si Excel lo exige.
