# Decisiones finales de modelamiento — pre-defensa

Fecha: 2026-07-05 · Branch `entrega-tesis` · Goal: cerrar lógica de modelo antes de UI.
Índice: `growth_dynamics_final.md` · `saa_here_and_now_final.md` ·
`recourse_extension.md` · `exit_proxy_non_arbitrary.md` · `growth_band_experiment.md`
· auditorías previas (`closing_recommendations.md` y compañía) · bitácora `WORKLOG.md`.

## Qué queda IMPLEMENTADO (producción, tests verdes)

- Pipeline determinista + DD (12 reglas propias + 11 calibración) + M4 SAA two-stage
  + evaluación out-of-sample LHS N=1000.
- Frenos disponibles: ceiling log × M (default), convex-CAC (opt-in, documentado
  como no apto), publicidad acotada (recta + I_min/I_max + cap — auditada hoy: SÍ
  acota), caja, mix por canal con validación Σmin ≤ 1 ≤ Σmax.
- Salesforce monótona sin despidos con contratación posible m13+ (test:
  `test_sellers_and_leaders_can_grow_in_projection`).
- DD12 exit-ROI 3× + exención DD03 operating-company (godemos corre).
- `mean_cvar_lambda` como dial: λ=1 ⇒ **max E[VAN] here-and-now sin tocar código**.
- Hitos breakeven/payback/exit con mes+clientes+dinero mapeados
  (`exit_proxy_non_arbitrary.md` §Hitos).

## Qué queda como FALLBACK para el lunes

- **Ceiling logarítmico declarado como benchmark de mercado** (no como ley
  económica). El M que se use se presenta como referencia declarada, con la
  sensibilidad VAN(M) del grid E2 sobre la mesa (transparencia > ocultamiento).
- mean-CVaR λ=0.5 α=0.15 como default vigente, presentado como caso paramétrico de
  la formulación mean-riesgo (λ=1 es el caso neutral pedido académicamente).

## Qué se recomienda para la DEMO

1. Instancia: entrena o godemos (ambas corren end-to-end sin bloqueo).
2. Relato de crecimiento: causa económica del unbounded (falta fricción de crecer)
   → evidencia E1/E4/banda → propuesta formal piso-VC + fricción (ADR 0014 futuro)
   → fallback benchmark transparente hoy.
3. Estocástico: formulación SAA here-and-now (`saa_here_and_now_final.md`), titular
   P50 + banda P5–P90, robustez al objetivo como resultado.
4. Exit: DCF/VR 1×EBITDA como core; múltiplo ingresos solo como contraste VC con
   matriz de sensibilidad.

## Qué queda como EXTENSIÓN FUTURA

- ADR 0014: `growth_commitment` (stock_t ≥ B_t, g con fuente) + `hiring`
  (V_t ≤ V_{t-1}+h) en producción + paridad estocástica + goldens (~1 día).
- Recourse comercial / rolling horizon (`recourse_extension.md`).
- Elicitación de distribuciones (prioridad: salesforce_efficiency, WACC).
- DD08 sobre drawdown; campo "clientes en breakeven/payback" en summary; curva de
  saturación publicitaria cóncava; múltiplos comparables con fuente.

## Riesgos metodológicos abiertos

- Truncamiento año 3 (todos los frenos): declarar si preguntan.
- Slack de banda sin fuente = supuesto de tesis (marcado).
- Distribuciones estocásticas no validadas (−20% E[VAN] por construcción, declarado).
- Beloop mal especificado vs Excel; kavacomex solo modo ceiling.

## Reproducir

```bash
uv run pytest -q                                     # 161 pass esperados
uv run python scripts/threshold_analysis.py          # E1-E4
uv run python scripts/growth_band_experiment.py      # banda mín+holgura (5 variantes)
uv run python scripts/objective_sweep.py             # objetivo estocástico λ×α
```

**Cumplimiento del goal:** crecimiento ya no depende del ceiling ×8 como verdad
(queda benchmark declarado + alternativa ideal cuantificada y documentada, no
improvisada); causa económica del unbounded explicada; banda mín+holgura evaluada
con evidencia CSV/MD; publicidad auditada (acota); salesforce monótona y puede
crecer; Σmin_share validado; SAA here-and-now formulado con factibilidad medida;
recourse documentado como extensión; hitos cuantificados; múltiplos no arbitrarios
(DCF core); tests verdes.
