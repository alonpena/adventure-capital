# Trabajo futuro — registro de extensiones diferidas

Decisiones explícitas de NO hacer ahora, con su razón. Cada ítem entra al
producto solo cuando su criterio de disparo ocurra.

| Extensión | Estado hoy | Por qué diferido | Disparo |
|---|---|---|---|
| **Capital de trabajo / política de liquidez** | `liquidity_policy` existe en config (none/nonnegative/minimum_cash) y `working_capital` como piso −VC, pero sin modelamiento fino (ciclos de cobro/pago por servicio). Retirado del formulario 2026-07-13 | Requiere trabajo de modelamiento serio, no un widget | Cliente con tensión de caja real donde el veredicto dependa del working capital |
| **Full stochastic optimization** (M4 define el plan) | M4 = diagnóstico de robustez (ADR 0015); término canónico "Análisis de robustez" | No mezclar con el entregable oficial; el plan oficial es determinista target-driven | Demanda explícita de un cliente + revisión académica |
| **Extracción de API / React** | ADR 0017: Streamlit es la superficie de entrega | Cero valor hoy; frontera ya protegida (UI no calcula) | Multi-tenant, auth, jobs largos o segundo frontend |
| **Sensibilidad tipo tornado configurable** | Sensibilidad hardcoded ±10% visible en Valoración | Suficiente como métrica de referencia | Consultor pide magnitudes de shock por palanca |
| **`g_max_suavizado`** | Parámetro muerto: ningún constraint del modelo lo lee (freno legacy pre-target-seeker). Retirado del formulario; se acepta en YAML por compatibilidad | Eliminarlo del config/schema requiere migración de YAMLs históricos | Próxima limpieza de schema de config (romper compatibilidad deliberadamente) |
