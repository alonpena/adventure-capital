# Reporte de Due Diligence — Adventure Capital

**Veredicto**: ⚠️ PASSED WITH WARNINGS
**Permite valoración estocástica**: sí
**Modo de valoración**: final
**Nivel de ajuste**: none
**Re-ejecución recomendada**: no
**Veredicto de calibración (insumo)**: WARN
**Fecha**: 2026-06-23T07:30:33.172145+00:00

## Resumen

| Hallazgos | Fallidos | Estructural | Mayor | Menor | Avisos |
|---|---|---|---|---|---|
| 12 | 2 | 0 | 0 | 0 | 2 |

## Diagnóstico de liquidez

- Caja mínima: 57,825 (mes 9)
- Brecha máxima de financiamiento: 0 (mes None)
- Mes de breakeven (EBITDA acumulado ≥ 0): 17
- ¿La caja se vuelve negativa?: no
- ¿La caja se recupera al final?: no
- Caja final: 2,153,250

_La liquidez es diagnóstica: no bloquea la valoración estocástica._

## Hallazgos

### C08 · ltv_cac — ⚠️ Aviso (calibration)

**Qué pasó**: LTV/CAC 111.1× fuera de banda [1.0, 20.0]. Artefacto de fórmula — usar ARPU ponderado y margen por servicio.

**Evidencia**: `{'value': {'ltv_cac': 111.14289893659796}, 'threshold': {'min_ratio': 1.0, 'max_ratio': 20.0}}`

### C09 · mix_concentration — ⚠️ Aviso (calibration)

**Qué pasó**: 100% de la adquisición se concentra en 'Sesiones_Blended'. Considerar simplificar el mix.

**Evidencia**: `{'value': {'top_service': 'Sesiones_Blended', 'top_pct': 1.0, 'totals': {'A_Sesiones_Blended': 1492.318292}}, 'threshold': {'max_concentration': 0.85}}`

## Próximo paso

La valoración estocástica robusta puede correr normalmente.

## Inputs

- Output dir: `benchmark_v1/entrena-en-casa_det`
- Config: `benchmark_v1/entrena-en-casa_det/config.yaml`
