# CLI Workflow MVP

Status: implementation plan for replacing the near-term UI dependency with a filesystem-backed CLI workflow.

## Goal

Provide a usable local workflow for instances, executions, M4 stochastic runs, and M5 simple HTML reporting without building the Streamlit UI first.

## Storage

Use filesystem registry for MVP. Do not add SQLite yet.

```text
outputs/
  instances/
    <instance_id>/
      instance.yaml
      metadata.json
  executions/
    <run_id>/
      execution.json
      config.yaml
      ...canonical artifacts...
```

SQLite may be added later as a read/index cache over these files. Canonical financial source of truth remains CSV/JSON artifacts.

## Commands

```bash
adventure-capital instances create --config configs/base.yaml --name "Caso base"
adventure-capital instances list
adventure-capital instances show <instance_id>

adventure-capital executions run --instance <instance_id>
adventure-capital executions list
adventure-capital executions status <run_id>
adventure-capital executions stochastic <run_id> --time-limit 420
adventure-capital executions report <run_id>
```

## Execution gate behavior

`executions run` runs M1-M3 first: deterministic PCA, valuation/unit economics, and Due Diligence. It then decides whether to run M4.

| DD verdict | M4 behavior | valuation_mode |
|---|---:|---|
| `passed` | auto-run M4 | `final` |
| `passed_with_warnings` | prompt for confirmation | `final` |
| `requires_minor_adjustment` | prompt for confirmation | `warning` |
| `requires_major_adjustment` | blocked | `none` |
| `rejected_for_stochastic` | blocked | `none` |

Interactive prompt for warning/minor:

```text
Due Diligence has warnings/minor issues. Run M4 anyway? [y/N]
```

Non-interactive flags:

```bash
--yes             # confirm warning/minor and run M4
--no-stochastic   # stop after M3 even if allowed
```

M4 time limit:

```bash
--stochastic-time-limit 420
```

Default M4 time limit should come from backend M4 defaults and be at least 420s for mixed-channel cases.

## M5 report behavior

`executions report <run_id>` generates a simple direct artifact report:

```text
outputs/executions/<run_id>/report.html
```

It reads canonical artifacts directly and should not depend on the older standard report pipeline. PDF is out of scope for MVP.

Minimum sections:

1. Portada/metadata.
2. Executive KPIs.
3. M1 deterministic PCA summary.
4. M2 valuation and unit economics.
5. M3 Due Diligence verdict and recommendations.
6. M4 stochastic PCA summary when present: CVaR, expected VAN, percentiles, final active clients, runway, funding gap.
7. Artifact links/list.
