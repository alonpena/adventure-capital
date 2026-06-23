Escuela de Ingeniería Industrial

Entregable 3: Informe Final Corregido

**Diseño de una metodología estandarizada para la aceleración y valorización de startups**

por

**Alonso Peña Domarchi**

EII 6160 - Proyecto de Ingeniería Industrial 2

Profesor Guía: Ignacio Beláustegui

Profesor Evaluador: Bruno Lavín

Mandante: Alejandro Maureira

Junio, 2026

---

# Glosario

**Aceleración:** Proceso mediante el cual una startup planifica y ejecuta crecimiento rápido basado en adquisición, retención y monetización de clientes.

**Adquisición de clientes:** Captura de nuevos clientes en un período mensual de planificación. En el modelo, toda adquisición genera una venta nueva del mismo servicio y período.

**Artefacto canónico:** Archivo CSV o JSON generado por el pipeline que constituye fuente de verdad auditable para resultados, métricas y reportes.

**CAC:** Costo de adquisición de clientes. En el sistema se descompone por canal comercial: fuerza de ventas, publicidad y comisión de terceros.

**Churn:** Tasa de pérdida de clientes. El modelo usa churn específico por servicio y año; en M4 se aplica además un multiplicador estocástico general por escenario.

**Cohorte de servicio:** Clientes adquiridos para un servicio específico en un período de planificación. Su supervivencia y recurrencia se calculan durante el horizonte mensual.

**CVaR:** Conditional Value at Risk. En M4 se usa como objetivo conservador: maximiza el VAN esperado en el peor 5% de escenarios.

**Due Diligence:** Flujo de evaluación, recomendación y recalibración que envuelve el modelo determinista, emite un veredicto y determina si el caso puede continuar a M4.

**Flujo de Caja Descontado (DCF):** Método de valorización que descuenta los flujos futuros a una tasa ajustada por riesgo.

**Hipercubo Latino (LHS):** Técnica de muestreo estratificado usada en M4 para generar escenarios SAA y evaluación ex-post con menor varianza que un muestreo aleatorio simple.

**LTV:** Valor esperado de un cliente durante su relación con la empresa.

**M4 estocástico canónico:** Modelo SAA de dos etapas con paridad respecto del determinista, tres canales comerciales, adquisición realizada variable por escenario y objetivo CVaR_5%(VAN).

**Plan de Crecimiento Acelerado (PCA):** Plan operativo y comercial optimizado que proyecta adquisición, ingresos, costos, EBITDA y caja para acelerar la startup.

**Recta publicitaria:** Relación lineal continua entre inversión publicitaria y adquisición planificada: `A_ad = a + b·I_ad`.

**Third-Party Commission Window:** Número limitado de períodos durante los cuales el canal de terceros cobra comisión sobre ingresos atribuibles a cohortes originadas por ese canal.

**Unit Economics:** Métricas unitarias del negocio: CAC, LTV, ARPU, ARR, margen bruto, churn y LTV/CAC.

---

# Lista de Abreviaturas

**AC:** Adventure Capital  
**ADR:** Architecture Decision Record  
**ARPU:** Average Revenue Per User  
**ARR:** Annual Recurring Revenue  
**CAC:** Customer Acquisition Cost  
**CBC:** COIN-OR Branch and Cut  
**CVaR:** Conditional Value at Risk  
**DCF:** Discounted Cash Flow  
**DD:** Due Diligence  
**EBITDA:** Earnings Before Interest, Taxes, Depreciation and Amortization  
**LHS:** Latin Hypercube Sampling  
**LTV:** Lifetime Value  
**MILP:** Mixed-Integer Linear Programming  
**PCA:** Plan de Crecimiento Acelerado  
**SAA:** Sample Average Approximation  
**VAN:** Valor Actual Neto  
**VC:** Capital de trabajo inicial / ticket de financiamiento

---

# I. Resumen Ejecutivo

El proyecto diseña e implementa un sistema integrado para que Adventure Capital estandarice y automatice la planificación del crecimiento acelerado, la valorización financiera y la generación de reportes para startups. El diagnóstico inicial mostró una operación artesanal, dependiente del criterio y tiempo del mandante, con alta variabilidad por caso y un cuello de botella operativo que limita la capacidad mensual de atención.

La solución transforma una metodología basada en planillas y notebooks en una canalización modular en Python. El flujo actual considera: normalización de una instancia YAML, modelo determinista de optimización MILP para el Plan de Crecimiento Acelerado, valorización DCF y Unit Economics, Due Diligence cuantitativa, optimización estocástica canónica M4 mediante SAA con LHS y objetivo CVaR_5%(VAN), y generación de un reporte HTML simple en español. Además, se incorporó una CLI orientada a instancias y ejecuciones, lo que permite operar el sistema sin depender todavía de una interfaz gráfica completa.

El caso base auditado resuelve el modelo determinista con estado óptimo, adquisición total de 1.621 clientes, ingresos acumulados por USD 3,00 millones, EBITDA acumulado por USD 1,69 millones, caja final de USD 1,79 millones y VAN determinista de USD 530 mil. La Due Diligence clasifica el caso como `requires_minor_adjustment`, principalmente por presión de caja temprana, pero permite continuar a M4 en modo `warning`. El M4 canónico ejecuta 100 escenarios SAA y 1.000 escenarios de evaluación ex-post LHS, obteniendo VAN esperado de USD 1,54 millones, CVaR 5% de USD 834 mil, probabilidad nula de VAN negativo y 1.359 clientes activos finales en mediana. El resultado muestra creación de valor bajo incertidumbre, pero con probabilidad elevada de presión de liquidez, por lo que el reporte recomienda ajustar capital de trabajo o suavizar adquisición.

El sistema queda funcional para ejecución local reproducible mediante CLI, con artefactos trazables y un reporte HTML simple. Quedan como trabajo futuro la mejora estética del reporte, la consolidación de la UI, la validación con casos reales del mandante, la calibración de múltiplos de mercado y la optimización de performance del M4 para configuraciones mixtas de canales.

*Palabras clave:* valorización de startups, optimización entera mixta, programación estocástica, CVaR, unit economics, due diligence.

---

# II. Definición del Problema, Contexto y Metodología

## 2.1 Problema y oportunidad

Adventure Capital es una consultora financiera especializada en startups. Su propuesta de valor combina diagnóstico del modelo de negocio, planificación del crecimiento acelerado y valorización defendible ante inversionistas. Antes del proyecto, gran parte del proceso dependía de trabajo manual del mandante, con tiempos variables y difícil trazabilidad de supuestos, fórmulas y resultados.

El problema central es la escalabilidad operativa. Cuando la preparación de modelos, reportes y diagnósticos se realiza artesanalmente, cada caso requiere rearmar archivos, fórmulas y narrativas. Esto incrementa el tiempo por startup, dificulta comparar resultados y limita el número de clientes atendidos.

## 2.2 Objetivo general

Diseñar e implementar una metodología computacional estandarizada para acelerar y valorizar startups, reduciendo dependencia manual, aumentando trazabilidad y generando artefactos auditables para análisis financiero, Due Diligence e informes.

## 2.3 Objetivos específicos

1. Formalizar el flujo financiero y comercial del Plan de Crecimiento Acelerado.
2. Implementar un modelo determinista de optimización mensual.
3. Calcular valorización DCF, múltiplos de referencia y Unit Economics.
4. Implementar una capa de Due Diligence cuantitativa.
5. Incorporar una optimización estocástica canónica con LHS, paridad de canales y CVaR.
6. Generar un reporte HTML simple desde artefactos canónicos.
7. Proveer una CLI para operar instancias, ejecuciones, M4 y reportes.

## 2.4 Alcance

Incluye motor de optimización, valorización, Unit Economics, Due Diligence, M4 estocástico, artefactos CSV/JSON, CLI local y reporte HTML simple. No incluye todavía SaaS multiusuario, autenticación, base de datos persistente, UI productiva completa, calibración automática de comparables de mercado ni validación empírica con una cartera amplia de casos reales.

## 2.5 Marco teórico

**Lean Startup y Unit Economics.** En startups, la unidad mínima de análisis financiero suele ser el cliente: cuánto cuesta adquirirlo, cuánto compra, cuánto permanece y qué margen deja. Por eso CAC, LTV, churn, ARPU y recurrencia son indicadores centrales para evaluar escalabilidad.

**Valorización por DCF.** El DCF estima valor presente de flujos futuros ajustados por riesgo. En etapas tempranas, la incertidumbre de adquisición, retención y tasa de descuento exige complementar la lectura determinista con sensibilidad y escenarios.

**Optimización estocástica.** SAA aproxima un problema bajo incertidumbre mediante una muestra de escenarios. En este proyecto, M4 usa LHS para construir escenarios y CVaR para privilegiar planes que mantienen valor en la cola adversa, no solo en el promedio.

**Trazabilidad de artefactos.** Para que la metodología sea auditable, los resultados se materializan en CSV/JSON. El reporte y la CLI leen estos artefactos; no recomputan la lógica financiera.

---

# III. Diseño de la Solución y Resultados

## 3.1 Arquitectura general

El flujo actual es:

```text
startup.yaml
  → instancia normalizada
  → M1 modelo determinista PCA
  → M2 valorización DCF + Unit Economics
  → M3 Due Diligence
  → M4 estocástico si DD lo permite
  → M5 reporte HTML simple
  → CLI de instancias y ejecuciones
```

El modelo determinista sigue siendo la base operacional. La Due Diligence decide si el caso puede pasar a M4. El reporte final se genera a partir de artefactos canónicos, no desde cálculos duplicados.

## 3.2 M1 — Modelo determinista del PCA

El M1 es un MILP mensual implementado con PuLP/CBC. Optimiza la adquisición y recursos comerciales desde el mes 13 en adelante, manteniendo los primeros 12 meses como período consensuado de adquisición fija (`A_base`).

El modelo considera múltiples servicios, cohortes de clientes, ventas nuevas, ventas recurrentes, ingresos, costos operacionales con piso de capacidad, CAC, gastos administrativos, RRHH, EBITDA y caja. El costo operacional usa semántica de máximo entre costo variable y piso de capacidad, no suma fija más variable.

El refinamiento determinista incorporó:

1. techo logarítmico opcional de adquisición;
2. separación de canales comerciales;
3. recta publicitaria continua;
4. trazabilidad de CAC por componente;
5. piso de caja de capital de trabajo y diagnóstico de brecha;
6. Unit Economics anualizados y consistentes.

Los canales comerciales son:

- fuerza de ventas: vendedores `V` y líderes `L`;
- publicidad: inversión `I_ad` y recta `A_ad = a + b·I_ad`;
- terceros: adquisición vía comisión sobre ingresos atribuibles al canal.

## 3.3 M2 — Valorización y Unit Economics

M2 toma los resultados del PCA y calcula flujos de caja descontados. El DCF resta impuestos solo cuando el EBITDA es positivo, descuenta con tasa mensual derivada de la tasa anual e incorpora el capital inicial VC. También calcula múltiplos de ingresos y EBITDA como referencia metodológica, no como comparables de mercado calibrados.

Los Unit Economics incluyen adquisición, CAC, ticket promedio, recurrencia, ARR, gross profit, ARPU, burn rate, bootstrapping, LTV, LTV(2), LTV/CAC y clientes monetizados. Cada métrica se conserva en `unit_economics.csv` y se referencia desde `valuation_summary.json`.

## 3.4 M3 — Due Diligence

La Due Diligence envuelve al modelo determinista y clasifica el caso. Sus veredictos son:

| Veredicto | M4 | Modo |
|---|---:|---|
| `passed` | sí, automático | final |
| `passed_with_warnings` | sí, con confirmación CLI | final |
| `requires_minor_adjustment` | sí, con confirmación CLI | warning |
| `requires_major_adjustment` | no | none |
| `rejected_for_stochastic` | no | none |

La DD combina pre-reglas de instancia, reglas de síntesis sobre resultados deterministas y calibración técnica. Reglas estructurales bloquean el flujo; fallas mayores requieren recalibrar YAML antes de M4; fallas menores permiten M4 en modo advertencia.

## 3.5 M4 — Optimización estocástica canónica

M4 fue redefinido como un componente metodológico central, no como diagnóstico simplificado. El problema resuelve un SAA de dos etapas con paridad respecto del determinista y objetivo conservador CVaR_5%(VAN).

Las decisiones de primera etapa, comunes a todos los escenarios, son:

```text
V[t], L[t], I_ad[t],
A_sf_plan[s,t], A_ad_plan[s,t], A_tp_plan[s,t]
```

Desde el mes 13, la adquisición realizada por escenario depende de la eficiencia aleatoria de cada canal:

```text
A_sf[s,t,w] = salesforce_eff[w] * A_sf_plan[s,t]
A_ad[s,t,w] = advertising_eff[w] * A_ad_plan[s,t]
A_tp[s,t,w] = third_party_eff[w] * A_tp_plan[s,t]
```

Por ello, los clientes activos también son variables por escenario:

```text
C[s,t,w] = Σ_c phi[s,c,t,w] * A[s,c,w]
```

El M4 usa LHS para 100 escenarios SAA y LHS ex-post para 1.000 escenarios de evaluación. El objetivo es:

```text
max CVaR_5%(VAN) + ε·E[VAN]
```

El VAN del MILP usa impuesto lineal, VC fijo y valor terminal lineal. No se incorporan no linealidades, `max(EBITDA,0)` ni recourse comercial. La evaluación ex-post fija la estrategia óptima y calcula distribución de VAN, clientes activos finales, breakeven, runway, funding gap y Unit Economics.

## 3.6 M5 — Reporte HTML simple

Dado que el reporte estándar previo fue desarrollado antes de los cambios de canales y M4, se implementó un M5 simple y directo. El nuevo `report.html` lee artefactos planos canónicos y presenta, en español, portada, KPIs, M1, M2, M3, M4 y listado de artefactos. Si M4 está pendiente, bloqueado o falló, el reporte incluye la sección con el estado correspondiente.

El objetivo de esta versión no es estética final, sino entregar un documento funcional y trazable. La generación PDF y el reporte estándar pulido quedan como evolución posterior.

## 3.7 CLI de instancias y ejecuciones

Se implementó una CLI local basada en filesystem registry, sin SQLite por ahora. La estructura es:

```text
outputs/instances/<instance_id>/instance.yaml
outputs/instances/<instance_id>/metadata.json
outputs/executions/<run_id>/execution.json
outputs/executions/<run_id>/...artefactos...
```

Comandos principales:

```bash
adventure-capital instances create --config configs/base.yaml --name "Caso base"
adventure-capital instances list
adventure-capital instances show <instance_id>

adventure-capital executions run --instance <instance_id>
adventure-capital executions list
adventure-capital executions status <run_id>
adventure-capital executions stochastic <run_id> --stochastic-time-limit 420
adventure-capital executions report <run_id>
```

La CLI ejecuta M1-M3, aplica el gate de DD y, según el veredicto, ejecuta M4 automáticamente o solicita confirmación. El reporte se genera automáticamente al finalizar una ejecución o al re-ejecutar M4.

## 3.8 Resultados del caso base auditado

La ejecución auditada corresponde al caso base con horizonte de 36 meses, VC de USD 100.000 y canal activo de fuerza de ventas. El modelo determinista resuelve óptimamente.

**Tabla 1 — Resultados deterministas M1.**

| Indicador | Resultado |
|---|---:|
| Estado solver | Optimal |
| Adquisición total | 1.621 clientes |
| Ingresos acumulados | USD 3,00 MM |
| EBITDA acumulado | USD 1,69 MM |
| Caja final | USD 1,79 MM |
| Caja mínima | USD -18.098 |
| Vendedores máximos | 23 |
| Líderes máximos | 8 |

**Tabla 2 — Valorización y Unit Economics.**

| Indicador | Resultado |
|---|---:|
| VAN determinista DCF | USD 530.110 |
| VP de flujos | USD 630.110 |
| VC invertido | USD 100.000 |
| Valor por múltiplo de ingresos | USD 3,60 MM |
| Valor por múltiplo de EBITDA | USD 4,85 MM |
| CAC | USD 359/cliente |
| ARPU | USD 250/cliente |
| LTV | USD 5.360/cliente |
| LTV/CAC | 14,93× |

**Tabla 3 — Due Diligence.**

| Campo | Resultado |
|---|---|
| Veredicto | `requires_minor_adjustment` |
| Permite M4 | Sí |
| Modo de valorización | `warning` |
| Calibración | `FAIL` |
| Recomendación principal | Aumentar VC, diferir contrataciones o suavizar adquisición |

La clasificación no bloquea M4, pero exige leer la valorización estocástica como advertencia por presión de caja temprana.

**Tabla 4 — Resultados M4 estocástico.**

| Indicador | Resultado |
|---|---:|
| Escenarios SAA | 100 |
| Escenarios ex-post LHS | 1.000 |
| VAN esperado | USD 1,54 MM |
| VAN P5 | USD 943 mil |
| VAN P10 | USD 1,06 MM |
| VAN P50 | USD 1,54 MM |
| VAN P90 | USD 2,03 MM |
| CVaR 5% | USD 834 mil |
| Probabilidad VAN negativo | 0,0% |
| Clientes activos finales P50 | 1.359 |
| Probabilidad de alcanzar 1.000 clientes activos finales | 96,7% |
| Probabilidad de alcanzar 2.000 clientes activos finales | 0,0% |
| Breakeven mediano | Mes 23 |
| Runway mediano | Mes 10 |
| Probabilidad caja bajo piso | 100,0% |
| Funding gap esperado | USD 20.766 |
| Funding gap máximo | USD 41.203 |
| CAC P50 | USD 372/cliente |
| LTV/CAC P50 | 13,86× |

La lectura conjunta indica que el plan crea valor incluso en cola adversa, pero no es robusto en liquidez: todos los escenarios evaluados cruzan el piso de caja definido. El sistema, por tanto, no solo entrega una valorización, sino también una recomendación operativa: ajustar capital de trabajo o suavizar la aceleración.

## 3.9 Estado de implementación

| Componente | Estado | Evidencia |
|---|---|---|
| M1 determinista MILP | Implementado | `model.py`, `results.py` |
| Canales comerciales | Implementado | fuerza de ventas, publicidad, terceros |
| M2 DCF + Unit Economics | Implementado | `valuation.py`, `unit_economics.py` |
| M3 Due Diligence | Implementado | `due_diligence/` |
| M4 SAA + LHS + CVaR | Implementado | `stochastic/`, tag `m4-stochastic-parity` |
| Evaluación ex-post LHS | Implementado | `stochastic/evaluate.py`, `stochastic_summary.csv` |
| CLI instancias/ejecuciones | Implementado MVP | `workflow_registry.py`, `cli.py` |
| M5 HTML simple | Implementado MVP | `simple_report.py`, `report.html` |
| Streamlit UI | MVP previo / postergado | `app.py`, `streamlit_pages/` |
| Reporte estándar pulido/PDF | Parcial/legacy | `standard_report/` |
| Validación con casos reales | Pendiente | fuera de esta ejecución |

La suite automatizada reporta 137 pruebas pasando y 3 omitidas por dependencias de WeasyPrint. El linter está limpio en archivos modificados recientes; el baseline completo conserva advertencias preexistentes en módulos no tocados.

## 3.10 Limitaciones

1. El reporte HTML simple cumple función de entrega trazable, pero no reemplaza una versión visual final de consultoría.
2. La ejecución M4 mixta puede tardar varios minutos; se agregó `--stochastic-time-limit` y un default operacional de 420 segundos.
3. La UI Streamlit existe como MVP de exploración, pero se postergó en favor de CLI + M4 + M5 funcionales.
4. Los múltiplos siguen siendo referencias configurables, no comparables de mercado calibrados.
5. No hay validación empírica amplia con casos reales del mandante.
6. El registry actual usa filesystem, no SQLite ni base multiusuario.

---

# IV. Conclusiones

El proyecto logra convertir una metodología manual de valorización y aceleración en un flujo computacional modular, reproducible y auditable. El sistema no solo calcula un plan determinista, sino que encadena valorización, Unit Economics, Due Diligence, optimización estocástica aversa al riesgo y reporte automático.

La contribución central es metodológica: el M4 canónico evita evaluar incertidumbre sobre un modelo simplificado. En su lugar, replica la estructura comercial del determinista, incorpora tres canales, permite que la adquisición realizada y los clientes activos varíen por escenario, y optimiza un objetivo conservador CVaR_5%(VAN). Esto permite analizar no solo el valor esperado, sino también el desempeño en escenarios adversos.

La incorporación de una CLI de instancias y ejecuciones permite operar el sistema sin esperar una UI completa. Esta decisión fue relevante para cerrar el flujo de punta a punta: crear instancia, ejecutar M1-M3, aplicar gate de Due Diligence, correr M4 cuando corresponde y generar un reporte HTML simple.

Los resultados del caso base muestran valorización positiva y baja probabilidad de VAN negativo, pero también presión de liquidez. Esta doble lectura evidencia el valor del sistema: no se limita a producir un número de valorización, sino que identifica restricciones operativas y recomendaciones de recalibración.

Como trabajo futuro se propone validar con casos reales del mandante, mejorar el reporte visual y PDF, consolidar la UI, optimizar performance del M4, calibrar múltiplos de mercado y evaluar la migración del registry a SQLite o una base de datos cuando el flujo requiera multiusuario.

---

# Bibliografía

Blank, S. (2013). *Why the lean start-up changes everything*. Harvard Business Review, 91(5), 63–72.

Bortolini, R. F., Nogueira Cortimiglia, M., Danilevicz, A. de M. F., & Ghezzi, A. (2018). Lean Startup: A comprehensive review. *IEEE Transactions on Engineering Management*, 65(3), 424–440.

Köhn, A. (2018). The determinants of startup valuation in the venture capital context. *Venture Capital*, 20(2), 113–136.

Montani, D., Frigerio, M., & Marchesi, A. (2020). Startup company valuation: The state of art and future trends. *Journal of Innovation and Entrepreneurship*, 9(1), 1–23.

Project Management Institute. (2021). *A guide to the project management body of knowledge (PMBOK® guide) – Seventh edition*. Project Management Institute.

Ries, E. (2011). *The lean startup: How today's entrepreneurs use continuous innovation to create radically successful businesses*. Crown Business.

Asociación Chilena de Venture Capital (ACVC). (2025). *Impact report ACVC 2025*.
