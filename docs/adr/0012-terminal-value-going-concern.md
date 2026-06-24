# 0012 — Default terminal value: 1x last-year EBITDA (going concern)

Status: Accepted
Date: 2026-06-23
Relates to: deterministic DCF (`valuation.py`), stochastic terminal (`stochastic/model.py`).

## Context

Deterministic DCF ran with `valor_residual_metodo = "none"` by default, so the Enterprise
Value excluded any terminal/residual value. The benchmark instance YAMLs
(`instances_yaml_v1/*`) do not set the method, so every CLI run produced a VAN with no
terminal component — while the manual founder spreadsheets all include a "valor de
desecho" (terminal). This made the model's VAN look implausibly low: e.g. entrena
$275k vs manual $1.41M, kavacomex $129k vs manual $3.78M (the gap is dominated by the
missing terminal, which for a recurring-revenue business carries most of the EV).

The terminal value is the right place to close the gap, but **arbitrary high multiples
are not acceptable** — a large EV/EBITDA multiple would let the firm be worth far more
"in parts" than as a going concern, which is economically backwards for an early-stage
company. The mandante's rule: terminal value = **1x the last-year EBITDA**.

## Decision

Default terminal value = **1x annualized last-year EBITDA**, i.e.
`valor_residual_metodo = "ebitda_multiple"` with `ebitda_multiple = 1.0`.

- `valuation.py`: the method fallback changes `"none" -> "ebitda_multiple"`; the multiple
  fallback is already `1.0` (`mult_vd_ebitda`). Applies to loaded YAMLs that omit the
  block (config defaults are not merged on load, so the fallback lives in `valuation.py`).
- `config.py` default config carries `valor_residual_metodo: "ebitda_multiple"`,
  `ebitda_multiple: 1.0` for the `default_config()` path.
- The stochastic model already uses `terminal_multiple = 1.0` on annualized last-year
  EBITDA, so deterministic and stochastic terminals are now consistent at 1x.

Effect (deterministic VAN): base -121k -> -76k, entrena 275k -> 554k,
kavacomex 129k -> 362k, beloop 9.7M -> 14.9M (now matching the manual multiples value).

## Consequences

- VAN is no longer systematically understated; it includes a conservative going-concern
  terminal that cannot exceed the operating value by construction (1x).
- A negative VAN now signals a genuinely unprofitable plan (e.g. the underfunded `base`
  demo: VC < year-1 fixed cost), not a missing terminal.
- Per-instance overrides remain available (`valor_residual_metodo`, `ebitda_multiple`,
  or `gordon`) with documented justification. Arbitrary multiples are discouraged.

## Rejected / deferred

- **High EV/EBITDA multiples (e.g. x5-x10).** Bring VAN above the manual but are arbitrary
  and let "parts > whole." Not the default.
- **LTV/CAC-based terminal.** A possible alternative anchored to unit economics; only
  worth adopting if shown to be reasonable (not an arbitrary scalar). Deferred.
