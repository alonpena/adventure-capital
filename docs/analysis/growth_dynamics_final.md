# Dinámica de crecimiento — decisión final

> **SUPERSEDIDO EN LA RECOMENDACIÓN (2026-07-06, corrección de Alonso):** la
> fricción de contratación NO es el mecanismo core de acotamiento — queda como
> feature opcional experimental/de sensibilidad. El core vigente es
> `growth_commitment` (piso) + `acquisition_envelope` (envolvente agregada de
> adquisición derivada del plan consensuado). Ver
> `NEXT_AGENT_HANDOFF_GROWTH_CORE.md` y ADR 0014 (enmienda). La EVIDENCIA de
> este documento (E1-E4, causa económica del unbounded) sigue válida.

Fecha: 2026-07-05 · Evidencia: `threshold_analysis.md` (E1–E4),
`growth_band_experiment.md` (B), `growth_dynamics_audit.md` (auditoría previa).
Criterio rector: el crecimiento NO puede depender de ceiling ×8 arbitrario; si el
modelo sin freno es unbounded, explicar la causa económica.

## Causa económica del Unbounded (criterio 2)

`max VAN` con: margen unitario positivo constante (c_u ≈ 0 en benchmarks reales),
canales lineales en adquisición, contratación instantánea y gratuita en capacidad,
y piso de caja laxo ⇒ el valor marginal de un cliente adicional es una constante
positiva ⇒ el LP empuja adquisición → ∞. **Lo que falta económicamente no es un
techo de mercado: es el costo/fricción de crecer** (contratar, formar, saturar
canales). Cualquier freno que no represente eso es un parámetro arbitrario.

## Comparación de mecanismos (tarea A)

| mecanismo | fórmula | sentido económico | parámetros | riesgo arbitrariedad | estado | costo impl. | ¿lunes? |
|---|---|---|---|---|---|---|---|
| Ceiling log × M (actual) | stock acumulado ≤ curva log → M·C12 | proxy tamaño mercado ex-ante | M, slack | **alto** (M es el driver del VAN: ×6.4 entre M=5 y 12) | producción | 0 | solo como **fallback declarado benchmark** |
| Banda mín + slack fijo/creciente (techo) | B_t ≤ stock_t ≤ B_t(1+δ) | compromiso VC con tolerancia | g, δ | medio (δ asumido) | experimento | ~20 líneas | NO: mata upside (VAN 2.5k–56k, tabla B) |
| Banda mín + slack MoM | g del MoM del plan consensuado (15.8%/mes → 4.8×/año) | "el plan promete su propia pendiente" | ninguno nuevo (derivado de A_base) | **bajo** (fuente: el propio YAML) | experimento | ~20 líneas | candidata si se exige techo |
| **Mín VC + fricción contratación (sin techo)** | stock_t ≥ B_t; V_t ≤ V_{t-1}+h; L_t ≤ L_{t-1}+h_L | piso = promesa al VC; techo = capacidad real de contratar/formar | g (fuente VC 2×: Motor godemos + Maureira), h (plan de contratación del cliente) | **bajo** (ambos declarables y auditables) | experimento (Optimal, VAN 3.83M, rampa orgánica V 3→14→26) | ~30 líneas + paridad estocástica + ADR | **ideal — post-lunes** |
| Saturación publicidad | A_ad = a+b·I; I∈[I_min,I_max]; A_ad ≤ cap | respuesta lineal declarada (ADR 0006) | recta + cap | bajo | **producción, auditada: SÍ acota** (tope = min(a+b·I_max, cap)/mes) | 0 | ya activo |
| CAC creciente por tramos (convex, ADR 0013) | premium θ·k por batch | saturación de canal | θ | alto (θ*=45–300 para reproducir ramps; VAN negativo en base) | producción opt-in | 0 | NO — documentado como comparación |
| Caja | Caja_t ≥ −VC | working capital | VC | nulo | producción | 0 | activo |
| Mix mínimo por canal | A_c ≥ min_share·A_total; Σmin ≤ 1 validado | estrategia comercial comprometida | min_share | bajo | producción (validación 2026-07-05) | 0 | activo |

## Evidencia banda (tarea B, `growth_band_experiment.md`)

| variante | status | VAN | lectura |
|---|---|---:|---|
| min 2× + slack 15% fijo | Optimal | 2,542 | techo apretado mata upside |
| min 2× + slack 10%/30% | Optimal | 55,847 | ídem |
| min 4.8× (MoM plan) + 15% | Optimal | 2,797,480 | holgura anclada al plan libera valor |
| min 2× SIN techo | **Unbounded** | — | piso solo no acota (esperado) |
| **min 2× + fricción h=1, sin techo** | Optimal | **3,829,866** | piso VC + techo económico; contratación orgánica |

Trade-off explícito: banda-techo elimina arbitrariedad del M pero introduce la del δ
y recorta upside; fricción de contratación acota por economía del negocio sin techo
numérico — su "parámetro" (h) es el plan de contratación del cliente, mismo estatus
epistemológico que `A_base`.

## Decisión

- **Ideal (documentada, NO implementada en producción):** mínimo VC-benchmark
  (g = 2×/año, fuentes: Motor godemos realizado + regla Maureira) + fricción de
  contratación (h declarado). Requiere: model.py (~30 líneas), paridad
  `stochastic/model.py`, claves YAML `growth_commitment`/`hiring`, ADR 0014,
  re-baseline goldens. Estimación: 1 día de trabajo con tests — **no se improvisa
  el fin de semana** (goal: "do not fake it").
- **Fallback estable para el lunes:** ceiling logarítmico, presentado como
  *benchmark de mercado declarado* (no como ley económica), con la banda/fricción
  como resultado de investigación cuantificado (tablas de arriba). Tests verdes.
- slack sin fuente (15% fijo) queda marcado **supuesto de tesis, no verdad empírica**.
