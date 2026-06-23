# Reporte de Due Diligence — Adventure Capital

**Veredicto**: ⚠️ PASSED WITH WARNINGS
**Permite valoración estocástica**: sí
**Modo de valoración**: final
**Nivel de ajuste**: none
**Re-ejecución recomendada**: no
**Veredicto de calibración (insumo)**: WARN
**Fecha**: 2026-06-23T07:33:01.457347+00:00

## Resumen

| Hallazgos | Fallidos | Estructural | Mayor | Menor | Avisos |
|---|---|---|---|---|---|
| 13 | 3 | 0 | 0 | 0 | 3 |

## Diagnóstico de liquidez

- Caja mínima: 224,009 (mes 3)
- Brecha máxima de financiamiento: 0 (mes None)
- Mes de breakeven (EBITDA acumulado ≥ 0): 6
- ¿La caja se vuelve negativa?: no
- ¿La caja se recupera al final?: no
- Caja final: 26,019,821

_La liquidez es diagnóstica: no bloquea la valoración estocástica._

## Hallazgos

### C07 · gross_margin — ⚠️ Aviso (calibration)

**Qué pasó**: Gross profit 98.0% fuera de banda [30%, 92%]. `c_u`/`c_min` subestimados o costos no modelados.

**Evidencia**: `{'value': {'gross_profit': 0.979664183385735, 'revenue': 28552185.0936, 'cost': 580632.0}, 'threshold': {'min_gp': 0.3, 'max_gp': 0.92}}`

### C08 · ltv_cac — ⚠️ Aviso (calibration)

**Qué pasó**: LTV/CAC 128.9× fuera de banda [1.0, 20.0]. Artefacto de fórmula — usar ARPU ponderado y margen por servicio.

**Evidencia**: `{'value': {'ltv_cac': 128.9380606325272}, 'threshold': {'min_ratio': 1.0, 'max_ratio': 20.0}}`

### C09 · mix_concentration — ⚠️ Aviso (calibration)

**Qué pasó**: 90% de la adquisición se concentra en 'SaaS_Recurrente'. Considerar simplificar el mix.

**Evidencia**: `{'value': {'top_service': 'SaaS_Recurrente', 'top_pct': 0.8991254817675548, 'totals': {'A_SaaS_Recurrente': 1850.648082, 'A_SaaS_Enterprise': 207.62756420000002}}, 'threshold': {'max_concentration': 0.85}}`

## Próximo paso

La valoración estocástica robusta puede correr normalmente.

## Inputs

- Output dir: `benchmark_v1/beloop_det`
- Config: `benchmark_v1/beloop_det/config.yaml`
