# Reporte de Due Diligence — Adventure Capital

**Veredicto**: ⚠️ PASSED WITH WARNINGS
**Permite valoración estocástica**: sí
**Modo de valoración**: final
**Nivel de ajuste**: none
**Re-ejecución recomendada**: no
**Veredicto de calibración (insumo)**: WARN
**Fecha**: 2026-06-23T07:33:02.724624+00:00

## Resumen

| Hallazgos | Fallidos | Estructural | Mayor | Menor | Avisos |
|---|---|---|---|---|---|
| 12 | 2 | 0 | 0 | 0 | 2 |

## Diagnóstico de liquidez

- Caja mínima: 33,766 (mes 12)
- Brecha máxima de financiamiento: 0 (mes None)
- Mes de breakeven (EBITDA acumulado ≥ 0): 20
- ¿La caja se vuelve negativa?: no
- ¿La caja se recupera al final?: no
- Caja final: 2,974,534

_La liquidez es diagnóstica: no bloquea la valoración estocástica._

## Hallazgos

### C08 · ltv_cac — ⚠️ Aviso (calibration)

**Qué pasó**: LTV/CAC 214.9× fuera de banda [1.0, 20.0]. Artefacto de fórmula — usar ARPU ponderado y margen por servicio.

**Evidencia**: `{'value': {'ltv_cac': 214.9255737830648}, 'threshold': {'min_ratio': 1.0, 'max_ratio': 20.0}}`

### C09 · mix_concentration — ⚠️ Aviso (calibration)

**Qué pasó**: 94% de la adquisición se concentra en 'Vino_Blended'. Considerar simplificar el mix.

**Evidencia**: `{'value': {'top_service': 'Vino_Blended', 'top_pct': 0.9352704430582189, 'totals': {'A_Vino_Blended': 2236.395849, 'A_Licencias_Software': 154.77973620000003}}, 'threshold': {'max_concentration': 0.85}}`

## Próximo paso

La valoración estocástica robusta puede correr normalmente.

## Inputs

- Output dir: `benchmark_v1/kavacomex_det`
- Config: `benchmark_v1/kavacomex_det/config.yaml`
