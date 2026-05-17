# Blueprint del Módulo de Calibración

Compuerta de calibración (`calibration gate`) entre la corrida del modelo y el generador del informe estándar. Su propósito: **bloquear la generación de informes de valorización sobre planes que no convergieron a una solución razonable**, y proponer ajustes accionables sobre los parámetros del modelo o del documento.

## Posición en el pipeline

```
config.yaml ─► run_pipeline() ─► outputs/<run>/*.csv
                                       │
                                       ▼
                          run_calibration(outputs/, config.yaml,
                                          configs/calibration.yaml)
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                         PASS         WARN         FAIL
                          │            │            │
                          │            │            ▼
                          │            │     ✋ bloquea informe
                          ▼            ▼            ▼
                          ───► build_report_data_package() ◄───
                              (sólo si PASS o --gate warn-ok|skip)
```

## Convenciones

- **Idioma**: outputs en español (mensajes, sugerencias). API en inglés.
- **Severidades**: `error` (falla dura), `warning` (señal de calibración), `info` (siempre permite).
- **Veredicto agregado**: `FAIL` si cualquier error, `WARN` si cualquier warning y ningún error, `PASS` en otro caso.
- **Configurabilidad**: todos los umbrales viven en `configs/calibration.yaml`. Cada cheque puede deshabilitarse con `enabled: false`.
- **Trazabilidad**: cada cheque emite `value`, `threshold`, y la `formula` que aplicó, para auditoría.

## Catálogo de cheques (Fase A + B)

Cada cheque tiene: `id`, `severity` por defecto, dependencias de archivos, fórmula y banda aceptable.

### C01 · Estado del solver

- **Severidad**: error
- **Fuente**: `solution.status` (almacenado en `optimized_results.csv` como metadata, o en `pipeline.result`)
- **Falla si**: `status != "Optimal"`
- **Por qué**: una solución `Infeasible` o `Unbounded` significa que la optimización no encontró un plan viable bajo las restricciones; cualquier output derivado es ruido.

### C02 · Capacidad de vendedores saturada

- **Severidad**: warning
- **Fuente**: `optimized_results.csv`
- **Fórmula**: `slack[t] = meta * Vendedores[t] - Adq_clientes[t]` para `t ≥ 13`
- **Falla si**: porcentaje de meses con `slack < 0.5` supera `max_pct_saturated` (default `0.70`)
- **Por qué**: si el modelo opera al techo de capacidad casi todo el horizonte optimizado, no representa un plan de aceleración, sino un plan de cosecha sobre capacidad fija. El plan de aceleración exige inversión en fuerza comercial.

### C03 · Vendedores nunca crecen pero capacidad satura

- **Severidad**: warning
- **Fuente**: `optimized_results.csv`
- **Fórmula**: `max(Vendedores) == min(Vendedores[t≥13])` **AND** C02 satura
- **Falla si**: ambas condiciones se cumplen
- **Por qué**: confirma que el optimizador prefiere no contratar; típicamente `rem_v` es alto vs ticket marginal o `meta` es excesivamente generosa.

### C04 · Caja negativa en algún momento

- **Severidad**: error (configurable, depende de `liquidity_policy`)
- **Fuente**: `optimized_results.csv`
- **Fórmula**: `min(Caja[t])`
- **Falla si**: `min(Caja) < liquidity_floor` (default `0`)
- **Por qué**: un plan que requiere financiamiento intermedio no comunicado no es presentable como caso base.

### C05 · EBITDA total negativo

- **Severidad**: error
- **Fórmula**: `Σ EBITDA[t]`
- **Falla si**: `< 0`
- **Por qué**: el horizonte debe cerrar con utilidad operacional positiva para sustentar valorización.

### C06 · VAN negativo

- **Severidad**: error
- **Fórmula**: `dcf.VAN`
- **Falla si**: `< 0`
- **Por qué**: con VAN negativo, la valorización DCF carece de sentido inversor; no debería emitirse el informe sin recalibración.

### C07 · Margen bruto fuera de banda

- **Severidad**: warning
- **Fórmula**: `gross_profit = 1 - Σ Costo_operacional / Σ Ingresos`
- **Banda aceptable**: `[0.30, 0.92]` (configurable)
- **Falla si**: fuera de esa banda
- **Por qué**: > 92% indica que `c_u`/`c_min` están subestimados (servicios humanos que en realidad cuestan más); < 30% indica un margen no-VC.

### C08 · LTV/CAC fuera de rango realista

- **Severidad**: warning
- **Fórmula**: `unit_economics["LTV/CAC"]`
- **Banda aceptable**: `[1.0, 20.0]` (configurable)
- **Falla si**: fuera de esa banda
- **Por qué**: el cálculo de LTV en el modelo actual usa `ticket_promedio` aritmético y `churn_mensual` derivado de churn anual; cuando la mezcla real de adquisición está sesgada hacia servicios de bajo ticket pero la fórmula promedia tickets, el resultado se infla. Ver C12 sobre cálculo ponderado.

### C09 · Concentración extrema en un servicio

- **Severidad**: warning
- **Fórmula**: `max_s(Σ A[s,t]) / Σ A[s,t]`
- **Falla si**: > `max_concentration` (default `0.85`)
- **Por qué**: si el optimizador concentra > 85% de adquisiciones en un solo servicio, la oferta multi-servicio no es representativa y el plan podría reformularse con menos planes.

### C10 · Stock final muy bajo respecto a adquisición acumulada

- **Severidad**: warning
- **Fórmula**: `Clientes_activos[H] / Σ Adq_clientes[t]`
- **Falla si**: < `min_retention_ratio` (default `0.20`)
- **Por qué**: una retención agregada < 20% en el horizonte sugiere un churn anual demasiado alto para la frecuencia configurada — la economía recurrente no se materializa.

### C11 · Documento YAML obligatorio incompleto

- **Severidad**: error
- **Fuente**: reutiliza `validate_report_inputs()` actual
- **Falla si**: cualquier campo `required` o `collections` no satisface el schema
- **Por qué**: aunque exista el modelo financiero, sin narrativa documental el informe queda incompleto.

### C12 · Consistencia interna A/Q/C

- **Severidad**: warning
- **Fuente**: `optimized_results.csv` + `instance`
- **Fórmula**: para cada servicio `s`:
  - `expected_Q[s] = A[s] + α × Σ supervivencia × elegibles_recompra`
  - desviación = `|Q[s,t] - expected_Q[s,t]| / max(Q[s,t], 1)`
- **Falla si**: desviación > `5%` en > 5% de los meses
- **Por qué**: detectores de bugs en el modelo o en los datos pre-procesados (e.g., `repurchase_eligible` mal calculado).

## Sugerencias automatizadas (Fase C)

Cada cheque que falle dispara una sugerencia accionable parametrizada con los valores observados. Ejemplos:

| Cheque | Sugerencia template |
|---|---|
| C02 | `Reducir 'meta' de {meta_actual} a {meta_actual // 2}, o bajar 'rem_v' de {rem_v_actual} para permitir crecimiento de fuerza comercial.` |
| C03 | `Considerar relajar restricción monotónica de 'sellers' o agregar incentivo en la función objetivo.` |
| C04 | `min(Caja) = {min_cash}. Aumentar 'VC' (capital de trabajo) a al menos {recommended_vc} o activar 'liquidity_policy.minimum_cash'.` |
| C07 (alto) | `Gross profit {gp:.1%} > 92%. Revisar 'c_u' (actual {c_u}) — debería reflejar costo real de delivery, típicamente 15-25% del ticket promedio ({suggested_c_u}).` |
| C08 (alto) | `LTV/CAC = {ratio}× es artefacto: la fórmula usa ticket promedio aritmético ({ticket_avg}) pero ARPU ponderado real es {arpu_real}. Recalcular usando ARPU por adquisición.` |
| C09 | `{pct:.1%} de la adquisición se concentra en '{top_service}'. Considerar eliminar planes con < 10% de mezcla del modelo.` |
| C10 | `Retención agregada {ratio:.1%}. Bajar 'churn_anual' a < {suggested_churn} o subir 'frecuencia' (compras más frecuentes mejoran retención efectiva).` |

## Estructura de salida

### `calibration_report.json`

```json
{
  "schema_version": "1.0",
  "created_at": "...",
  "verdict": "PASS|WARN|FAIL",
  "summary": {
    "total_checks": 12,
    "passed": 9,
    "warnings": 3,
    "errors": 0,
    "skipped": 0
  },
  "checks": [
    {
      "id": "C02",
      "name": "seller_capacity_saturation",
      "severity": "warning",
      "passed": false,
      "value": {"meses_saturados": 27, "slack_promedio": 0.0, "pct_saturado": 0.96},
      "threshold": {"max_pct_saturated": 0.70},
      "message": "Vendedores fijos en 1 desde el mes 10, capacidad saturada el 96% del horizonte optimizado.",
      "suggestion": "Reducir 'meta' de 38 a 19, o bajar 'rem_v' de 1333 a 800-1000 para permitir crecimiento de fuerza comercial."
    }
  ],
  "inputs": {
    "output_dir": "outputs/aijourney-2024",
    "instance": "configs/aijourney.yaml",
    "thresholds": "configs/calibration.yaml"
  }
}
```

### `calibration_report.md`

Versión en español agrupada por severidad con cheques y sugerencias. Incluye:

- Hero: veredicto + 4 tiles (errores, warnings, passed, skipped)
- Sección por severidad con los cheques que fallaron
- Apéndice con cheques que pasaron (para confirmar cobertura)

## Modos del gate

| Modo | Comportamiento |
|---|---|
| `strict` (default) | Bloquea generación si veredicto = `WARN` o `FAIL` |
| `warn-ok` | Bloquea sólo si `FAIL`; permite `WARN` |
| `skip` | Siempre permite (modo debug) |

## CLI

```bash
# Sólo ejecutar la calibración
adventure-capital calibrate \
  --input outputs/aijourney-2024 \
  --config configs/aijourney.yaml \
  --thresholds configs/calibration.yaml

# El gate se invoca implícitamente en report; --gate controla cómo trata WARN/FAIL
adventure-capital report \
  --input outputs/aijourney-2024 \
  --document reports/valuation-base.yaml \
  --config configs/aijourney.yaml \
  --gate strict
```

## Códigos de retorno

- `0` = PASS
- `1` = WARN
- `2` = FAIL
- `3` = WARN bloqueado por gate strict
- `4` = FAIL bloqueado por gate

## Archivos producidos

| Archivo | Propósito |
|---|---|
| `outputs/<run>/calibration_report.json` | dictamen máquina-legible |
| `outputs/<run>/calibration_report.md` | dictamen humano-legible en español |

## Limitaciones conocidas

1. Los umbrales son heurísticos. Un negocio puede legítimamente estar fuera de banda (e.g., SaaS con LTV/CAC 25× real). El usuario puede ajustar `configs/calibration.yaml` o pasar `--gate warn-ok`.
2. C12 no se implementa en MVP — requiere reconstruir la lógica de `repurchase_eligible` del modelo. Se deja como follow-up.
3. La capa de sugerencias usa fórmulas paramétricas simples; no garantiza convergencia tras aplicar el cambio. Es indicativa, no prescriptiva.
