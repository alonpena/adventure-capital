# Speaker Script — Opening 3 Min

Buenos días. Mi tesis aborda un problema muy concreto en evaluación de startups: las decisiones financieras tempranas se toman con incertidumbre, información incompleta y muchos supuestos que suelen quedar dispersos entre Excel, notebooks y narrativa.

El objetivo de Adventure Capital fue convertir esa evaluación en un proceso reproducible. El sistema parte desde un YAML con supuestos del caso, genera una instancia financiera mensual, optimiza un plan de crecimiento acelerado con un modelo MILP, calcula valorización DCF y unit economics, aplica una capa de due diligence y finalmente genera artefactos auditables para reporte y UI.

La idea central no es reemplazar al consultor ni automatizar una decisión de inversión. La idea es hacer explícitos los supuestos, ordenar la evidencia y mostrar qué condiciones sostienen o debilitan una valorización.

En la presentación voy a mostrar tres cosas: primero, la arquitectura del pipeline; segundo, cómo el plan operacional se transforma en valor de empresa; y tercero, cómo la due diligence y el análisis de robustez evitan sobreinterpretar resultados que no cumplen criterios de escala o riesgo.

El alcance es deliberadamente acotado: es un MVP metodológico local, no un SaaS productivo. Pero deja contratos de entrada/salida, artefactos trazables y una base técnica para evolucionar hacia una plataforma.

