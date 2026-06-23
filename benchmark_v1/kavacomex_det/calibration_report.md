# Reporte de Calibración — Adventure Capital

**Veredicto**: ⚠️ WARN
**Fecha**: 2026-06-23T07:33:02.722927+00:00

## Resumen

| Total | Pasaron | Warnings | Errors | Saltados |
|---|---|---|---|---|
| 11 | 9 | 2 | 0 | 0 |

## Cheques que fallaron

### C08 · ltv_cac — ⚠️ Warning

**Fórmula**: `unit_economics['LTV/CAC']`

**Valor**: ltv_cac=214.9

**Umbral**: min_ratio=1, max_ratio=20

**Mensaje**: LTV/CAC 214.9× fuera de banda [1.0, 20.0]. Artefacto de fórmula — usar ARPU ponderado y margen por servicio.

**Sugerencia**: LTV/CAC = 215× es artefacto: la fórmula actual en `unit_economics.py` usa `ticket_promedio` aritmético y `marginal_gp` del primer servicio. Corrección recomendada: (a) calcular ARPU ponderado por adquisición real (Σ Ingresos / Σ adquisición), (b) usar `gross_profit` agregado en lugar del margen del primer servicio, (c) tratar `frecuencia` y `alpha` en el horizonte real (no a infinito). Una banda LTV/CAC realista B2B es 3×–10×.

### C09 · mix_concentration — ⚠️ Warning

**Fórmula**: `max_s(Σ A[s]) / Σ A`

**Valor**: top_service=Vino_Blended, top_pct=0.9353, totals=A_Vino_Blended=2,236, A_Licencias_Software=154.8

**Umbral**: max_concentration=0.85

**Mensaje**: 94% de la adquisición se concentra en 'Vino_Blended'. Considerar simplificar el mix.

**Sugerencia**: 94% de la adquisición se concentra en 'Vino_Blended'. El modelo prefiere ese plan ampliamente. Considerar (a) eliminar servicios con <10% del mix para simplificar el portafolio, (b) revisar tickets/c_u si la concentración no es deseada (quizás otros planes tienen margen unitario más bajo que el optimizador descarta).

## Cheques que pasaron

- **C01 · solver_status** — Solver retornó estado **Optimal**.
- **C02 · seller_capacity_saturation** — Capacidad saturada 8% — dentro del umbral 70%.
- **C03 · sellers_no_growth_with_saturation** — Vendedores muestran variación o no hay saturación crítica.
- **C04 · cash_floor** — Caja mínima USD 33,766 ≥ piso configurado.
- **C05 · total_ebitda** — EBITDA total USD 2,827,684 ≥ umbral.
- **C06 · npv** — VAN USD 1,345,563 ≥ umbral.
- **C07 · gross_margin** — Gross profit 70.4% dentro de banda.
- **C10 · retention** — Retención agregada 94% ≥ umbral.
- **C11 · document_completeness** — Documento y artifacts completos.

## Inputs

- Output dir: `benchmark_v1/kavacomex_det`
- Instance: `benchmark_v1/kavacomex_det/config.yaml`
- Document: `reports/valuation-base.yaml`
- Thresholds: `configs/calibration.yaml`
