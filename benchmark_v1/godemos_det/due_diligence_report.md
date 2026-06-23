# Reporte de Due Diligence — Adventure Capital

**Veredicto**: 🚫 REJECTED FOR STOCHASTIC
**Permite valoración estocástica**: no
**Modo de valoración**: none
**Nivel de ajuste**: structural
**Re-ejecución recomendada**: sí
**Veredicto de calibración (insumo)**: —
**Fecha**: 2026-06-23T07:30:10.411340+00:00

## Resumen

| Hallazgos | Fallidos | Estructural | Mayor | Menor | Avisos |
|---|---|---|---|---|---|
| 5 | 1 | 1 | 0 | 0 | 0 |

## Hallazgos

### DD03 · financing_present — 🚫 Estructural (bloqueante) (due_diligence)

**Qué pasó**: Falta input esencial: `VC` <= 0 (sin capital de trabajo inicial para ejecutar el plan).

**Qué recalibrar**: Definir un `VC` (capital de trabajo inicial) > 0.

**Evidencia**: `{'VC': 0.0}`

## Motivos de bloqueo (estructural)

- Falta input esencial: `VC` <= 0 (sin capital de trabajo inicial para ejecutar el plan).

## Próximo paso

La instancia es estructuralmente inviable; la valoración estocástica **no corre**. Corregir los motivos de bloqueo y re-ejecutar el flujo.

## Inputs

- Output dir: `benchmark_v1/godemos_det`
- Config: `<in-memory>`
