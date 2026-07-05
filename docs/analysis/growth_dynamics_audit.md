# Auditoría de dinámicas de crecimiento (determinista)

Fecha: 2026-07-05 · Evidencia: `threshold_analysis.md` (E1–E4), ADR 0010/0013,
`benchmark_v1/BENCHMARK_REPORT.md`, memoria de calibración θ.

## 1. Las cinco dinámicas, auditadas

| dinámica | naturaleza | evidencia | veredicto |
|---|---|---|---|
| Media móvil 3 períodos (`g_max_suavizado`) | freno de **tasa**; recurrencia geométrica (1+g)^t | mejor fidelidad histórica reportada por el autor; diverge dentro del MILP (E1: sin nivel el problema es Unbounded); inerte en código desde ADR 0011 | **LEGACY** — narrativa "naturaleza startup" válida para la tesis como motivación, no como restricción |
| Ceiling logarítmico × M (ADR 0010) | freno de **nivel**; proxy mercado ex-ante | acota siempre; VAN ~lineal en M (grid E2: VAN 5×→12× ≈ ×6.4) → M es el driver del valor, objeción metodológica válida | **BENCHMARK** — guard-rail de mercado / cota superior de referencia, no default |
| Convex-CAC θ (ADR 0013) | costo marginal creciente (endógeno económico) | reproduce ramps Motor (±0.05 Y2/Y1) pero θ*≈45–300 y VAN −25/−73%; en caso base VAN negativo; congela contratación (V 2→2) | **DOCUMENTADO COMO NO-FUNCIONA** para demo; comparación de métodos en tesis |
| **Fricción de contratación** `V_t ≤ V_{t-1} + h`, `L_t ≤ L_{t-1} + 1` | parámetro del **negocio** (capacidad de contratar/formar) | E4: Unbounded → Optimal solo con esto; rampa orgánica mensual; h declarado por el cliente (como `A_base`) | **DEFAULT RECOMENDADO** (requiere ADR 0014 + implementación formal + paridad estocástica) |
| Mínimo de crecimiento con holgura | piso, no techo | no implementado | **EXTENSIÓN FUTURA** (formulación en §2) |

## 2. Formulación alternativa evaluada (propuesta ADR 0014)

Combinación "el negocio acota, el benchmark vigila":

```text
(a) fricción operativa:   V_t ≤ V_{t-1} + h            t ≥ 13   [h: contrataciones/mes]
                          L_t ≤ L_{t-1} + h_L                    [líderes escalan, sup fijo]
(b) lag de productividad: capacidad usa V_{t-lag}                [commercial_productivity_lag > 0]
(c) caja:                 Caja_t ≥ −VC                           [ya existe]
(d) benchmark mínimo:     Σ_s A_{s,t} ≥ (1−δ)·A_bench_t          [piso: promesa de crecimiento]
    holgura superior:     Σ_s A_{s,t} ≤ (1+δ)·ceiling_t          [guard-rail mercado opcional]
(e) mix comercial:        min_share_c·A_t ≤ A_{c,t} ≤ max_share_c·A_t   [ya existe;
                          validación Σmin ≤ 1 ≤ Σmax agregada 2026-07-05]
```

- (a)+(b)+(c) bastan para acotar (probado E4) → upside no se mata: VAN crece con h,
  y h es auditable ("plan de contratación"), alineado con "plan a 3 años auditable"
  exigido por VCs (reunión 2026-07-01).
- (d) hace la promesa de crecimiento un COMPROMISO verificable (piso), no un techo:
  responde "benchmark mínimo de crecimiento con holgura" sin reintroducir M como driver.
- Costo de implementación: ~30 líneas en `model.py` + espejo en `stochastic/model.py`
  + 2 claves YAML (`hiring: {max_new_sellers_per_month, max_new_leaders_per_month}`).
  Golden tests se re-baselinean.

## 3. Fuerza de ventas estática — diagnóstico cerrado

Causa por archivo/línea ([model.py](../../src/adventure_capital/model.py)):

- `model.py:242-247` — t ≤ 12: V y L **fijados** desde `A_base` del plan consensuado
  (correcto por diseño).
- `model.py:248-253` — t ≥ 13: V solo aparece como capacidad (`Σ sf ≤ meta·V`) y span
  (`V ≤ sup·L`); `model.py:286-289` monotonía `V_t ≥ V_{t-1}`. **Puede** crecer
  (probado: `test_sellers_and_leaders_can_grow_in_projection`).
- No hay costo ni límite de contratación → el solver salta al máximo que el freno
  permite en el mes 13 y queda plano (ceiling: 2→9→9) o no salta (convex θ alto:
  2→2 — el estancamiento observado; las corridas del branch eran convex).
- Líderes SÍ escalan con vendedores (`V ≤ sup·L` fuerza L=⌈V/sup⌉); costos salariales
  no dominan (LTV/CAC 8–80× en benchmarks); canales alternativos no absorben (base
  demo es salesforce-only).

**Test que lo captura:** `tests/test_model_behavior.py::test_sellers_and_leaders_can_grow_in_projection`.
**Fix mínimo:** fricción §2(a) — elimina el salto-meseta (contrata cada mes).
**Impacto antes/después (base.yaml):** ceiling 8×: V 2→9→9 (meseta 24 meses), VAN 560k ·
con fricción h=1 sin ceiling: V 2→3→…→26 (rampa mensual), obj 1.9M.

## 4. Recomendación

- **Default:** fricción de contratación (h del cliente) + caja. Implementar tras ADR 0014.
- **Benchmark:** ceiling log × M como guard-rail superior opcional + referencia 3×.
- **Legacy:** media móvil (`g_max_suavizado`), documentada en tesis como motivación.
- **Futuro:** mínimo de crecimiento con holgura (§2d) + mini-optimizador de mix de
  canales (idea Maureira 2026-07-01).
- **Para el LUNES:** si no alcanza a entrar ADR 0014, demo corre con ceiling 8×
  (benchmark declarado) y la fricción se presenta como resultado de investigación
  (E4) — es más honesto que venderla implementada.
