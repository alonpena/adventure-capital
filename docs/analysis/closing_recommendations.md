# Recomendaciones de cierre — defensa lunes 6 jul 2026, 8:15

Fecha: 2026-07-05 · Branch: `entrega-tesis` · Suite: 161 tests verdes.
Índice de la auditoría: `model_behavior.md` · `growth_dynamics_audit.md` ·
`due_diligence_audit.md` · `valuation_unit_economics_map.md` ·
`stochastic_objective_audit.md` · `distribution_assumptions.md` · este archivo.

## 1. Resumen ejecutivo

El sistema NO calibra instancias para cuadrar resultados: la auditoría estableció los
**umbrales de la clase de modelo** bajo los cuales una startup alcanza resultados tipo VC:

1. **Crecimiento**: sin freno el MILP es Unbounded (probado). El freno con significado
   de negocio es la **fricción de contratación** (h vendedores/mes): sola convierte el
   problema en Optimal con rampa orgánica. Ceiling×M queda como benchmark; convex-CAC
   documentado como no-funciona; media móvil legacy.
2. **Capital**: el requerimiento real es el drawdown (≈113k para la estructura base),
   invariante a VC y M. VAN lineal en VC. Tickets pre-seed ≤100k son compatibles.
3. **Umbral VC**: el criterio correcto es **exit ≥ 3× post-money** (DD12, implementado),
   no VAN ≥ 1× ingresos (inalcanzable: tope 0.65 con β=35%).
4. **Estocástico**: objetivo mean-CVaR empíricamente inerte (5 combinaciones λ×α →
   mismo plan). El −20% E[VAN] viene de distribuciones sesgadas asignadas sin
   validación. 98% de la varianza: salesforce_efficiency (77%) + WACC (21%).
5. **DD**: con la exención operating-company, ninguna de las 4 instancias reales queda
   bloqueada. Las reglas distinguen bien bloquear/advertir/informar; único ajuste
   recomendado: DD08 sobre drawdown en vez de gap/VC.

## 2. Cambios realizados (esta auditoría, branch entrega-tesis)

- `scripts/threshold_analysis.py` (E1–E4) + `scripts/objective_sweep.py` + grids CSV.
- Regla **DD12 exit-ROI 3×** + **exención DD03** (`operating_company: true`);
  godemos se valoriza por primera vez (VAN 1,178k, minor, M4 habilitado).
- Validación nueva: Σ min_share canales activos ≤ 1 (error YAML claro).
- `tests/test_model_behavior.py` (8 invariantes) + 6 tests DD nuevos.
- Informe HTML: fórmulas movidas a Anexo metodológico.
- Outputs purgados 59MB→5.7MB (§5 de este doc); monolito Colab a `legacy/`.
- 7 documentos de auditoría en `docs/analysis/`.

## 3. Decisiones recomendadas para el lunes (en orden)

| decisión | recomendación | esfuerzo |
|---|---|---|
| Ley de crecimiento a presentar | demo con **ceiling 8× declarado como benchmark**; fricción de contratación presentada como resultado de investigación (E4) y propuesta ADR 0014 — NO implementarla el fin de semana | 0 (relato) |
| β | bajar a **0.30** en el caso demo (reunión: 20%+10%) | 1 línea YAML |
| VC caso demo | **≤ 100k** (regla de negocio) + narrar capital requerido = drawdown ≈113k con las 3 dimensiones (clientes/tiempo/dinero) | 1 línea YAML |
| Titular estocástico | P50 + banda P5–P90; CVaR como métrica de riesgo; mencionar robustez a la elección de objetivo | 0 (la UI ya lo hace) |
| Distribuciones | declarar "supuestos por elicitar" (versión B) — honesto y defendible; NO simetrizar a la carrera | 0 |
| Instancia demo | entrena (passed_with_warnings) o godemos (ahora corre; DD12 muestra señal real 1.7×) | 0 |

## 4. Riesgos abiertos

- **Truncamiento año 3** (Y3/Y2 ≈ 1.3 vs Motor ~2): artefacto de horizonte compartido
  por todos los frenos (ADR 0013). Mitigación futura: término de cola. Declararlo si preguntan.
- Fricción de contratación NO implementada en producción (solo E4 experimental) — no
  venderla como hecha.
- Distribuciones sin elicitar: E[VAN] estocástico subestima ~20% por construcción.
- DD08 aún compara gap contra VC (recomendación pendiente).
- Beloop H=38: unidades/downgrades mal especificados vs Excel (+469% VAN) — no usar en demo.
- kavacomex con convex θ en cota (ramp plano): usar solo modo ceiling.

## 5. Outputs: qué se conserva y por qué

- **Conservado**: `outputs/instances/` + `outputs/executions/` — único estado que lee
  la UI Streamlit (workflow_registry.py: OUTPUTS_ROOT). `benchmark_v0/` (YAMLs fuente),
  `benchmark_v1/` (reporte comparativo citado por docs).
- **Borrado** (2026-07-03): ~40 dirs ad-hoc en `outputs/` (aijourney*, cli-*, dd-*,
  demo-*, m4-audit*, phase-1, etc.) y `runs/` con timestamps — corridas de desarrollo
  sin consumidor. 59MB → 5.7MB.

## 6. Comandos para reproducir

```bash
uv run pytest -q                                    # suite completa (161 pass)
uv run python scripts/threshold_analysis.py         # E1-E4 -> docs/analysis/threshold_*
uv run python scripts/objective_sweep.py            # sweep λ×α -> docs/analysis/objective_sweep.*
uv run adventure-capital run --config benchmark_v0/godemos.yaml --output /tmp/godemos-check
uv run adventure-capital run --config configs/caso-base-1m.yaml --output /tmp/base-check
```

## 7. ¿Listo para demo?

**SÍ, con el relato correcto.** Pipeline completo corre end-to-end (instancia → DD →
M4 → informe HTML) sobre las 4 instancias reales sin bloqueos; suite verde; UI lee
artefactos consistentes. Lo que NO está listo (y no debe fingirse): ley de fricción de
contratación en producción, distribuciones elicitadas, corrección DD08. Los tres están
cuantificados y documentados — presentarlos como hallazgos de la auditoría y trabajo
futuro es más fuerte que ocultarlos.
