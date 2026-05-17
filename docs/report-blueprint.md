# Blueprint del Informe Estándar de Valorización

Estructura unificada para generar, a partir de una instancia YAML de Adventure Capital, un informe de valorización + planificación estratégica + unit economics con granularidad de página.

## Fundamentos

Tres fuentes consolidadas:

- **Metodología A. Maureira** — base teórica: 3 pilares (Modelamiento Financiero, Plan de Aceleración, Valorización VC) y 4 capas del MapValue (Variables de Entrada → Flujos Operativos → Resultados Financieros → Valorización).
- **AiJourney (marzo 2024)** — narrativa rica, gráficos por servicio, sensibilidad y breakeven.
- **SolutionOps Post-Money (abril 2026)** — formato moderno: tarjetas hero, tablas Año 1/2/3, comparativa de estrategias (PULL vs PUSH), matriz de sensibilidad WACC × Múltiplo, cap table pre/post-money.

## Convenciones globales

- **Idioma**: español.
- **Moneda**: USD nativo del modelo; al renderizar se muestran MUS$ (miles) si valor ≥ 1.000, USD$ en caso contrario. Las visualizaciones declaran la unidad.
- **Periodo**: meses; agregados anuales se muestran como Año 1, Año 2, …, Año N (no fechas calendario).
- **Tipografía**: hero (cifras 80–120pt), título sección (40–60pt), cuerpo (12–14pt).
- **Tema**: oscuro con acento ámbar para hitos PULL, cyan para alternativa PUSH/comparativa, rojo para egresos.
- **Footer**: `Confidencial · Adventure Capital · {{report_date}} · {{page}}`.
- **Origen de datos**: cada elemento referencia `instance.yaml`, `optimized_results.csv`, `dcf_*.csv`, `multiples_valuation.csv`, `unit_economics.csv` o cálculos derivados.

---

## Estructura del informe

Total objetivo: 36–48 páginas. Páginas opcionales marcadas con [OPT].

### Bloque 0 — Portada y referencia (pp. 1–4)

| # | Página | Tipo | Datos requeridos |
|---|---|---|---|
| 1 | **Portada** | Hero: nombre empresa, "Informe de Valorización", subtítulo con WACC y método, autor, fecha, sello confidencial | `instance.empresa.nombre`, `instance.empresa.rut`, `dcf.beta_anual`, `report.author`, `report.date` |
| 2 | **Glosario de monedas y unidades** | Tabla 2-col (símbolo / descripción) + 3 tiles (UF utilizada, tipo de cambio, fecha) | `instance.unidades` (CLP$, UF, USD$, MUS$, MM$), `instance.fx`, `instance.fecha_referencia` |
| 3 | **Índice** | Lista 2-col, número de página + título de sección | Generado del propio TOC |
| 4 | **Resumen ejecutivo (1-pager)** | 6 tiles grandes: Valor Post-Money, EBITDA año N, Ingresos año N, Inversión requerida, ROI inversionista, % a entregar | `dcf.valor_empresa`, `annual.ebitda[-1]`, `annual.ingresos[-1]`, `inversion.total`, `inversion.roi_x`, `cap_table.pct_inversionista` |

### Bloque 1 — Antecedentes generales (pp. 5–11)

| # | Página | Tipo | Datos requeridos |
|---|---|---|---|
| 5 | **Carátula sección 01** | Numero gigante "01" + título "Antecedentes Generales" + subtítulo empresa | `instance.empresa.nombre` |
| 6 | **¿Qué hace la empresa?** | 2 columnas: descripción narrativa + 3 bullets de beneficios | `instance.empresa.descripcion`, `instance.empresa.beneficios` |
| 7 | **Valores / propuesta** | 3–4 tarjetas con principios | `instance.empresa.valores[]` |
| 8 | **Clientes / Target Market** | Tabla segmentos B2B (ID, rango, nombre) + diagrama de tipos de empresa | `instance.target_market` |
| 9 | **Historia y equipo** [OPT] | Timeline horizontal + grid de fotos/roles | `instance.equipo[]`, `instance.timeline[]` |
| 10 | **Modelo de negocio** | 2 columnas: Modelo principal (ticket primario) vs complementario | `instance.modelo_negocio.principal`, `instance.modelo_negocio.complementario` |
| 11 | **Problemas que resuelve** [OPT] | Cards: problema → impacto cliente | `instance.problemas[]` |

### Bloque 2 — Plan comercial y operacional (pp. 12–17)

| # | Página | Tipo | Datos requeridos |
|---|---|---|---|
| 12 | **Propuesta central** | Hero: nombre del producto/servicio + ticket promedio (USD/mes) + frecuencia | `instance.servicios[0]` (ticket, frecuencia) |
| 13 | **Pricing por plan** | 3-col tarjetas: para cada `servicios[*]` mostrar ticket UF/USD, frecuencia, condiciones | `instance.servicios[].{nombre,ticket,frecuencia}` |
| 14 | **Meta mensual por segmento** | Stacked area chart (12 meses × servicios) con totales debajo | `instance.servicios[].A_base` |
| 15 | **Meta de ventas año 1** | Tabla 12 meses × servicio + suma + chart | Derivado de `A_base` |
| 16 | **Estructura comercial** | Organigrama (CCO → KAM → Partners) + tarjetas con remuneraciones y comisiones | `instance.{rem_v,rem_l,com_v,com_l,meta,sup}` |
| 17 | **Fuentes de adquisición** | 3-col tarjetas: directa / partners / recurrencia | Derivado de `meta`, `com_l`, `frecuencia`, `alpha` |

### Bloque 3 — Modelamiento financiero (Flujos del MapValue) (pp. 18–28)

Esta es la columna vertebral del modelo. Cada flujo es una página dedicada.

| # | Página | Tipo | Datos requeridos |
|---|---|---|---|
| 18 | **Carátula 02 — Modelamiento financiero** | Título grande + cita metodológica "Resultado matemático: EBITDA y Capital de Trabajo" | — |
| 19 | **Flujo 1 — Clientes** | Fórmula `Stock = Σ(Adquisición) × (1−Churn)`, tabla anual (adquisición, churn %, stock), 2 tiles (Stock año N, Churn año 1 vs año N) | `optimized_results` (A[s,t]), `instance.churn_anual`, derived stock |
| 20 | **Flujo 2 — Servicios** | Fórmula `Volumen = Stock × Recurrencia`, tabla por plan (horas/mes × precio), tiles (ciclo productivo, capacidad año N) | `optimized_results.Q[s,t]`, `instance.u_max`, `instance.ciclo_op` |
| 21 | **Flujo 3 — Ingresos** | Stacked bar 12-meses año 1 + tabla anual por servicio + tiles (ARR%, ticket promedio, DaaS sobre total) | `optimized_results.I[s,t]`, `dcf.annual.ingresos` |
| 22 | **Gross Margin** | Tabla `Componente × Año` + 3 barras horizontales año1/año2/año3 + tile GP promedio | `optimized_results.Cost_op[s,t]`, `instance.servicios[].c_u/c_min`, gross_profit derived |
| 23 | **Flujo 4 — CAC** | Tabla componentes (fuerza venta, publicidad, otros, comisión terceros) × año + tiles (CAC promedio, CAC payback, LTV/CAC) | `optimized_results.CAC[t]`, unit_economics.{CAC,LTV} |
| 24 | **Flujo 5 — Costos operacionales** | Bullets de componentes (c_u, c_min, capacidad) + tabla floor cost vs variable + tile GP % | `instance.servicios[].{c_u,c_min,u_max}`, derived |
| 25 | **Administración y RR.HH.** | Tabla planilla mensual por rol (g_adm + RRHH_mensual desglosado por año) + tile total mensual | `instance.g_adm`, `instance.RRHH_mensual` |
| 26 | **EBITDA — P&L Anual** | Tabla P&L: Ingresos, (-) Costos op., GP, (-) GAV, (-) Planilla, EBITDA puro, (-) CAC, EBITDA + tile EBITDA año N + margen % | `dcf_annual_summary.csv` |
| 27 | **Capital de trabajo** | Fórmula `CT = Ciclo Prod × Cash Burn Rate`, tabla 3 años, tile Bootstrapping total | `unit_economics.{cash_burn_rate,bootstrapping,working_capital}` |
| 28 | **Cashflow mensual (chart)** | Line chart: EBITDA mensual + Caja acumulada (eje secundario), zona negativa resaltada | `dcf_cashflow.csv` |

### Bloque 4 — Valorización (MapValue) (pp. 29–36)

| # | Página | Tipo | Datos requeridos |
|---|---|---|---|
| 29 | **Carátula 03 — Valorización** | Título + subtítulo metodológico (CAPM, WACC ajustado) | — |
| 30 | **Tasa de descuento (WACC)** | Fórmula `Ke = Rf + β(Rm − Rf) + RP` + tabla componentes (BCP, US-T, IPSA, β, RP) + tile WACC final | `instance.dcf.{beta_capm,Rf,Rm,country_risk,sector_beta}`, calc beta |
| 31 | **Horizonte de evaluación** | Fórmula `H = 1/WACC` + tile horizonte años · meses, anotación sobre 36 meses explícitos | `instance.H`, `instance.beta` |
| 32 | **Valor terminal** | 2 columnas: método usado (1× EBITDA año N) vs Gordon growth (referencia) | `dcf.valor_desecho`, derived gordon |
| 33 | **Unit economics por cliente** | Cascada: ARPU → LTR → LTV → Net LTV, 4 tiles a la derecha (ticket, recurrencia, LTV, Net LTV) | `unit_economics.csv` |
| 34 | **Del cliente al modelo completo** | Visual `Net LTV × Clientes − Gastos Adm = EBITDA` + tile breakeven (#clientes y meses) | unit_economics, dcf_annual |
| 35 | **MapValue (póster)** | Diagrama causal de 4 capas (variables entrada → flujos → resultados → valorización) con flechas y valores nominales | Composición de todos los outputs |
| 36 | **Valor Post-Money** | Hero gigante: valor empresa MUS$ + 4 tiles (Inversión requerida, % a entregar, ROI inversionista, EBITDA año N) | `dcf.van`, `inversion.total`, `cap_table.pct`, `roi` |

### Bloque 5 — Inversión, Cap Table y comparativas (pp. 37–42)

| # | Página | Tipo | Datos requeridos |
|---|---|---|---|
| 37 | **Inversión inicial requerida** | 1 o 2 columnas (PULL solo / PULL vs PUSH si hay alternativa): hero MUS$ + breakdown (capital trabajo, bootstrap, % propiedad, ROI) | `inversion.{total,working_capital,bootstrap}` |
| 38 | **Roadmap de inversión** | Timeline 4 hitos: Inversión inicial → Fuerza venta → Gastos admin → Contingencia, con %/MUS$ | `inversion.uso_capital[]` |
| 39 | **Cap Table pre/post-money** | Tabla 5-col (Accionista, Common, Total, Fully Diluted, %) pre-money + 2 tiles (Participación inversionista PULL vs PUSH si aplica) | `instance.cap_table.pre[]`, `dcf.valor_empresa` |
| 40 | **Comparativa de estrategias** [OPT] | Tabla de doble columna PULL vs PUSH × {Ingresos, EBITDA, CAC, Inversión requerida, ROI} + diferencias | Solo si se evaluaron 2 escenarios |
| 41 | **Tesis VC vs Modelo** | Tabla `Variable | Modelo | Tesis VC | Estado (✓/→)` por: churn, crecimiento, LTV/CAC, %Inv/Valor, %EBITDA año 1 | unit_economics + thresholds metodología |
| 42 | **Floor Value y ajustes finales** [OPT] | Fórmula `Valor Final = VAN + Floor − Pasivos`, tabla descomposición | `dcf.van`, `instance.floor_value`, `instance.pasivos` |

### Bloque 6 — Sensibilidad y anexos (pp. 43–48)

| # | Página | Tipo | Datos requeridos |
|---|---|---|---|
| 43 | **Sensibilidad — Matriz WACC × Múltiplo EBITDA** | Heatmap/tabla 7×7 (WACC en filas, múltiplo en columnas) con caso base marcado | Cálculo paramétrico del valor con `dcf` y `multiples_valuation` |
| 44 | **Sensibilidad — Variables operativas** | Tabla: Variable, Actual, Análisis, Valor resultante, Efecto % | Reruns con `churn`, `frecuencia`, `tax`, `castigo_riesgo` |
| 45 | **Variables para EBITDA = 0** | Tabla: Variable, Actual, Mínimo para EBITDA=0, Variación tolerable | Búsqueda inversa sobre `clientes`, `ticket`, `CAC`, `recurrencia` |
| 46 | **Dashboard de unit economics** | Grid 3×4 de tiles con todos los unit economics clave | `unit_economics.csv` completo |
| 47 | **Anexo — Supuestos del modelo** | Lista numerada de supuestos derivados de la instancia YAML | Volcado anotado de `instance.yaml` |
| 48 | **Anexo — Equipo asesor / créditos** [OPT] | Bio y trayectoria | `report.team[]` |

---

## Datos requeridos en la instancia YAML

Extensiones al schema actual (`configs/base.yaml`) para alimentar el informe:

```yaml
# campos del modelo (ya existen)
H: 36
VC: 209000
beta: 0.3544
servicios: [...]
# ... resto del modelo

# nuevos bloques solo para el informe
empresa:
  nombre: SolutionOps SpA
  rut: 77.145.798-3
  descripcion: |
    Multi-line markdown.
  beneficios: [punto1, punto2, punto3]
  valores: [{titulo: ..., descripcion: ...}]
  pais: Chile

target_market:
  tipo: B2B
  segmentos:
    - {id: A, rango_min: 1, rango_max: 25, nombre: MiPyME}

modelo_negocio:
  principal:   {nombre: DaaS, descripcion: ..., ticket_descripcion: "50–120 UF/mes"}
  complementario: {nombre: Asesorías, ...}   # opcional

equipo:                        # opcional
  - {nombre: ..., cargo: ..., foto: path/to.png}

problemas:                     # opcional
  - {titulo: ..., descripcion: ...}

unidades:
  - {simbolo: CLP$, descripcion: Pesos chilenos}
  # ...
fx:
  uf_clp: 40000
  usd_clp: 900
fecha_referencia: 2026-04-01

dcf:
  beta_capm: 1.05
  Rf_local: 0.0486          # BCP 3 años
  Rf_us:    0.0384          # US Treasury 3 años
  Rm:       0.20            # IPSA anual
  country_risk: 0.0102
  sector: "IT Services / Software (Damodaran)"
  castigo_riesgo: 0.10
  valor_desecho_metodo: ebitda_multiple   # | gordon
  ebitda_multiple: 1.0

inversion:
  total: 170900           # MUS$170,9 — bootstrapping
  uso_capital:
    - {hito: "Inversión Inicial",  monto: 11200,  pct: 0.065}
    - {hito: "Fuerza de Venta",    monto: 45200,  pct: 0.264}
    - {hito: "Gastos Adm.",        monto: 98100,  pct: 0.574}
    - {hito: "Contingencia",       monto: 16400,  pct: 0.097}

cap_table:
  pre:
    - {accionista: "Founder 1 (CEO)", common: 72.5, fully_diluted: 0.604}
  post_money_dilution_target: 0.10   # % máx a entregar

pasivos:        0
floor_value:    0           # activos intangibles

report:
  author: "Adventure Capital Chile"
  date: 2026-04-01
  scenario:  base            # base | conservador | upside
  comparativa:               # opcional, segunda corrida para comparar
    nombre: PUSH
    config_ref: configs/push.yaml
```

## Outputs requeridos del pipeline

Ya producidos:

- `optimized_results.csv` — series mensuales A[s,t], C[s,t], R[s,t], Q[s,t], I[s,t], Cost_op[s,t], CAC[t], EBITDA[t], Caja[t]
- `fixed_cashflow.csv` — meses 1–12 (periodo fijo)
- `dcf_cashflow.csv` — flujo mensual descontado
- `dcf_annual_summary.csv` — agregado anual
- `multiples_valuation.csv` — valorización por múltiplos
- `unit_economics.csv` — todos los unit economics calculados

Faltantes a producir (extensión del pipeline):

- `sensitivity_wacc_multiple.csv` — matriz N×M paramétrica
- `sensitivity_variables.csv` — barrido sobre churn, frecuencia, tax, castigo
- `breakeven_variables.csv` — variable mínima para EBITDA=0
- `mapvalue.json` — snapshot de las 4 capas con valores y conexiones

## Pipeline de generación

```
model_config.yaml ──► run_pipeline() ──► outputs/<run>/{csvs}
                                               │
                                               ▼
document.yaml + blueprint.md ──► build_report_data_package()
                                               │
                                               ▼
                         outputs/<run>/report_data.json
                         outputs/<run>/artifacts_manifest.json
                         outputs/<run>/figures/*.png
                                               │
                                               ▼
                                  render_report(outputs/<run>/)
                                               │
                                               ▼
                                  outputs/<run>/report.html
                                  outputs/<run>/report.pdf  [opcional]
```

`build_report_data_package` normaliza los CSV de optimización/valorización, el YAML documental y el blueprint en un paquete intermedio trazable.

`render_report` consume principalmente `report_data.json` y `artifacts_manifest.json`, resuelve las secciones del blueprint y compone el HTML/PDF (sugerencia: WeasyPrint + plantillas Jinja con tema oscuro a la SolutionOps; gráficos pre-renderizados como PNG con Matplotlib en outputs/figures/).

## Especificaciones de visualizaciones

Para cada gráfico el blueprint declara:

- **chart_id** — identificador único en outputs/figures/
- **tipo** — bar | stacked_bar | stacked_area | line | heatmap | sankey | waterfall | timeline
- **fuente** — CSV + columnas
- **eje x / eje y** — y unidades
- **estilo** — paleta dark + ámbar, grid sutil, sin recuadro, etiquetas inline

Catálogo mínimo:

| chart_id | tipo | página |
|---|---|---|
| `acquisition_year1` | stacked_area | 14, 15 |
| `revenue_breakdown_3y` | stacked_bar | 21 |
| `cashflow_monthly` | line dual-axis | 28 |
| `client_revenue_36m` | stacked_area | 28 |
| `cac_components` | horizontal_bar | 23 |
| `gross_margin_progression` | horizontal_bar | 22 |
| `sensitivity_heatmap` | heatmap | 43 |
| `unit_economics_grid` | tile_grid | 46 |
| `mapvalue_diagram` | sankey/flow | 35 |
