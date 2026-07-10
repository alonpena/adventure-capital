# Exit proxy sin arbitrariedad

Fecha: 2026-07-05 · Código: `valuation.py` (`calculate_dcf`,
`calculate_multiples_valuation`), ADR 0012, `due_diligence/rules.py` (DD12).
Criterio: múltiplos no pueden ser arbitrarios; preferir DCF/valor residual; múltiplos
solo con fuente o como sensibilidad.

## Opciones evaluadas

| opción | fórmula | arbitrariedad | veredicto |
|---|---|---|---|
| **Valor residual DCF (ADR 0012)** | VR = 1× EBITDA anualizado del último mes, descontado a t=H | **baja**: 1× es piso conservador documentado; el EBITDA sale del propio plan | **CORE** (ya es el default: `vr_nominal`/`vr_pv` en summary) |
| EBITDA Y3 × múltiplo | `mult_ebitda` (default 3.0) × EBITDA año 3 | media: 3.0 sin comparable citado | contraste secundario; etiquetado `implemented_reference, not market-calibrated` en `valuation_summary.json` (ya existe esa nota) |
| Ingresos Y3 × múltiplo | `mult_ingresos` (default 1.5) × ingresos año 3 | media: 1.5 plausible (Maureira citó 0.8–3× retail) pero sin fuente formal | **contraste VC** — es la base de DD12; presentar como "si el mercado paga k× ingresos"; el k queda parámetro explícito del YAML, no verdad |
| Múltiplo derivado de MoM/crecimiento | k = f(g) (ej. regla growth-adjusted) | alta sin paper que la respalde | descartado para tesis; mencionable como trabajo futuro con fuente (e.g. reglas revenue-multiple vs growth públicas) |
| Múltiplo comparable | k de transacciones/empresas comparables del sector | baja SI hay fuente; hoy NO hay dataset | camino correcto post-tesis; requiere fuente (Crunchbase/transacciones locales) |
| Solo sensibilidad | reportar EV(k) para k ∈ rango | nula | **ya implementado**: `sensitivity_wacc_multiple.csv` (matriz WACC × múltiplo) — usar como respaldo del contraste |

## Decisión

1. **Core = DCF con valor residual 1× EBITDA** (ADR 0012). Es el número que se
   defiende: conservador, autocontenido, sin múltiplo externo.
2. **Múltiplos = contraste VC, no valorización**: `mult_ingresos` alimenta el exit
   proxy de DD12 (exit ≥ 3× post-money) y se presenta SIEMPRE con la matriz de
   sensibilidad (WACC × múltiplo) en vez de como punto único.
3. Post-money mínimo = `max(VAN,0) + VC` (implementado en DD12) — definición de la
   reunión 2026-07-01, sin parámetros nuevos.
4. Todo múltiplo del YAML se declara **parámetro del análisis** en el informe (la
   nota metodológica ya existe en `multiples_reference`).

## Hitos cuantificados (criterio 10: clientes + dinero + mes)

| hito | mes | clientes | dinero | dónde vive hoy |
|---|---|---|---|---|
| Breakeven | primer t con EBITDA acum ≥ 0 (`liquidity_diagnostic.breakeven_month`, DD06) | `Clientes_activos` en ese t (optimized_results.csv) | EBITDA acumulado = 0 por definición; caja en ese t en la misma fila | ✅ mes y dinero directos; clientes por lookup de fila — la UI de growth plan ya muestra el acumulado en caja-cero |
| Payback | `payback_month` (primer t con Caja ≥ VC, unit_economics) | `payback_customers = VC/contribución` + `Clientes_activos` en ese t | VC recuperado (= VC por definición) | ✅ |
| Exit proxy | t = H (mes 36) | `Clientes_activos` en H | exit = mult_ingresos·Ingresos_Y3; post-money mín y ROI en DD12 evidence | ✅ (DD12 desde 2026-07-03) |

Gap menor (documentado, no parcheado a la carrera): "clientes en el mes de
breakeven/payback" existe en `optimized_results.csv` pero no está copiado como campo
propio en `summary.json`/informe — agregarlo es 1 línea en postprocess, candidato
post-lunes junto a DD08.
