# Guía de estilo UI — Adventure Capital

Identidad: **Memorando / Investment Research Console** (ADR 0008 §6 enmendado).
La app es un documento de trabajo financiero, no un dashboard. Norte visual:
memo de equity research + tabla booktabs de paper académico.

## Paleta (no ampliar)

| Rol | Hex | Uso |
|---|---|---|
| Papel | `#F7F5F0` | fondo |
| Panel | `#FCFBF8` | tarjetas, expanders |
| Tinta | `#21201C` | texto, reglas fuertes |
| **Oxblood** | `#7A2E2E` | ÚNICO acento: CTA, nav activa, serie primaria, focus |
| Slate | `#3E5C76` | serie secundaria de gráficos, nada más |
| Verde bosque / ocre / rojo apagado | `#2E6B4F` `#9A6A00` `#A32D2D` | solo estados (ok/warn/bad) |

Regla: si un elemento nuevo "necesita" un color nuevo, está mal diseñado.
El acento se gana: máximo un elemento oxblood por bloque visual.

## Tipografía

- **Serif (Georgia)**: títulos y CIFRAS (los números son protagonistas — siempre
  `tabular-nums`).
- **Sans (sistema)**: chrome, labels, ayuda. Labels de sección en
  versalitas-espaciadas (`h3` actual).
- **Mono**: ids, hashes, rutas de artefactos. Nunca prosa.
- No añadir familias. Jerarquía por tamaño/peso/regla, no por color.

## Distribución

- Una columna dominante; columnas múltiples solo para números hermanos (KPIs,
  cajas por año). Máx 4.
- Jerarquía documental: masthead con regla 2px → secciones con regla fina →
  contenido. El ojo baja como en un memo.
- Progresión de formulario = narrativa de decisión: Caso → Negocio → supuestos.
  Lo raramente tocado, colapsado (nunca oculto sin señal).
- Cada bloque de datos cierra con su `source_caption` (trazabilidad visible =
  la marca del producto).

## Movimiento

- Solo transiciones 150–200ms (hover, focus, fade-in de entrada). Nada pulsa,
  nada gira, nada rebota. `prefers-reduced-motion` siempre respetado.

## Copy

- Español de negocio primero, símbolo del modelo entre paréntesis: "Tasa de
  recompra (alpha)". Jerga de método (LHS, SAA, CBC) solo en captions/tooltips.
- Errores: qué pasó + qué hacer, sin traceback a la vista (detalle técnico en
  expander).
- Estados vacíos siempre dicen el siguiente paso ("Crea una instancia desde…").

## Anti-patrones (rechazados explícitamente)

- Dark theme con acentos neón ("AI dashboard") — rechazado 2026-07-05.
- Cards con sombras fuertes, gradientes, glassmorphism.
- Emojis como señal de estado (usar badges).
- Más de un CTA primario por pantalla.
