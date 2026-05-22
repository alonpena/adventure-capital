# Due Diligence Module

An **iterative assess → recommend → rerun** workflow that wraps the deterministic baseline, evaluates whether the case resembles a scalable venture-scale business, and recommends which assumptions to recalibrate. Due Diligence (DD) owns the verdict and report; **Calibration** is reused as a technical evidence source, not a separate phase. DD is not a hard fail/stop gate — only structural infeasibility blocks the **Stochastic Model**. See ADR [0005](adr/0005-due-diligence-umbrella.md) and the CONTEXT.md glossary (Due Diligence, Due Diligence Verdict, Valuation Mode, Calibration).

## Flow

```
raw instance/config
  -> DD pre-rules            (raw instance)
  -> run_pipeline()          (deterministic baseline: optimized results, DCF, multiples, unit economics)
  -> run_calibration()       (post-model technical checks, reused as evidence)
  -> DD eligibility/synthesis rules + liquidity diagnostic
  -> aggregate findings      (DD rules + mapped calibration findings)
  -> Due Diligence Verdict (+ decision fields) + report (always)
  -> if rejected_for_stochastic (structural): stochastic blocked; rejection report
  -> otherwise: stochastic robust valuation runs, tagged by valuation_mode
  -> consultant recalibrates per recommendations and re-runs (iterative)
```

`run_assessment` chains the whole preliminary flow (DD → stochastic if allowed → `assessment_summary.json`). `run_due_diligence` runs the assessment only. DD reuses `run_pipeline` (no duplicated model/valuation logic) and `run_calibration` (no reimplemented financial checks). It does not modify `pipeline.py` or `model.py`, and is not wired into the deterministic CLI yet.

## Verdicts, severity, and decision fields

Worst failing finding wins (precedence top to bottom):

| Severity class | Verdict | `allows_stochastic` | `valuation_mode` | `adjustment_level` |
|---|---|---|---|---|
| `structural` | `rejected_for_stochastic` | false | `none` | `structural` |
| `major` | `requires_major_adjustment` | true | `diagnostic` | `major` |
| `minor` | `requires_minor_adjustment` | true | `warning` | `minor` |
| `warning` | `passed_with_warnings` | true | `final` | `none` |
| (none) | `passed` | true | `final` | `none` |

- **`structural`** — instance cannot be meaningfully modeled (only this blocks).
- **`major`** — not yet venture-scale eligible (insufficient growth, no credible EBITDA regime by year 3, scaling-incompatible retention). Stochastic runs **diagnostically** (not investment-ready).
- **`minor`** — fixable business/liquidity risk (negative cash, funding gap, low runway). Stochastic runs as **preliminary/warning**.

The verdict also carries `blocking_reasons`, `adjustment_recommendations` (what to recalibrate), and `rerun_recommended`. A report is **always** produced — explaining what failed, why it matters, which parameters to recalibrate, and what would make the instance acceptable. Liquidity (negative cash / funding gap) is reported as a diagnostic, never a structural block.

## Rule registry

### DD pre-rules (raw instance — new logic)

| Rule | Class | Condition (fail) |
|---|---|---|
| `DD01_instance_valid` | structural | config fails `validate_config` |
| `DD02_unit_margin_positive` | structural | any service `ticket <= c_u` (non-computable unit economics) |
| `DD03_financing_present` | structural | `VC <= 0` (missing essential input) |
| `DD04_churn_valid` | structural | any `churn_anual` outside `[0, 1]` |
| `DD05_churn_severity` | major / warning | max annual churn above `churn_major` / `churn_warn` |

### DD eligibility + synthesis rules (deterministic outputs — new)

| Rule | Class | Condition (fail) |
|---|---|---|
| `DD06_breakeven_within_horizon` | major / warning | cumulative EBITDA never ≥ 0 (major) or breaks even after `breakeven_warn_month` (warning) |
| `DD09_ebitda_regime_by_year3` | major | annual EBITDA not positive by `ebitda_regime_year` |
| `DD10_revenue_growth` | major | final-year / first-year revenue below `revenue_growth_min_multiple` (SME-like, not scalable) |
| `DD07_runway` | minor / warning | cash goes negative on/before `runway_minor` (minor) else warning — diagnostic |
| `DD08_funding_gap_severity` | minor / warning | working-capital trough vs `VC` above `gap_minor` / `gap_warn` — diagnostic |

Liquidity is also summarized (not pass/fail) in `liquidity_diagnostic`: min cash + month, max funding gap + month, breakeven month, whether cash recovers, final cash.

### Delegated to Calibration (mapped, not reimplemented)

NPV (`C06`), LTV/CAC (`C08`), gross margin (`C07`), cash floor (`C04`), total EBITDA (`C05`), retention (`C10`), mix concentration (`C09`), document completeness (`C11`), solver status (`C01`). Mapping:

- id in `blocking_ids` (default `C01`) → `structural`
- id in `major_ids` (default `C06`) → `major`
- other Calibration `error` → `minor`
- Calibration `warning` → `warning`
- pass / skipped → no finding; `calibration_overrides` force a class per id.

There is one source of truth for these metrics: Calibration.

## Config (`configs/due_diligence.yaml`)

```yaml
thresholds:
  churn_warn: 0.6
  churn_major: 0.95
  breakeven_warn_month: 24
  runway_minor: 6
  gap_warn: 0.5
  gap_minor: 5.0
  ebitda_regime_year: 3
  revenue_growth_min_multiple: 1.5
blocking_ids: ["C01"]          # calibration ids -> structural
major_ids: ["C06"]             # calibration ids -> major
calibration_overrides: {}      # force a class per calibration id
```

Everything has code defaults; the file may be omitted or partial.

## Outputs

Written to the run's output directory:

- `due_diligence_report.json` / `.md` — verdict, decision fields, liquidity diagnostic, all findings, recommendations.
- `assessment_summary.json` (from `run_assessment`) — verdict + decision fields + stochastic result tagged with `valuation_mode`.
- Plus deterministic artifacts, `calibration_report.*`, and (when allowed) `stochastic_*.csv`.

## Implemented vs conceptual

**Implemented:** `due_diligence/{rules,workflow,report}.py`, `run_assessment` chaining DD → stochastic, `configs/due_diligence.yaml`, smoke tests, real run on `configs/base.yaml`.

**Conceptual / future:** wiring DD as a formal optional CLI/pipeline stage; auto-applying recommended adjustments (currently the consultant edits and re-runs); migrating Calibration rules into a unified DD registry; richer venture-eligibility rules (CAC payback, cohort-level retention).
