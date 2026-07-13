# Free The Mama — bitácora de calibración (2026-07-12/13)

Registro de qué cambió cada variante y por qué. **La instancia original del
cliente no fue modificada** (`inst_20260710-125036_30f45c5d` y sus 9 copias
idénticas del 10-07). v3 y v4 son instancias NUEVAS creadas para diagnóstico.

## Original (del cliente) — Infactible

`A_ad_cap: 0` con publicidad activa y `min_share: 1.0`: el tope anulaba el
único canal. Además `A_min: 373` (piso de la recta desde el mes 13) supera el
techo de mercado de los meses 25–36 (307–345). Dos contradicciones
estructurales; el solver no miente: no existe plan que las satisfaga.

## v3 "(factible)" — Optimal, VAN −206K

Cambios respecto al original, mínimos para demostrar que el pipeline funciona:
- `A_ad_cap: 0 → 13000` (= A_max; hoy este valor se deriva solo y ya no se pide).
- `A_min: 373 → 100` — **parche técnico mío, no dato del cliente**: baja el
  piso del canal bajo el techo de mercado para restaurar factibilidad.

Lectura: caso resoluble pero débil (churn 78%, ROI 1.1×, ingresos 0.86×).
Advertencia: `frecuencia: 37 > H=36` significa cero recompra en el horizonte —
si el negocio es venta única real, es correcto; si es recurrente, invalida todo.

## v4 "(venta única, sin techo)" — Optimal, VAN +10.4M ← DESORBITANTE

Cambios respecto al original:
- `A_ad_cap: 0 → 13000` (igual que v3).
- `A_min` vuelve al valor del cliente (373).
- `acquisition_ceiling.enabled: true → false` — hipótesis: si no hay recompra,
  el techo anclado en stock (3×) no aplica.

**Por qué explotó:** sin techo, el único freno era la recta publicitaria, y la
recta del YAML dice que con I_max=8.000 USD/mes entran 13.000 clientes/mes →
CAC implícito **$0,62** con ticket $59. El optimizador compra el máximo todos
los meses: 316.470 clientes en 36 meses. No desconfiguré el modelo — la recta
del cliente es la que imprime dinero cuando nada la acota.

## Conclusión para recalibrar (a mano, por Alonso/Alejandro)

Los tres números que deciden el caso, en orden:
1. **Recta publicitaria real**: dos puntos observados (gastamos X → entraron Y).
   Con CAC realista el VAN cae a tierra solo.
2. **Techo/saturación**: si venta única, el tope del canal (A_ad_cap explícito,
   mercado direccionable) reemplaza al techo por stock. Es pregunta de mercado,
   no técnica.
3. **frecuencia**: confirmar venta única (37) o recurrencia real (1–3).

Ver `docs/CALIBRACION_INTAKE.md` para el intake completo.
