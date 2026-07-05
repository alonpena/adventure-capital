# Comportamiento del modelo (invariantes probadas)

Fecha: 2026-07-05 · Evidencia: `tests/test_model_behavior.py` (8 tests, corren en ~3 s)
y `scripts/threshold_analysis.py` (E1–E4, resultados en `threshold_analysis.md`).

## Invariantes verificadas por test

| propiedad | test | resultado |
|---|---|---|
| VAN monótono creciente en `ticket` | `test_van_monotonic_in_ticket` | ✓ |
| Recurrencia (α>0) agrega valor | `test_recurrence_adds_value` | ✓ |
| Churn alto destruye valor | `test_higher_churn_destroys_value` | ✓ |
| Costos CAC (rem/com) reducen valor | `test_higher_cac_costs_reduce_value` | ✓ |
| **VC no mejora la operación**: plan idéntico, VAN baja exactamente ΔVC | `test_vc_does_not_improve_the_operating_plan` | ✓ |
| Vendedores/líderes PUEDEN crecer en proyección (m≥13) | `test_sellers_and_leaders_can_grow_in_projection` | ✓ |
| min_share activos > 100% → error de validación | `test_invalid_channel_minimums_fail_validation` | ✓ (validación agregada hoy) |
| max_share activos < 100% → error de validación | `test_insufficient_channel_maximums_fail_validation` | ✓ (ya existía) |

## Invariantes estructurales (threshold_analysis, E1–E4)

1. **Sin freno externo el MILP es `Unbounded`** (E1). El crecimiento no es endógeno
   en la clase actual: margen marginal positivo constante + canales lineales + sin
   fricción de contratación.
2. **Fricción de contratación sola acota** (E4): `V_t ≤ V_{t-1} + h` convierte
   Unbounded → Optimal con rampa orgánica mensual (h=1: V 2→26, obj 1.9M; h=2: 2→50, 3.6M).
3. **VAN lineal en VC** mientras el piso de caja no muerde (test + grid E2, exacto).
4. **Capital requerido real = drawdown máximo ≈ 113k** para la estructura de costos
   base, invariante a VC y a M (E2). Coincide con umbral analítico
   12·(g_adm+RRHH₁) − margen bruto año 1.
5. **VAN/Ingresos_Y3 ≤ 0.65** en todo el grid (E2): el benchmark correcto para tesis
   VC es exit-múltiplo ≥ 3× post-money (regla DD12), no VAN ≥ 1× ingresos.
6. **Salto-y-meseta de vendedores** bajo ceiling; estancamiento total bajo convex-CAC
   (ver `growth_dynamics_audit.md` §3).

## Reproducir

```bash
uv run pytest tests/test_model_behavior.py -q
uv run python scripts/threshold_analysis.py            # regenera threshold_analysis.md + CSV
```
