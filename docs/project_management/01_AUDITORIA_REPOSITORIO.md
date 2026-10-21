# Auditoría independiente de Adventure Capital

Fecha: 16-10-2026. Línea base: `master`, commit `6f3a8b93be9aff2b5022688d7b9589e40dd798ea`. Alcance: repositorio local, ejecución de pruebas, inspección estática y sondas sintéticas. No se modificó código productivo. La posterior aclaración del solicitante prioriza reparto de trabajo, empresa de software y costo de oportunidad sobre detalle presupuestario.

## Dictamen

Existe un motor Python modular, con optimización determinista y estocástica, reglas de due diligence, generación de informes y una interfaz Streamlit. Es una base reutilizable para un servicio de consultoría asistida. **No es todavía un SaaS multiusuario operable con garantías de aislamiento y operación.** No se justifica reconstruir todo el motor; sí corregir brechas científicas específicas y construir la capa de producto a su alrededor.

Las pruebas existentes respaldan comportamiento programado; no acreditan validez económica de los supuestos, seguridad de producción ni aceptación comercial. La empresa debería concentrarse en ingeniería de producto y Alonso en correctitud, metodología y aceptación técnica.

## Evidencia y verificaciones

| Verificación | Resultado observado | Alcance / limitación |
|---|---|---|
| Estado inicial de Git | Limpio; 283 archivos versionados | No se alteraron ramas ni worktrees |
| Suite completa, Python 3.12.13 | **194 passed, 80.312 warnings, 59,27 s** | Entorno local existente; ver `evidence/pytest.xml` y `pytest.log` |
| Ruff sobre código y tests originales | Pasa | `evidence/ruff.txt`; no mide corrección científica |
| Primera ejecución sin ajustes del entorno | Fallos CLI por caché `uv` restringida y PDF por descubrimiento de `libgobject` | Repetición con caché temporal, `UV_NO_SYNC=1` y biblioteca Homebrew resolvió los fallos; no se atribuyen al algoritmo |
| Validación negativa | Acepta alpha=2, ticket=NaN, churn=1,2 y adquisición negativa | Sondas directas a `validate_config`; `evidence/probes.json` |
| Paridad meses 1–12, canales mixtos | Diferencias en CAC y EBITDA con solución Optimal | Detalle abajo; no cubierto por la suite actual |
| Escape HTML y rutas de imágenes | Autoescape desactivado para `report.html.j2`; incrusta marcador fuera de carpeta del informe | Prueba inocua con archivo sintético temporal, sin acceso a secretos ni explotación de un servidor |
| Cobertura porcentual | **No determinada** | `coverage` no está instalado; 194 tests no equivalen a un porcentaje de cobertura |
| UI | Tests de importación, helpers y estado simulado | `tests/test_streamlit_app.py:1` declara «no browser»; no es prueba E2E de navegador |
| Producción, carga y pentest | **No determinados** | No se accedió a servidor, cuenta cloud, observabilidad ni usuarios reales |
| Instalación desde cero | No ejecutada | Se usó `.venv` existente, sin descargar/instalar dependencias; Excel detecta dependencia no declarada |

Comando de repetición usado:

```bash
UV_CACHE_DIR=/tmp/adventure-pm/uv-cache UV_NO_SYNC=1 \
DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib \
.venv/bin/pytest -q --tb=short -p no:cacheprovider \
  --junitxml=docs/project_management/evidence/pytest.xml
```

`tools/audit_probes.py` reproduce las sondas adicionales. `UV_NO_SYNC=1` evita que los subprocesos CLI intenten modificar el entorno; por ello esta verificación no sustituye un build limpio en CI.

## Inventario y arquitectura efectiva

| Área | Elementos observados | Evaluación |
|---|---|---|
| Empaquetado | `pyproject.toml`, `uv.lock`, `.python-version`, `src/adventure_capital` | La migración básica del notebook ya existe; no debe presupuestarse de nuevo |
| Modelo | `config.py`, `instance.py`, `financial_model.py`, `model.py`, `results.py` | Preprocesamiento, etapa fija y MILP separados; PuLP/CBC concentrado en modelo, con otro modelo en `stochastic/` |
| Análisis | `valuation.py`, `unit_economics.py`, `growth_diagnostics.py`, `calibration/`, `due_diligence/`, `stochastic/` | Reutilizables con contratos y validación económica |
| Informes | `reporting.py`, `standard_report/`, `simple_report.py`, `postprocess.py`, plantillas Jinja/CSS, esquemas YAML | Generación abundante; mantener una fuente canónica de cifras |
| Entradas | `configs/base.yaml`, ejemplos de canales/capital de trabajo, `configs/gold/`, `reports/` | Ejemplos no son datos de mercado validados |
| Interfaz | `app.py`, páginas/helpers en `streamlit_pages/` | Gestión local de casos, ejecución y exploración; existe UI, no partir de pantalla en blanco |
| Persistencia / orquestación | `workflow_registry.py`, JSON/YAML/CSV bajo `outputs/instances` y `outputs/executions` | Historial local con hash; no base transaccional multiempresa |
| Pruebas | 35 archivos `tests/test_*.py`, 194 casos ejecutados | Configuración, modelo, informes, escenarios, contratos y wiring UI; faltan límites adversos y E2E SaaS |
| CI | `.github/workflows/ci.yml` | GitHub Actions instala uv/Python 3.12, ejecuta Ruff y pytest en PR/push master; no CD ni evidencia de ejecución remota actual |
| Despliegue | `packages.txt`, app Streamlit, rama `deploy-production` | No se encontró infraestructura como código ni manifiesto de despliegue reproducible en master |
| Experimentos | `scripts/benchmark_instances_v1.py`, `growth_band_experiment.py`, `objective_sweep.py`, `threshold_analysis.py`, diagnósticos | Material reutilizable para validación, no ensayos de rendimiento SaaS ni benchmarks sectoriales |
| Artefactos | `benchmark_v0/`, `benchmark_v1/`, `docs/defense_audit/`, archivo ZIP y material de defensa | Evidencia histórica; no se asumió que estuviera recalculada o vigente |
| Documentación | `CONTEXT.md`, `docs/model.md`, `docs/api.md`, blueprint, planes y ADR | Rica, con divergencias; `PLAN.md` referido por AGENTS no existe en master |
| Legacy | Notebook en `legacy/` | Referencia histórica, no fuente operativa actual |

Flujo observado: config → validación/preprocesamiento → cashflow fijo y MILP → resultados → DCF/unit economics → calibración/DD → evaluación/optimización estocástica opcional → artefactos → reportes → UI. `run_pipeline(baseline_only=False)` delega a assessment y **crea `runs/` si no recibe output_dir** (`pipeline.py:35–44`), en tensión con la promesa general de API sin escrituras. El parámetro `document_path` también cambia descuento y método residual antes del solve (`pipeline.py:57–95`): los documentos no son siempre presentación pura.

### Ramas inspeccionadas

Comparación de referencias **locales**, sin fetch ni checkout. Los números son commits exclusivos `master / otra rama`, no conteo de funcionalidades:

| Rama | Divergencia | Consecuencia |
|---|---:|---|
| `deploy-production` | 25 / 0 | Ancestro de master; el nombre no prueba despliegue vigente |
| `demo-integrated-growth-ui` | 27 / 0 | Integrada históricamente; no hay que reimplementar por su nombre |
| `feat/stochastic-model` | 98 / 0 | La capacidad estocástica ya llegó a master |
| `ui-pro` | 45 / 3 | Tiene cambios exclusivos; revisar selectivamente, no merge automático |

También existen ramas de entrega, valoración y refinamiento. No se certificó cada commit histórico ni el estado remoto actual. La planificación usa master; adopción de cambios de `ui-pro` exige revisión y pruebas. Worktrees de otras ramas se dejaron intactos.

## Matriz de funcionalidades

Estados: **V** = Implementada y verificada en el alcance descrito; **P** = Implementada parcialmente; **I** = Implementada sin verificación suficiente; **D** = Diseñada, pero no implementada; **A** = Ausente en la línea base inspeccionada; **N** = No determinada. P0 indispensable/bloqueante; P1 importante; P2 posterior. «Verificada» se refiere a pruebas locales, nunca a calidad productiva general.

| Módulo | Funcionalidad | Estado real | Evidencia | Limitaciones | Trabajo pendiente | Prioridad |
|---|---|---|---|---|---|---|
| A | Captura de parámetros | P | `instance_manager_page.py`; tests Streamlit | YAML/formulario local; sin E2E | UX guiada y errores por campo | P0 |
| A | Validación de dominio | P | `config.py:166–203`; sondas | No finitud/rangos completos | T08–T09 | P0 |
| A | Adquisición fija / optimizada | V | `instance.py`, `model.py`; phase1/2 y channels tests | Base 12 meses; H≥14; planes condicionados a supuestos | Mantener regresión y explicar límite | P0 |
| A | Cohortes / segmentación | P | `instance.py`, `financial_model.py` | Cohortes por servicio; no segmentos conductuales cruzados | Delimitar alcance de segmentación | P1 |
| A | Retención y churn | V | `phi`, churn por servicio; model_behavior tests | Exógeno; no estimador estadístico | Calibración con datos observados | P1 |
| A | Reactivación | A | Sin estado/transición de reactivación en cohortes | Recurrencia no equivale a reactivación | Diseñar sólo con caso comercial | P2 |
| A | Nuevas ventas, recurrencia y servicios | V | `financial_model.py:60–76`; phase1/2 | α en ventana; supervivencia exógena | Pruebas de unidades y límites | P0 |
| A | Ingresos | V | `ticket × Q`; phase3/model_behavior | Precio constante; no cobranza diferida | Mantener y explicitar | P0 |
| A | Pricing dinámico | A | `ticket` constante en modelo | Modificar input no optimiza precios | Diferir elasticidad/pricing endógeno | P2 |
| A | CAC por canal | P | `financial_model.py:81–104`, `model.py:173–269` | Divergencia de etapa fija con mix | T10 | P0 |
| A | Publicidad / eficacia comercial | P | Canales, recta publicidad, límites y tests | Relación paramétrica, no atribución causal | Evidencia externa y calibración | P1 |
| A | Costos unitarios y escalonados | V | `max` y epígrafes; ADR0001; tests | Piso, no fijo+variable | Preservar decisión y documentar casos | P0 |
| A | RRHH / administración | P | Sellers/leaders, RRHH y g_adm | No nómina ni contratos laborales completos | Validar interpretación y unidades | P0 |
| A | Caja | P | `model.py:348–359`, cash floor tests | EBITDA acumulado +VC; no todos los flujos de tesorería | T11–T12 | P0 |
| A | Capital de trabajo | P | `unit_economics.py:139`, suelo −VC | Proxy burn×ciclo y restricción de caja; no DSO/DPO/inventario | Definir método y rotular limitaciones | P0 |
| B | Escenario base / crecimiento | V | Pipeline/MILP; phase2 y behavior tests | No predicción garantizada | Envolver en servicio aislado | P0 |
| B | Restricciones de capacidad, caja y crecimiento | V | `model.py`; ceiling/envelope/commitment tests | Techo/objetivo exógeno influye en resultado | Mostrar restricciones activas y fuente | P0 |
| B | Mínimo para equilibrio | P | `sensitivity.py:116`, unit economics | Cálculo inverso agregado, no óptimo mínimo factible | Etiquetar; nuevo problema sólo después | P1 |
| B | Máxima utilización antes de escalón | P | Capacidades y escalones en MILP | No servicio específico con ese objetivo | Métrica diagnóstica primero | P2 |
| B | Financiamiento mínimo | P | `solve_with_working_capital`, elastic floor | Minimiza suma de shortfalls; no ticket óptimo mínimo | No venderlo como mínimo requerido | P0 |
| B | Modificar inversión/salarios/costos/precios | P | YAML/formulario y reruns | Se puede recalcular; no negociación colaborativa | Versiones y comparación T16/T21/T27 | P0 |
| B | Sensibilidad determinista | P | `standard_report/sensitivity.py` | Perturbaciones de totales; no reoptimiza | Separar aproximación y rerun | P1 |
| B | Evaluación estocástica de plan | V | `stochastic/evaluate.py`; stochastic tests | Muestra y distribuciones asumidas | Validar calibración/estabilidad T14 | P1 |
| B | Optimización estocástica | P | `stochastic/model.py:424–435`; tests | SAA mean-CVaR; paridad con M1 no acreditada globalmente | T13; acceso experimental | P1 |
| B | Optimización robusta min-max / DRO | A | ADR0004/0011 y formulación SAA | Diagnóstico de robustez no es optimización robusta | Fuera del MVP | P2 |
| B | Burn rate / runway | P | `unit_economics.py:58–100` | Razones con caja/EBITDA; depende de definición | Validar signos, no confundir runway con pronóstico | P0 |
| B | Comparación de escenarios | P | Artefactos/runs, vistas y reportes | No gestor SaaS versionado y homogéneo | T16/T21/T27 | P0 |
| C | Consistencia aritmética | V | `standard_report/consistency.py`; consistency tests | Sólo identidades implementadas | Ampliar a paridad entre etapas | P0 |
| C | Supuestos cuestionables / feedback | P | `calibration/checks.py`, `due_diligence/rules.py` | Heurísticas y umbrales metodológicos | Documentar fundamento y excepciones | P0 |
| C | Recomendaciones y reevaluación | P | `calibration/suggestions.py`, DD workflow | Reglas; cambios deben ser aceptados por experto | Capturar decisión y rerun trazable | P0 |
| C | Trazabilidad | P | `workflow_registry.py:41`, manifests | Hash y archivos; no audit trail multiusuario | Actor, versión, acceso y cambio inmutable | P0 |
| C | Explicabilidad | P | Fórmulas, narrativa parametrizada y reportes | No explicación completa de causalidad/óptimo | Advertencias y restricciones activas | P1 |
| C | Integridad de datos | P | Esquemas/validación; config congelada | Sin transacciones/tenancy; valores inválidos pasan | T09/T20/T21 | P0 |
| C | Benchmark sectorial externo | A | Configs gold y benchmarks son casos técnicos | Sin proveedor/versionado de datos sectoriales | Fuentes licenciadas y comparabilidad | P2 |
| D | Proyecciones financieras | V | CSV mensuales/anuales y tests | Proyecciones condicionadas, no estimaciones empíricas | Validación comercial del lenguaje | P0 |
| D | DCF | P | `valuation.py:57–105`; valuation tests | Proxy EBITDA después de impuestos; −VC; terminal anualizado | T11–T12 | P0 |
| D | Múltiplos | V | `calculate_multiples_valuation`; phase3 | Multiplicadores dados, sin comparables externos | Fechar fuente si se usa como mercado | P1 |
| D | Unit economics | P | `unit_economics.py`; tests | LTV suma servicios como cesta; denominadores/modelo simplificados | Definir cliente, cesta y CAC comparable | P0 |
| D | Visualización / reporte ejecutivo | V | Matplotlib, Plotly, Jinja; tests phase4/5 | Verificación estructural, no QA editorial completo | T29/T36 y seguridad | P0 |
| D | PDF | V | Suite con bibliotecas nativas disponibles | Dependencias nativas; fallback Chrome específico Mac | Imagen de ejecución reproducible | P0 |
| D | CSV/JSON/HTML | V | Artifact contracts y phase5 | No autorización por usuario | Descargas privadas | P0 |
| D | XLSX | I | `components.py:547–555` | `openpyxl` no declarado en pyproject/lock | Declarar/aislar exportador y probar instalación limpia | P0 |
| E | UI / experiencia | P | `app.py`, páginas, guía de estilo | No evaluación de tareas con clientes | UX desde S3, no mes 7 | P0 |
| E | Autenticación | A | Sin proveedor/login en app/registry | Session state no autentica | T20/T24 | P0 |
| E | Roles / organizaciones | A | Registry sin ownership | Casos compartidos en filesystem | Modelo de autorización T20 | P0 |
| E | Persistencia / historial | P | JSON y directorios locales | Sin DB transaccional ni auditoría de accesos | T21 | P0 |
| E | Orquestación de módulos | V | Pipeline, registry y tests workflow | Ejecución local; no cola durable | Adaptador de jobs | P0 |
| E | API Python / CLI | V | `pipeline.py`, `cli.py`; tests | Excepción a no-write en assessment | Aclarar contrato, versionar | P0 |
| E | API HTTP | D | ADR0017 | Extracción propuesta, sin endpoints productivos | T06/T20–T23 | P0 |
| E | Trabajos asíncronos durables | A | Llamadas síncronas UI/registry | Proceso navegador no es worker durable | T22 | P0 |
| E | Hosting productivo actual | N | Rama deploy y packages | No evidencia de servidor/cuentas/SLA | Inventario al contratar | P0 |
| E | Seguridad SaaS | P | YAML safe_load; mecanismos locales | Hallazgos HTML/rutas y sin tenancy | T28/T34/T37 | P0 |
| E | Logs / monitoreo | P | Estados y metadatos de ejecuciones | Sin alertas centralizadas ni métricas de servicio | T31 | P0 |
| E | Facturación / consumo | A | Sin ledger ni cobro | Cobro por consulta es hipótesis | Cuotas + cobro manual primero | P1 |
| E | LLM / agentes | D | Narrativa futura en CONTEXT; prompt YAML documental | No runtime LLM integrado | Evaluación opcional, sin dependencia MVP | P2 |
| E | Gestión documental / RAG | A | Hay artefactos, no repositorio semántico autorizado | Archivos no equivalen a RAG | Diferir hasta caso demostrado | P2 |
| F | Portafolios VC | A | Registry administra casos, no participaciones/fondos | Sin cartera multiempresa con permisos | Extensión posterior | P2 |
| F | Real vs proyectado / desviaciones | A | Sin series de resultados efectivos | No seguimiento de presupuesto real | Primero importación CSV autorizada | P2 |
| F | Metas / indicadores | P | Growth commitment y métricas de modelo | No seguimiento temporal de ejecución real | Separar tesis de progreso observado | P2 |
| F | Valorizaciones periódicas | P | Rerun manual posible | Sin calendario ni reconciliación de versiones | Posterior a historial SaaS | P2 |
| F | Vistas por perfil | A | Páginas por módulo | No acceso por rol | T20/T24 para MVP; cartera después | P0/P2 |
| F | Contabilidad / SII | A | Sin conector ni importador contable | No asumir API universal | Estudio acotado y carga autorizada futura | P2 |

## Hallazgos que condicionan el producto

1. **H01 — validación insuficiente, P0.** `config.py:185–203` comprueba presencia y algunos límites, pero admite valores inválidos o no finitos en variables fundamentales. Una interfaz con mínimos no protege API/importaciones. Criterio de cierre: contrato de dominio y pruebas negativas en la frontera del motor.
2. **H02 — etapa fija y MILP no son equivalentes con canales mixtos, P0.** En `demo-mixed-channels`, H=14: CAC fijo año 1 = 126.727,5; CAC MILP = 113.237,5. EBITDA fijo = −98.162,8061; MILP = −84.672,8064. La etapa fija imputa comisiones sobre toda adquisición y costo terceros cero; el MILP distribuye canales. Diferencia material ≈13.490. No corregir sin decidir qué parte del plan consensuado incluye el mix.
3. **H03 — significado de financiación, P0.** Caja empieza en +VC y el suelo opcional es −VC: algebraicamente permite EBITDA acumulado hasta −2VC. No corresponde automáticamente a «agotar solamente el ticket». El modelo elástico minimiza suma de déficits, mientras informa máximo déficit: no demuestra financiamiento mínimo óptimo. Es una decisión metodológica que debe explicarse, ratificarse o revisarse.
4. **H04 — DCF y EV, P0.** El flujo usa EBITDA menos impuesto sin CapEx, depreciación, deuda ni Δcapital de trabajo. VAN descuenta VC; no debe rotularse automáticamente Enterprise Value o Equity Value. Terminal usa último mes×12; Gordon aproxima FCF con EBITDA. Pasar tests confirma fórmulas, no equivalencia con valoración financiera completa. Como contraste metodológico, FCFF resta inversión neta y cambios en capital de trabajo del resultado operativo después de impuestos; además exige tasa consistente con el tipo de flujo. [Damodaran, NYU, secciones Cash Flows y Discount Rates](https://pages.stern.nyu.edu/adamodar/New_Home_Page/invemgmt/assetsel.htm).
5. **H05 — coherencia M1/M4, P1.** El determinista maximiza EBITDA descontado; M4 combina esperanza y CVaR de VAN. M4 tiene reglas propias de financiación/terminal/comisiones. Conservar ambas capacidades, pero no afirmar equivalencia bajo escenario degenerado sin prueba específica. La evaluación ex post mantiene el plan; SAA optimiza uno compartido entre escenarios. Ninguno implica optimización robusta min-max ni decisiones multietapa adaptativas generales.
6. **H06 — publicación de informes no confiables, P0.** `select_autoescape(["html","xml"])` no reconoce extensión `.j2`; `inline_report_html` lee rutas relativas sin contención. Prueba local confirma ambos mecanismos. Antes de SaaS: autoescape correcto, sanitización, contención de rutas, objetos privados, aislamiento de renderer y política de acceso de red. No se comprobó una explotación remota.
7. **H07 — frontera de producto local, P0.** ADR0017 explícitamente justifica Streamlit para un consultor y prevé API al requerir concurrencia, auth o jobs. El nuevo alcance activa esos criterios. Esto justifica evolución; no invalida la decisión anterior.
8. **H08 — documentación y reproducibilidad, P1.** `PLAN.md` falta; API y modelo contienen secciones históricas de smoothing/terminal que no representan toda la evolución actual. `openpyxl` se usa sin declararse. CI no establece control de cobertura, pruebas de seguridad ni despliegue. Consolidar documentación vigente y probar entorno limpio.
9. **H09 — sensibilidad no es reoptimización, P1.** `sensitivity.py:80–114` ajusta totales ±10%; además inserta LTV/CAC junto con valores de EBITDA. Mezcla dimensión monetaria y razón en la misma estructura. El campo `method` toma el texto del documento sin cambiar ese algoritmo. Etiquetar y separar unidades antes de comparar.

## Reutilización frente a reconstrucción

| Alternativa | Esfuerzo incremental aproximado | Riesgo y calidad esperada | Decisión |
|---|---|---|---|
| Evolucionar núcleo y añadir producto | Plan: 2.193 h, incluida coordinación | Aprovecha 194 tests y separación existente; exige cerrar H01–H09 | **Recomendada** |
| Reescribir núcleo y producto | Añadir 350–650 h científicas/ingeniería y validación; orden 10–13 meses con igual equipo | Mayor riesgo de pérdida de reglas y nuevas discrepancias; mantenibilidad sólo mejora si hay causa concreta | No justificada hoy |
| Sustituir sólo piezas defectuosas | Dentro del plan mediante contratos y regresiones | Menor riesgo; puede extraerse cálculo común M1/M4 tras validar semántica | Preferida para correcciones futuras |

Los rangos son juicio de ingeniería, no cotización. A tarifa ilustrativa externa de 18–35 mil CLP/h, 350–650 h representan ≈6,3–22,8 millones adicionales si se externalizaran; la validación de Alonso seguiría siendo necesaria. No se encontró evidencia de una limitación estructural que obligue a desechar el motor completo.

La prioridad comercial es convertir el pipeline reutilizable en un servicio seguro, reproducible y comprensible. El siguiente documento traduce estos hallazgos en responsables, aceptación y fechas relativas.
