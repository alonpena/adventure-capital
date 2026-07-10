# Speaker Script — Demo 2 Min

Para la demo, partiría desde una ejecución concreta: `{{GOLD_RUN_PATH}}`.

Primero muestro el `config.yaml`, porque ahí están los supuestos: servicios, ticket, recurrencia, churn, costos, inversión y tesis de crecimiento. Después abro `optimized_results.csv`, que es el plan mensual canónico generado por el solver. Ahí se ve adquisición, clientes activos, ingresos, CAC, EBITDA y caja.

Luego abro `valuation_summary.json` y `dcf_cashflow.csv` para mostrar cómo el plan se traduce en VAN. Si uso el reporte, abro `report.html` y explico que no es una pantalla calculando de nuevo, sino una vista generada desde artefactos.

Después muestro `due_diligence_report.md`: este archivo es importante porque dice si el caso permite análisis estocástico, si requiere ajustes, y qué supuestos hay que recalibrar.

Si hay M4 disponible, muestro `stochastic_summary.csv` solo como robustez: percentiles de VAN, probabilidad de VAN negativo y funding gap. Remarco que el plan oficial del MVP sigue siendo determinista target-driven.

