# 0017 — Producto v0.0.1: Streamlit como superficie de entrega; extracción de API diferida con criterios explícitos

## Status
Accepted
Date: 2026-07-12

## Context

La tesis fue entregada (tag `thesis-final`). El repo pasa a ser producto
(v0.0.1, piloto con un cliente consultor). Se cuestionó si migrar a
React + API de microservicios era fundamental para continuar el desarrollo.

Evaluación técnica: no lo es. El valor vendible es el pipeline M1–M5
(`workflow_registry`: config YAML congelada → artefactos JSON/CSV → informe).
Ese pipeline ya es "config in → artifacts out", sin estado compartido con la
UI (ADR 0007: la UI solo lee artefactos). Streamlit cubre el caso de uso
actual: un consultor, una máquina, casos secuenciales.

## Decision

1. **Streamlit sigue siendo la superficie de entrega** del producto v0.0.1.
   Prioridad del desarrollo: usabilidad, correctitud y valor para el piloto —
   no re-plataformar. (Ratifica ADR 0008.)
2. **La extracción de una API es un TODO documentado, no trabajo actual.**
   Primer paso cuando toque: FastAPI delgada sobre `workflow_registry`
   (crear instancia / ejecutar / listar artefactos), sin tocar la UI.
   React u otro frontend solo después de eso.

## Criterios que disparan la extracción de API (cualquiera de estos)

- Más de un usuario concurrente (multi-tenant o dos consultores en paralelo).
- Necesidad de autenticación/autorización por cliente.
- Ejecuciones que deban correr fuera de la sesión del navegador (colas, jobs
  largos, notificaciones).
- Un segundo frontend (React, integración con herramienta del cliente).

Mientras ninguno ocurra, invertir en API es costo sin valor.

## Consequences

- El deploy sigue siendo una app Streamlit (Streamlit Cloud / VM única).
- La disciplina que protege el futuro: **nada de lógica de negocio en
  `streamlit_pages/`** — todo cálculo vive en `src/adventure_capital/` y se
  comunica por artefactos (ADR 0007). Esa frontera es la API futura.
