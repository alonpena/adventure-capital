# Adventure Capital — Reporte de problemas y soporte

Proceso liviano de tickets para el piloto con Alejandro. Vive en un Google Doc
compartido (una tabla por sección); este archivo es la plantilla y la fuente de
verdad del proceso. Cuando un ticket se resuelve, la fila se mueve a "Resueltos"
con referencia al commit o instancia corregida.

## Cómo reportar (para Alejandro)

Copia este bloque al final de la sección "Abiertos" y completa:

```
ID:        AC-<número correlativo>
Fecha:     <dd-mm-aaaa>
Página:    <Gestor / Informe / Plan / Valoración / Due diligence / Robustez / Artefactos>
Caso:      <nombre de la instancia o run_id, p. ej. run_20260710-125137_30f45c5d>
Qué hice:  <pasos, 1-2-3, incluye el YAML si cargaste uno>
Qué esperaba:
Qué pasó:  <mensaje de error textual si hay; pantallazo si puedes>
Impacto:   Bloqueante / Molesto / Cosmético
```

Reglas de oro:
- **Un ticket = un problema.** Dos problemas, dos filas.
- **El run_id importa.** Aparece en la cabecera de cada página (`run_...`);
  con él se reproduce todo, porque la configuración queda congelada en disco.
- Si el veredicto dice "Plan infactible", eso **no es un bug**: es el modelo
  diciendo que esa configuración no soporta la tesis. El ticket va igual, pero
  con impacto "Molesto" — la respuesta será qué palanca ajustar.

## Triage (para Alonso)

| Impacto | SLA piloto | Acción |
|---|---|---|
| Bloqueante (no puede seguir trabajando) | mismo día | fix o workaround inmediato |
| Molesto (puede seguir, con fricción) | 48 h | agrupar y priorizar |
| Cosmético | backlog | lote semanal |

Cada ticket resuelto cierra con: causa raíz (1 línea), fix (commit o cambio de
configuración) y verificación (test o run que lo demuestra).

## Secciones del Doc

1. **Abiertos** — tabla con los bloques de arriba.
2. **En curso** — máximo 3 a la vez.
3. **Resueltos** — con commit/run de verificación.
4. **Decisiones** — cambios de comportamiento acordados (equivale a mini-ADRs;
   los importantes se copian a `docs/adr/`).
