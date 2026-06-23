# Reporte de Calibración — Adventure Capital

**Veredicto**: ⚠️ WARN
**Fecha**: 2026-06-23T07:33:01.455677+00:00

## Resumen

| Total | Pasaron | Warnings | Errors | Saltados |
|---|---|---|---|---|
| 11 | 8 | 3 | 0 | 0 |

## Cheques que fallaron

### C07 · gross_margin — ⚠️ Warning

**Fórmula**: `gp = 1 − Σ Costo_operacional / Σ Ingresos`

**Valor**: gross_profit=0.9797, revenue=2.855e+07, cost=5.806e+05

**Umbral**: min_gp=0.3, max_gp=0.92

**Mensaje**: Gross profit 98.0% fuera de banda [30%, 92%]. `c_u`/`c_min` subestimados o costos no modelados.

**Sugerencia**: Gross profit 98.0% es muy alto. `c_u` (actual 11) probablemente subestima el costo real de delivery. Sugerencia: `c_u ≈ 280` (≈20% del ticket) o activar `c_min` > 0 para reflejar costo fijo de capacidad. Servicios reales B2B rara vez superan 85% GP sostenido.

### C08 · ltv_cac — ⚠️ Warning

**Fórmula**: `unit_economics['LTV/CAC']`

**Valor**: ltv_cac=128.9

**Umbral**: min_ratio=1, max_ratio=20

**Mensaje**: LTV/CAC 128.9× fuera de banda [1.0, 20.0]. Artefacto de fórmula — usar ARPU ponderado y margen por servicio.

**Sugerencia**: LTV/CAC = 129× es artefacto: la fórmula actual en `unit_economics.py` usa `ticket_promedio` aritmético y `marginal_gp` del primer servicio. Corrección recomendada: (a) calcular ARPU ponderado por adquisición real (Σ Ingresos / Σ adquisición), (b) usar `gross_profit` agregado en lugar del margen del primer servicio, (c) tratar `frecuencia` y `alpha` en el horizonte real (no a infinito). Una banda LTV/CAC realista B2B es 3×–10×.

### C09 · mix_concentration — ⚠️ Warning

**Fórmula**: `max_s(Σ A[s]) / Σ A`

**Valor**: top_service=SaaS_Recurrente, top_pct=0.8991, totals=A_SaaS_Recurrente=1,851, A_SaaS_Enterprise=207.6

**Umbral**: max_concentration=0.85

**Mensaje**: 90% de la adquisición se concentra en 'SaaS_Recurrente'. Considerar simplificar el mix.

**Sugerencia**: 90% de la adquisición se concentra en 'SaaS_Recurrente'. El modelo prefiere ese plan ampliamente. Considerar (a) eliminar servicios con <10% del mix para simplificar el portafolio, (b) revisar tickets/c_u si la concentración no es deseada (quizás otros planes tienen margen unitario más bajo que el optimizador descarta).

## Cheques que pasaron

- **C01 · solver_status** — Solver retornó estado **Optimal**.
- **C02 · seller_capacity_saturation** — Capacidad saturada 4% — dentro del umbral 70%.
- **C03 · sellers_no_growth_with_saturation** — Vendedores muestran variación o no hay saturación crítica.
- **C04 · cash_floor** — Caja mínima USD 224,009 ≥ piso configurado.
- **C05 · total_ebitda** — EBITDA total USD 25,776,782 ≥ umbral.
- **C06 · npv** — VAN USD 11,192,853 ≥ umbral.
- **C10 · retention** — Retención agregada 96% ≥ umbral.
- **C11 · document_completeness** — Documento y artifacts completos.

## Inputs

- Output dir: `benchmark_v1/beloop_det`
- Instance: `benchmark_v1/beloop_det/config.yaml`
- Document: `reports/valuation-base.yaml`
- Thresholds: `configs/calibration.yaml`
