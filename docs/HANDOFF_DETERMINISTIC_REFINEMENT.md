# Handoff — Deterministic Refinement Complete

Date: 2026-06-12
Branch: `feature/deterministic-refinement`
Remote: `origin` (`git@github.com:alonpena/adventure-capital.git`)

## Self-assessment

The deterministic optimization refinement is implemented across five staged commits and verified locally. The current local branch was ahead of GitHub by two commits when audited (`854d930`, `97ff8ad`). This handoff captures the remaining repo hygiene required for a reproducible GitHub branch: commit the planning document, restore the root demo config referenced by tests/docs, and include the CLI `all` command used by stage handoff demo commands.

## Commit chain

```text
a8f21a9 feat: Phase 1 — logarithmic acquisition ceiling with slack
64e988a feat: Phase 2 — advertising channel, channel split, share bounds
d8611b9 feat: Phase 3 — CAC cost-component aggregation and traceability
19b6d82 feat: Phase 4 — working-capital cash floor with DD diagnostic
854d930 feat: Phase 4 — working-capital cash floor with DD diagnostic
97ff8ad feat: Phase 5 — unit economics, LTV/CAC consistency, breakeven analysis
```

Notes:

- `19b6d82` was already on `origin/feature/deterministic-refinement`.
- `854d930` is the follow-up Phase 4 DD/pipeline wiring.
- `97ff8ad` is Phase 5 unit economics.

## What is complete

### Phase 1 — Acquisition ceiling

- Formula-based logarithmic ceiling from consensual year-1 plan.
- Optional explicit override preserved.
- Total acquisition cap applies across services and future channels.

### Phase 2 — Channel split and advertising

- Separate acquisition channels (`salesforce`, `advertising`, `third_party`).
- Continuous advertising recta (`A_ad = a + b * I_ad`).
- Optional channel share bands, no proportion decision variables.

### Phase 3 — CAC traceability

- MILP CAC cost components.
- `CAC` remains total alias.
- Per-user CAC ratios are post-solve arithmetic only.

### Phase 4 — Working-capital cash floor

- Hard floor `Caja[t] >= -VC` when `working_capital.enabled`.
- Main objective remains discounted EBITDA only.
- Secondary diagnostic solve measures financing gap only after main infeasibility.
- DD alert `DD11` wired for financing gap.

### Phase 5 — Unit economics

- LTV annualized and summed by service line.
- CAC uses cumulative CAC per user.
- C08 high LTV/CAC remains a documented calibration artifact.
- Breakeven/payback/runway pure functions added and tested.

## Verification

Latest full local test run:

```bash
uv run pytest
# 101 passed, 3 skipped
```

After Phase 5 plus existing local test files, later audit run showed:

```bash
uv run pytest
# 101 passed, 3 skipped
```

If new tracked/untracked files are committed, rerun:

```bash
uv run pytest
```

## GitHub state

Before final repo-hygiene commit:

```text
origin/feature/deterministic-refinement -> 19b6d82
local feature/deterministic-refinement  -> 97ff8ad
local ahead of origin by 2 commits
```

Final handoff commits:

```text
bdfc093 chore: document deterministic refinement handoff
<current HEAD> docs: update deterministic refinement github handoff
```

After push:

```text
origin/feature/deterministic-refinement == local feature/deterministic-refinement
git rev-list --left-right --count origin/feature/deterministic-refinement...HEAD -> 0 0
```

GitHub draft PR opened:

```text
https://github.com/alonpena/adventure-capital/pull/1
```

PR title: `Deterministic refinement phases 1–5`.

## Repo hygiene fixed in final handoff commit

- `docs/PLAN_DETERMINISTIC_ACQUISITION_CAC_CASH.md` is the planning/audit source document and should be tracked.
- `configs/demo-complex.yaml` is referenced by tests/docs and should be tracked. It matches `configs/legacy/demo-complex.yaml`.
- `src/adventure_capital/cli.py` adds the `adventure-capital all` command used by `docs/STAGE_4.md` demo commands.

## Known remaining dirty/untracked files to ignore unless explicitly requested

Examples observed locally:

- `.Rhistory`
- `.DS_Store` files
- local presentation/spec docs (`MONDAY_*`, `CLAUDE_PLAN_INFORME.md`, etc.)
- local demo configs not referenced by tests (`configs/demo-good.yaml`, `configs/demo-bad.yaml`, `configs/demo-target.yaml`) unless product decides to track them
- `scripts/demo.sh` unless desired as official script

Do not commit those without explicit review.

## Open debt

- Phase 5 breakeven/payback/runway metrics are computed/tested but not yet persisted/rendered in the standard report.
- Calibration C08 message can be refreshed now that LTV is annual and service-summed.
- Stochastic parity remains flagged: deterministic refinements (ceiling, channels, CAC, cash floor) need stochastic SAA/Monte Carlo parity work later.
- Existing stochastic ex-post evaluator initializes cash from `0.0`; deterministic initializes `VC + EBITDA[1]`. Known issue, out of current scope.

## Next-agent console prompt

```text
You are continuing adventure-capital on branch feature/deterministic-refinement.

Context:
- Five deterministic refinement phases are implemented.
- Key commits: a8f21a9 Phase 1, 64e988a Phase 2, d8611b9 Phase 3, 854d930 Phase 4 DD wiring, 97ff8ad Phase 5.
- Current expected tests: uv run pytest -> 101 passed, 3 skipped.
- docs/HANDOFF_DETERMINISTIC_REFINEMENT.md and docs/STAGE_1..5.md explain implementation state.

First actions:
1. Run `git status --short --branch` and confirm no unintended dirty tracked files.
2. Run `git fetch origin --prune` and compare local branch to `origin/feature/deterministic-refinement`.
3. Run `uv run pytest`.
4. Audit whether `configs/demo-complex.yaml` and `docs/PLAN_DETERMINISTIC_ACQUISITION_CAC_CASH.md` are tracked; tests/docs reference them.
5. Do not commit local `.DS_Store`, `.Rhistory`, presentation docs, or unrelated demo files unless explicitly requested.

Focus areas for review:
- Phase 4 hard cash floor: main objective must remain discounted EBITDA only; diagnostic solve separate.
- Phase 5 LTV: annual, service-summed; CAC cumulative; C08 high ratio remains alert.
- Reproducibility on clean GitHub checkout.

If asked to continue work, prefer a fresh session because current conversation context is large.
```
