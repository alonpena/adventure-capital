# 12 Complete Technical Appendices

## A. Optimización

Variables: adquisición, clientes activos, recurrencia, servicios vendidos, ingresos, capacidad operacional, CAC, EBITDA, caja, vendedores/líderes. Fuente: `model.py`.

## B. Growth Target-Driven

`growth_commitment` agrega piso `C36 >= multiple*C12`; `acquisition_envelope` agrega cota superior `ΣA <= U_t`. Fuente: ADR 0014.

## C. Valorización

DCF usa EBITDA como proxy de flujo operativo, impuestos positivos, descuento mensual, valor terminal configurable. Fuente: `valuation.py`.

## D. Stochastic

LHS triangular, SAA, evaluación ex-post. Presentar como robustez, no plan oficial. Fuente: `stochastic/`, ADR 0015.

## E. UI

Streamlit gestiona instancias/ejecuciones y muestra artefactos. Fuente: `app.py`, `streamlit_pages/`.

## F. Limitaciones

No SaaS, no due diligence legal, no calibración de comparables de mercado, no gold final encontrado.

