# 13 AI Tools And Agent Coordination

## Tabla De Herramientas

| Herramienta/agente | Rol | Etapa | Validación humana | Evidencia |
|---|---|---|---|---|
| Python | implementación cálculos/modelo | core | tests/revisión | `src/` |
| PuLP/CBC | solver MILP | optimización | tests/smoke | `model.py` |
| Streamlit | UI local | demo | revisión visual | `app.py` |
| YAML | inputs/config | metodología | revisión experto | `configs/` |
| Git | versionado | todo | commits/branches | `git log` |
| Codex/Claude/otros agentes | apoyo código/docs/debug | desarrollo | usuario/revisor valida | reportado por contexto; requiere confirmación |
| ChatGPT/Gemini/NotebookLM | apoyo síntesis/investigación | tesis/docs | requiere confirmación usuario | reportado por usuario si aplica |

## Wording Académico Seguro

“El estudiante definió problema, alcance, lógica de negocio, decisiones metodológicas y validación final. Las herramientas de IA apoyaron generación de código, depuración, documentación y síntesis; no sustituyeron el juicio metodológico.”

## Unsafe

No decir “la IA hizo la tesis”. No atribuir decisiones metodológicas a agentes sin evidencia humana.

