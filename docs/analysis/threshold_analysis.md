# Análisis de umbrales del modelo determinista

Seed config: `configs/base.yaml` · generado por `scripts/threshold_analysis.py`

## E3 — Umbral analítico de factibilidad

Costo fijo comprometido año 1 = 12·(g_adm + RRHH_1) = **138,000**.
Todo VC bajo ese número depende del margen bruto del año 1 para no romper el piso de caja −VC.

## E1 — ¿Qué acota el crecimiento sin freno externo?

Ceiling y convex-CAC desactivados → **solver status = Unbounded**

## E4 — Fricción de contratación como freno endógeno

Mismo modelo sin freno + `V_t <= V_{t-1} + h`, `L_t <= L_{t-1} + 1` (t ≥ 13):

| h (vendedores/mes) | status | objetivo | V m13 / m24 / m36 |
|---:|---|---:|---|
| 1 | Optimal | 1,900,576 | 3 / 14 / 26 |
| 2 | Optimal | 3,638,902 | 4 / 26 / 50 |

## E2 — Frontera (VC × M)

min caja = capital realmente requerido (dinero); su mes = tiempo; breakeven = EBITDA acumulado ≥ 0.

| caso | VAN | Ing Y3 | VAN/IngY3 | min caja (mes) | breakeven | V m12→13→36 |
|---|---:|---:|---:|---:|---:|---|
| vc50k-m3 | -25,818 | 451,084 | -0.06 | -63,293 (m15) | 30 | 2→3→3 |
| vc50k-m5 | 220,057 | 754,501 | 0.29 | -61,918 (m12) | 21 | 2→6→6 |
| vc50k-m8 | 609,694 | 1,189,366 | 0.51 | -61,918 (m12) | 18 | 2→9→9 |
| vc50k-m12 | 1,143,278 | 1,755,677 | 0.65 | -61,918 (m12) | 16 | 2→12→12 |
| vc100k-m3 | -75,818 | 451,084 | -0.17 | -13,293 (m15) | 30 | 2→3→3 |
| vc100k-m5 | 170,057 | 754,501 | 0.23 | -11,918 (m12) | 21 | 2→6→6 |
| vc100k-m8 | 559,694 | 1,189,366 | 0.47 | -11,918 (m12) | 18 | 2→9→9 |
| vc100k-m12 | 1,093,278 | 1,755,677 | 0.62 | -11,918 (m12) | 16 | 2→12→12 |
