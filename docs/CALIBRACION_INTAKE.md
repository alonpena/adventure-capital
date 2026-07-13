# Hoja de intake — calibración de un caso

Fuente de verdad para crear una instancia. Sin estos números **medidos o
declarados por el cliente**, el veredicto no se presenta (garbage in →
veredicto Optimal pero inútil; caso real: Free The Mama con `frecuencia: 37`
que anulaba toda recompra).

Regla: cada número lleva su fuente (dato medido / estimación del founder /
supuesto del consultor). Los supuestos del consultor se marcan y se someten a
sensibilidad antes de presentar.

| # | Parámetro | Pregunta al cliente | Unidad | Trampa conocida |
|---|---|---|---|---|
| 1 | `ticket` | ¿Precio promedio de UNA venta? | USD | Confundir con LTV |
| 2 | `frecuencia` | ¿Cada cuántos meses recompra un cliente activo? | meses | **Si > horizonte, el modelo asume que NADIE recompra jamás** |
| 3 | `alpha` | De los que siguen activos, ¿qué fracción efectivamente recompra? | 0–1 | Confundir con retención |
| 4 | `churn_anual` | ¿Qué fracción de clientes pierdes al año? (por año 1, 2, 3) | 0–1 por año | Mezclar churn mensual con anual |
| 5 | `A_base` | Adquisición real/comprometida meses 1–12 | clientes/mes ×12 | Poner metas aspiracionales en vez de plan consensuado |
| 6 | `c_u` / `c_min` | Costo variable por servicio / costo fijo mínimo de operar | USD | Olvidar costos de fulfillment |
| 7 | Canal publicidad: `I_min–I_max`, `A_min–A_max` | Con inversión mínima X, ¿cuántos clientes/mes? ¿Y con máxima Y? | USD, clientes | La recta se ancla en estos 2 puntos: deben venir de gasto REAL observado. `A_ad_cap ≥ A_max` siempre |
| 8 | `VC` | Capital efectivamente disponible | USD | Incluir plata no comprometida |
| 9 | `meta`, `rem_v/l`, `com_v/l` | Solo si fuerza de ventas activa: productividad y remuneraciones reales | clientes/vendedor/mes, USD | meta=0.1 por typo hace inviable contratar |

## Chequeos pre-vuelo (automáticos o del consultor)

- `frecuencia > H` → advertir: cero recompra en todo el horizonte, ¿intencional?
- `A_ad_cap < A_min` → rechazado por validador (infactibilidad estructural).
- Piso del canal (`A_min`) vs techo de mercado meses finales → si piso > techo, infactible; revisar ambición del techo o piso del canal.
- Pico de adquisición aislado en m13 en resultados → artefacto de optimización (techo holgado), no plan ejecutable: revisar suavizado/techo antes de presentar.
