# Recourse y rolling horizon — extensión futura (no implementada)

Fecha: 2026-07-05 · Contexto: M4 actual es two-stage SAA con recourse limitado
(ADR 0004/0009): primera etapa = plan comercial único (PCA); segunda etapa =
variables financieras y escalones operativos por escenario. Recourse COMERCIAL y
rolling horizon quedan como extensión.

## Qué decisiones serían adaptativas

| decisión | hoy | con recourse pleno |
|---|---|---|
| Adquisición por canal m13–36 | first-stage única (here-and-now) | ajustable por escenario tras observar eficiencia realizada |
| Contrataciones V/L | first-stage | re-plan por período (contratar más si tracción alta, congelar si baja) |
| Inversión publicidad I_ad | first-stage | re-asignable por período/escenario |
| Escalones operativos, caja, funding | ya son recourse | igual |

## Qué información se revela por período

Eficiencia comercial realizada (clientes/vendedor efectivos), churn observado por
cohorte, caja efectiva. En rolling horizon: en cada t se observa el estado, se
re-resuelve el MILP con horizonte H−t y los parámetros re-estimados, se ejecuta
solo el primer mes — exactamente el ciclo "invertir por hitos / punto de equilibrio
por tramos" que describen los VCs (reunión 2026-07-01): el modelo re-planifica en
cada tramo de financiamiento.

## Por qué es académicamente correcto

Multistage stochastic programming: la política óptima es no-anticipativa —
decidir todo ex-ante (two-stage) es una cota inferior del valor de la política
adaptativa (VSS/EVPI cuantificables). Rolling horizon es la aproximación estándar
computable de multistage (política de re-optimización).

## Por qué NO antes del lunes

- Multistage exacto: árbol de escenarios ⇒ tamaño exponencial en etapas; con 5
  dimensiones inciertas y 24 meses es intratable con CBC.
- Rolling horizon: implementable (bucle de re-solve), pero exige re-estimación de
  parámetros por período + nueva capa de artefactos + validación — semanas, no horas;
  rompería la estabilidad de la entrega.
- Costo computacional: ~24 solves MILP por trayectoria simulada × N trayectorias
  (≥ horas por instancia con CBC).

## Qué decir en la defensa

El two-stage here-and-now es la elección conservadora correcta para valorizar un
COMPROMISO auditable (el VC financia un plan, no una política); recourse/rolling
horizon queda declarado como trabajo futuro con su justificación teórica (VSS) —
no como omisión.
