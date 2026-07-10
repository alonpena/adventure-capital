# Diagnóstico del camino Unbounded (modo destino)

> **SUPERSEDIDO EN EL FRAMING §0 (2026-07-06, corrección de Alonso):** el "modo
> destino" ya NO es piso + fricción de contratación — la fricción queda como
> feature experimental/de sensibilidad, no core. El core vigente es
> `growth_commitment` + `acquisition_envelope` (ADR 0014 enmienda); el agujero
> third-party de §5-6 quedó cerrado con la validación `A_tp_cap` obligatoria.
> La evidencia técnica de este documento sigue válida.

Fecha: 2026-07-05 · Branch: `growth-law-adr14` · Script reproducible:
`scripts/unbounded_path_matrix.py` (correr DESDE este branch/worktree).
Configuración auditada: `acquisition_ceiling.enabled=false` +
`growth_commitment.enabled=true` (vc_minimum ×3, checkpoints anuales) +
`hiring.enabled=true`.

## 0. Resultado principal — el caso reportado NO es Unbounded

**El modo destino (piso + fricción, ceiling off) es `Optimal` en las 4 instancias
benchmark, con h=1 y h=2.** La tabla "Unbounded en las 4" de
`growth_commitment_benchmarks.md` corresponde al **piso AISLADO sin fricción**
(hiring off) — comportamiento esperado y documentado (el piso nunca acota por
arriba). No hay bug en commitment/hiring.

| instancia | h | status | objetivo | V_36 | A_sf total |
|---|---:|---|---:|---:|---:|
| godemos | 1 | Optimal | 2,203,888 | 25 | 5,254 |
| godemos | 2 | Optimal | 4,135,024 | 49 | 9,754 |
| entrena | 1 | Optimal | 2,658,275 | 25 | 6,576 |
| entrena | 2 | Optimal | 5,133,897 | 49 | 12,576 |
| beloop | 1 | Optimal | 14,866,612 | 26 | 1,800 |
| beloop | 2 | Optimal | 26,785,955 | 50 | 3,300 |
| kavacomex | 1 | Optimal | 620,691 | 23 | 6,515 |
| kavacomex | 2 | Optimal | 1,426,569 | 45 | 12,455 |

Caveat honesto: el objetivo escala ~lineal con h (h es LA palanca de valor del
modo destino — parámetro declarado del cliente, mismo estatus que `A_base`).
kavacomex pasa de VAN −378k (ceiling) a +620k (destino h=1): la fricción permite
crecer más que el ceiling ×3 en ese caso.

## 1-2. Camino unbounded exacto y canal responsable

Existe UN camino unbounded real en la clase de modelo, y es **third-party**:

```text
mixed dest third_party-only            → Unbounded
mixed dest tp-only com=0               → Unbounded
mixed dest salesforce-only             → Optimal (fricción acota: meta·V, V acotado por h)
mixed dest advertising-only            → Optimal (recta + I_max + A_ad_cap acotan)
mixed dest ALL channels                → Optimal (tp acotado por max_share < 1)
```

Variables involucradas: `A_tp[s,t]` (y arrastradas: C, Q, I, revenue). Camino:
`A_tp → clientes → ingresos` con margen positivo y **ninguna cota propia del canal**.

## 3-7. Cotas por canal (auditoría de restricciones)

| canal | cota propia | ¿acota? |
|---|---|---|
| salesforce | `Σ A_sf ≤ meta·V_{t-lag}`; V monótono + fricción h | ✅ (con hiring on) |
| advertising | `A_ad = a + b·I`; `I_min ≤ I ≤ I_max` (t≥13); `A_ad ≤ A_ad_cap` | ✅ (model.py:180-196) |
| **third_party** | **NINGUNA**: solo `A_tp ≤ max_share·A_total` — si tp domina (max_share=1 o único canal), la cota es tautológica (A_tp ≤ A_tp) | ❌ **agujero** |
| A_total | sin cota agregada propia (por diseño: la ponen los canales) | n/a |

- Fricción de contratación SÍ liga la adquisición salesforce (probado: sf-only Optimal).
- I_max SÍ capa clientes por publicidad (probado: ad-only Optimal).
- Caja NO acota por sí sola: margen positivo autofinancia el crecimiento
  (`base dest + cash≥0` = **Infeasible**, no Optimal — el piso de caja duro choca
  con el año 1 consensuado; consistente con la decisión "solo piso −VC").
- Costos SÍ están ligados a adquisición (c_u·Q, comisiones, rem·V) — el problema
  no es de costos desconectados sino de margen unitario positivo sin límite de
  capacidad en tp.

## 8-10. Preguntas restantes

- ¿Variables con coeficiente positivo en el objetivo sin cota? Ninguna directa:
  el objetivo es VAN; la cadena A_tp→ingresos es la única vía indirecta sin cota.
- ¿Comisión detiene tp? No: con commission 25% y sin ella, Unbounded igual
  (margen sigue positivo).

## 11. ¿Bug o esperado?

**Esperado matemáticamente, agujero de modelado latente.** Documentado desde E1:
todo canal necesita SU freno. sf lo tiene (capacidad+fricción), ad lo tiene
(recta+caps), tp no tiene ninguno. Hoy es inofensivo: ninguna instancia real usa
third_party dominante (godemos/entrena/kavacomex sf-only; beloop sf-only), y con
mix real `max_share<1` lo acota indirectamente. Se manifiesta SOLO con tp único o
max_share=1.

## 5-6. Fixes mínimos y el más seguro antes del lunes

1. **Más seguro (config-only, recomendado antes del lunes): validación** en
   `validate_config` — si `third_party.active` y ceiling+convex off y
   `max_share ≥ 1` y no hay otro canal activo con cota ⇒ error claro
   ("third_party requiere A_tp_cap o max_share < 1 sin freno global"). No cambia
   ninguna solución existente.
2. Estructural (post-defensa): clave `A_tp_cap` (cap mensual por período, espejo
   de `A_ad_cap`) — 5 líneas en model.py + validación + test. Interpretación de
   negocio: capacidad del partner.
3. Alternativa económica futura: comisión creciente por tramos (convex) para tp.

## 7. Tests requeridos

- `test_tp_only_without_cap_rejected` (validación 1) o
  `test_tp_cap_bounds_acquisition` (fix 2).
- Regresión: `mixed dest ALL channels` sigue Optimal.
- Ya cubierto hoy: destino sf-only Optimal (`test_sellers_and_leaders_can_grow…`
  + benchmarks tabla §0).

## Anexo: cableo W1-W5 (encargo paralelo, IMPLEMENTADO en este branch)

`run_due_diligence` ahora: (a) emite W1/W2/W4/W5 pre-modelo cuando
`growth_commitment.enabled` (no-op si off); (b) emite **W3/DD17** cuando el solver
reporta Infeasible/Undefined con commitment activo — tanto en el camino normal
(la cadena sobrevive vía C01 de calibración) como en el camino de excepción de
consistencia (re-solve directo + reporte limpio, sin crash). Test:
`test_dd_chain_emits_w_warnings_and_survives_infeasible`. Suite: **172 passed, 3 skipped**.
