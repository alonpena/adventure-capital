# Benchmark v0 — First Validation Report

**Date:** 2026-06-23  
**Pipeline ver:** `workflow-mvp` (commit `e349441`)  
**Configs:** 4 real cases extracted from Alejandro's Excel models  
**Exchange rate:** CLP 900 = 1 USD (uniform)

---

## 1. Approach

Extract 4 real YAML configs from Excel models → run `adventure-capital run --config <yaml> --output outputs/benchmark/<name>` → compare VAN, EBITDA, Revenue against Excel targets (±20% tolerance).

Configs executed in recommended order: GoDemos → Entrena en Casa → Beloop → KavaComex.

Each pipeline stage: Due Diligence → M1-M3 (deterministic MILP) → M4 (stochastic SAA + CVaR).

---

## 2. Results Per Case

### 2.1 GoDemos — ❌ BLOCKED (DD03: VC=0)

| Metric | Model | Excel Target | Δ |
|--------|-------|-------------|----|
| VAN | — | $2,005K | — |
| EBITDA yr1 | — | $177K | — |
| Revenue yr1 | — | $303K | — |

**Block reason:** DD03 `financing_present` fails because `VC: 0`. The company is already operational and cash-flow positive from month 1, but the pipeline strictly requires VC > 0.

**Mitigation:** Set `VC: 1` (symbolic) or add DD03 override config for already-operational cases.

---

### 2.2 Entrena en Casa — ✅ FULL PASS (M4 Optimal)

| Metric | Model (DCF) | Model (Stochastic) | Excel Target | Δ |
|--------|------------|-------------------|-------------|----|
| VAN | $209K | $570K (expected) | $1,413K | **−85% / −60%** |
| EBITDA yr1 | $-101K | — | $-17.8K | large negative |
| EBITDA yr3 | $900K | — | $942K | **−5%** ✅ |
| Revenue yr1 | $75K | — | $173K | **−57%** |
| Revenue yr3 | $1,214K | — | $1,141K | **+6%** ✅ |
| Breakeven | month 24 | month 25 (P50) | month ~24 | ✅ |
| M4 solver | — | **Optimal** | — | ✅ |

**Verdict:** Model runs fully but **VAN is 60-85% below target**. However, EBITDA yr3 and revenue yr3 converge. The issue is **early-stage revenue understatement** and **cost structure mismatch** (negative EBITDA yr1 is much worse than Excel).

---

### 2.3 Beloop — ⚠️ PARTIAL (M4 Not Solved)

| Metric | Model (DCF) | Excel Target | Δ |
|--------|------------|-------------|----|
| VAN | $2,339K | $1,923K | **+22%** ✅ (barely outside ±20%) |
| EBITDA yr1 | $11K | $440K | **−97%** ❌ |
| EBITDA yr3 | $5,313K | $2,388K | **+123%** ❌ |
| Revenue yr1 | $239K | $828K | **−71%** ❌ |
| Revenue yr3 | $6,534K | $4,058K | **+61%** ❌ |

**Verdict:** VAN within tolerance but **yearly trajectory diverges from Excel** — model under-estimates yr1 and over-estimates yr3. M4 solver status: **Not Solved** (CBC timed out at 120s for 2-service SAA with 100 scenarios).

---

### 2.4 KavaComex — ❌ BLOCKED (requires major adjustment)

| Metric | Model (DCF) | Excel Target | Δ |
|--------|------------|-------------|----|
| VAN | **−$156K** | $1,789K | **−109%** ❌ |
| EBITDA yr1 | −$207K | — | negative |
| Cash min | −$135K (month 25) | — | **went negative** |
| Revenue yr1 | $190K | $135K | **+41%** |
| Revenue yr3 | — | $2,361K | — |

**Block reason:** `requires_major_adjustment` — cash goes negative (DD07), no breakeven within horizon (DD06), VAN negative (C06). Product-logistics business model does not fit the SaaS-oriented MILP structure.

**Structural gaps confirmed from summary:**
- Logistics costs not representable in c_u/c_min/u_max
- Product (bottle) vs client revenue model mismatch
- Channel-varying margins collapsed to single ARPU
- No inventory/working capital for supply chain

---

## 3. Cross-Cutting Issues

### 3.1 Solver time limit too tight for complex cases

All 4 configs hardcode `time_limit: 120`. The new M4 defaults raise this to 420s. Beloop (2-service SAA) times out at 120s. Entrena (1-service) solves at 120s but barely — no margin for larger scenario counts.

**Fix:** Configs should omit `time_limit` or use 420s+ for multi-service SAA. Pipeline should propagate M4 defaults when solver block is incomplete.

### 3.2 VC=0 blocks already-operational companies

DD03 requires VC > 0 unconditionally. GoDemos is cash-flow positive from month 1 with zero capital need. The DD gate should differentiate between "VC not provided" (error) and "VC=0 because company is already generating cash" (allowed with warning).

### 3.3 Revenue understatement in early months

Both Entrena and Beloop show yr1 revenue significantly below Excel targets (−57% and −71%). This suggests:
- **A_base acquisition plans may be too conservative** relative to Excel's implicit starting client base
- **Initial active client pool** not captured — Excel models start with existing clients, the MILP starts from zero and grows
- **Ticket/ARPU simplifications** lose revenue granularity (session packages, plan upgrades)

### 3.4 LTV/CAC ratio out of band (all cases)

All 3 runnable cases show LTV/CAC > 60×, far above the [1, 20] calibration band. The formula artifact is known (uses ARPU-weighted lifetime vs effective marginal cost). Unit economics needs service-level decomposition.

### 3.5 Gross margin extreme values

- Beloop: **94.6% gross margin** (c_u/c_min understated for SaaS)
- KavaComex: **26.9% gross margin** (logistics costs too high for MILP structure)

Both indicate the c_u/c_min/u_max cost schema needs calibration per business model.

---

## 4. What Must Be Fixed (Theory)

### 4.1 Pipeline infrastructure

| Issue | Fix | Priority |
|-------|-----|----------|
| VC=0 blocks operational cos | DD03: allow VC=0 with warning if cash-flow positive in first 3 months | **High** |
| Solver timeout for multi-service | YAML `time_limit` inheritance from M4 defaults; increase default to 420s | **High** |
| M4 "Not Solved" silent failure | Better diagnostics on solver status; cascade to deterministic-only report | **Medium** |
| No report.md generated | `run` legacy command skips standard report; `executions` path has it | **Low** (use new CLI) |

### 4.2 Model calibration

| Issue | Fix | Priority |
|-------|-----|----------|
| Revenue yr1 understatement | Add `initial_clients` parameter to seed month 1 active pool | **High** |
| ARPU simplification loses detail | Allow service-level `ticket` as array (period-specific pricing) | **Medium** |
| Multi-service SAA unsolvable | Add Benders decomposition or scenario reduction heuristics | **Low** (future) |
| Gross margin out of band | Better c_u/c_min defaults per industry vertical | **Medium** |

### 4.3 Schema extensions for product-based businesses

KavaComex exposes fundamental model gaps:

| Gap | Required Schema Change | Status |
|-----|----------------------|--------|
| Logistics cost per unit volume | `c_logistics` separate from service delivery cost | Not designed |
| Channel-varying margins | Per-channel service definitions or margin matrix | Not designed |
| Inventory/working capital for supply chain | `ciclo_op` per service or inventory turnover param | Not designed |
| Freelance commission with bonuses | `com_v` already exists but bonus logic is missing | Partial |

**Recommendation:** Create ADR on product-based business model support. Current MILP is SaaS/subscription-oriented. Wine distribution (and similar physical-goods businesses) need at minimum:
- Per-unit COGS separate from service delivery cost
- Inventory holding cost and lead time parameters
- Channel-based revenue segmentation

### 4.4 Due Diligence calibration

| Check | Issue | Fix |
|-------|-------|-----|
| C07 gross_margin [30%, 92%] | SaaS can legitimately be >92% | Make band configurable per industry |
| C08 ltv_cac [1, 20] | Formula artifact inflates ratio | Use per-service LTV/CAC, not blended |
| C09 mix_concentration | Single-service configs always fail | Skip check when N_services = 1 |

---

## 5. Recommended Action Plan

```
Priority 1 — Unblock pipeline for all 4 configs:
  □ DD03: allow VC=0 if cash-positive early
  □ YAML time_limit: remove hardcode, inherit M4 default (420s)

Priority 2 — Fix revenue understatement:
  □ Add initial_clients parameter for seed pool
  □ Validate A_base against Excel's starting client base

Priority 3 — Calibrate for validation targets:
  □ Run benchmark after each fix, compare VAN trajectory
  □ Tune c_u/c_min per service to hit gross margin targets
  □ Validate EBITDA trajectory, not just final VAN

Priority 4 — Schema design for product businesses:
  □ ADR on physical-goods / logistics model support
  □ KavaComex-specific schema extensions
```

---

## 6. Key Numbers at a Glance

| Config | DD | M1-M3 | M4 | VAN (DCF) | VAN Target | Δ | Breakeven |
|--------|----|-------|-----|-----------|------------|----|-----------|
| GoDemos | ❌ VC=0 | — | — | — | $2,005K | — | — |
| Entrena | ✅ | ✅ | ✅ Optimal | $209K | $1,413K | −85% | month 24 |
| Beloop | ✅ | ✅ | ⚠️ Not Solved | $2,339K | $1,923K | +22% | month 12 |
| KavaComex | ❌ major | ✅ | ❌ | −$156K | $1,789K | −109% | never |

Only Beloop hits ±20% on VAN. Entrena converges on yr3 but misses yr1. KavaComex needs new model. GoDemos blocked by infrastructure.
