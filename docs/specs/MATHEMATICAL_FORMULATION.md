# Mathematical Formulation — Adventure Capital

**Date:** 2026-05-29. Reconstructed from `src/adventure_capital/model.py`, `instance.py`, `valuation.py`, `stochastic/model.py`, `stochastic/evaluate.py`, and `docs/model.md`.

**Component labels:** **[I]** implemented in code · **[PI]** partially implemented · **[INF]** inferred from code · **[P]** proposed · **[F]** future work.

> Notation note: the code maximizes **discounted EBITDA** (pre-tax), and applies tax + terminal value **after** solving, inside the DCF. The objective below reflects the code, not an idealized after-tax NPV.

---

## Part 0 — Non-technical explanation (for evaluators)

The model answers: *given a startup's first-year sales assumptions and cost structure, what monthly growth plan (how many clients to acquire, how many salespeople and leaders to hire) maximizes the discounted operating result over a 3-year horizon, subject to realistic growth-speed and capacity limits?*

- **Input:** a YAML file with services (price, churn, repurchase frequency, unit cost), the fixed first-12-month acquisition, the commercial structure (quota per seller, span of control, salaries, commissions), administrative and HR costs, working capital, and discount rate.
- **Decides:** months 13–36 acquisition per service, and the size of the sales team over time.
- **Optimizes:** the present value of monthly EBITDA (revenue − operating cost − acquisition cost − admin − HR).
- **Uncertainty:** treated in two ways — (1) a *stochastic optimizer* that chooses ONE plan good across many sampled scenarios of churn, sales productivity, financing and discount rate; (2) a *Monte Carlo evaluation* that stress-tests that plan over many more scenarios to report the distribution of value, funding gap and break-even.
- **Supports decisions via:** Enterprise Value (DCF), unit economics, a due-diligence verdict, and a robustness distribution — i.e. how much the company is worth, whether the plan is investable, and how fragile it is.

The model treats the firm as an **operating whole valued by its cashflows (Enterprise Value)**, appropriate to an early-stage company; it does not yet compute Equity Value (debt, cap table, dilution).

---

## Part 1 — Deterministic Accelerated Growth Optimization Model

### 1.1 Sets and indices [I]
| Symbol | Meaning |
|---|---|
| $s \in \mathcal{S}=\{0,\dots,S-1\}$ | services |
| $t \in \mathcal{T}=\{1,\dots,H\}$ | planning months (horizon $H$, default 36) |
| $\mathcal{T}_{\text{base}}=\{1,\dots,12\}$ | fixed acquisition months |
| $c \in \{1,\dots,t\}$ | acquisition cohort month |

### 1.2 Parameters [I] (built in `instance.py`)
| Symbol | Code | Meaning |
|---|---|---|
| $A^{\text{base}}_{s,t}$ | `A_base` | given acquisition, $t\le 12$ |
| $p_s$ | `ticket` | service price |
| $f_s$ | `frecuencia` | repurchase frequency (months) |
| $\alpha_{s}$ | `alpha` | repurchase rate |
| $\theta^{\text{ann}}_{s,y}$ | `churn_anual` | annual churn (year $y$) |
| $\theta_{s,t}=1-(1-\theta^{\text{ann}}_{s,y(t)})^{1/12}$ | `churn_mensual` | monthly churn |
| $\phi_{s,c,t}=\prod_{\tau=c+1}^{t}(1-\theta_{s,\tau})$ | `phi` | cohort survival ($\phi_{s,c,c}=1$) |
| $\delta_{s,c,t}=\mathbb{1}[t>c \wedge (t-c)\bmod f_s=0]$ | `delta` | repurchase-window indicator |
| $c^u_s, c^{\min}_s, u^{\max}_s$ | `c_u,c_min,u_max` | unit cost, cost floor, capacity per step |
| $g$ | `g_max_suavizado` | max smoothed growth |
| $m$ (`meta`), $\sigma$ (`sup`) | quota/seller, span of control |
| $r_v,r_l$ (`rem_v,rem_l`); $\kappa_v,\kappa_l$ (`com_v,com_l`) | seller/leader salary; commission rates |
| $G$ (`g_adm`); $W_t$ (`RRHH`) | admin cost; monthly HR cost |
| $V\!C$ (`VC`); $\tau^{\text{tax}}$ (`tax`) | initial working capital; tax rate |
| $i_a$ (`beta_anual`); $i=(1+i_a)^{1/12}-1$ (`beta`) | annual / monthly discount |
| $d_t=(1+i)^{-t}$ | `descuento` | discount factor |
| $\ell$ | `commercial_productivity_lag` | capacity lag (default 0) |

### 1.3 Decision variables [I]
$$A_{s,t}\ge 0\ \text{(acq.)},\quad V_t,L_t\in\mathbb{Z}_{\ge0}\ \text{(sellers,leaders)},\quad m^{op}_{s,t}\in\mathbb{Z}_{\ge0}\ \text{(capacity steps)}$$
Auxiliary (linear) state: $C_{s,t},R_{s,t},Q_{s,t},I_{s,t},\text{Cost}_{s,t},\text{CAC}_t,\text{EBITDA}_t,\text{Caja}_t$.

### 1.4 Objective [I]
$$\max\ \sum_{t\in\mathcal{T}} d_t\,\text{EBITDA}_t \qquad\text{(present value of monthly EBITDA, pre-tax)}$$

### 1.5 Constraints [I]

**Fixed acquisition:** $A_{s,t}=A^{\text{base}}_{s,t},\ \forall s,\ t\le12.$

**Growth smoothing (moving average):**
$$A_{s,13}\le(1+g)\max\!\big(A^{\text{base}}_{s,12},\ \overline{A^{\text{base}}_s}\big),\quad A_{s,14}\le(1+g)A_{s,13},$$
$$A_{s,t}\le\tfrac{1+g}{3}\big(A_{s,t-1}+A_{s,t-2}+A_{s,t-3}\big),\quad t\ge15.$$

**Client/recurrence/revenue/cost (∀ s,t):**
$$C_{s,t}=\sum_{c=1}^{t}\phi_{s,c,t}A_{s,c},\qquad R_{s,t}=\sum_{c=1}^{t-1}\delta_{s,c,t}\,\phi_{s,c,t}\,\alpha_{s}\,A_{s,c},$$
$$Q_{s,t}=A_{s,t}+R_{s,t},\qquad I_{s,t}=p_s Q_{s,t},$$
$$Q_{s,t}\le u^{\max}_s m^{op}_{s,t},\qquad \text{Cost}_{s,t}\ge c^u_s Q_{s,t},\qquad \text{Cost}_{s,t}\ge c^{\min}_s m^{op}_{s,t}.$$

**Commercial capacity (∀ t):**
$$t\le12:\ V_t=\Big\lceil\tfrac{\sum_s A^{\text{base}}_{s,t}}{m}\Big\rceil,\ L_t=\Big\lceil\tfrac{V_t}{\sigma}\Big\rceil;\qquad
t\ge13:\ \sum_s A_{s,t}\le m\,V_{\max(1,t-\ell)},\ V_t\le\sigma L_t.$$
**Monotone team:** $V_t\ge V_{t-1},\ L_t\ge L_{t-1}\ (t\ge13).$

**CAC and EBITDA (∀ t):**
$$\text{CAC}_t=r_v V_t+r_l L_t+\sum_s(\kappa_v+\kappa_l)p_s A_{s,t},$$
$$\text{EBITDA}_t=\sum_s I_{s,t}-\sum_s\text{Cost}_{s,t}-\text{CAC}_t-G-W_t.$$

**Cash recursion:** $\text{Caja}_1=V\!C+\text{EBITDA}_1,\quad \text{Caja}_t=\text{Caja}_{t-1}+\text{EBITDA}_t.$

**Liquidity policy [I, default off]:** `none` → none; `nonnegative` → $\text{Caja}_t\ge0$; `minimum_cash` → $\text{Caja}_t\ge \underline{c}$.

### 1.6 Output variables consumed by valuation [I]
Monthly $\{I_{s,t},\text{Cost}_{s,t},\text{CAC}_t,\text{EBITDA}_t,\text{Caja}_t,A_{s,t},C_{s,t},Q_{s,t}\}$ → `optimized_results.csv`.

### 1.7 Post-optimization valuation (Enterprise Value) [I]
$$\text{Tax}_t=\max(\tau^{\text{tax}}\text{EBITDA}_t,0),\quad FC_t=\text{EBITDA}_t-\text{Tax}_t,\quad FC^{\text{desc}}_t=FC_t(1+i)^{-t},$$
$$\text{TV}=\begin{cases}0 & \text{none}\\ \max(12\cdot\text{EBITDA}_H\cdot \mu,0) & \text{ebitda\_multiple}\\ \max\!\big(\tfrac{12\,\text{EBITDA}_H(1+g_\infty)}{i_a-g_\infty},0\big) & \text{gordon}\end{cases}$$
$$\boxed{\;\text{EV}=\text{VAN}=-V\!C+\sum_{t}FC^{\text{desc}}_t+\text{TV}\,(1+i)^{-H}\;}$$
**Note [I]:** EBITDA is used as an FCF proxy (no D&A/capex/ΔWC beyond $V\!C$); tax has no loss carry. This is **Enterprise Value**; Equity Value (debt, cap table) is **[F]**.

---

## Part 2A — Monday-safe stochastic layer: Monte Carlo robustness evaluation [I]

> This evaluates a **fixed** plan; it does **not** re-optimize. Implemented in `stochastic/evaluate.py`.

**Scenario vector** $\xi_s$ [I]: multipliers $(\rho^{\text{churn}},\rho^{\text{prod}},\rho^{\text{fin}})$ and absolute WACC $w$, sampled triangular, seeded. Applied via $\theta^{\text{ann}}_s\!\leftarrow\!\text{clip}(\rho^{\text{churn}}\theta^{\text{ann}}_s,0,1)$, $m\!\leftarrow\!\rho^{\text{prod}}m$, $V\!C\!\leftarrow\!\rho^{\text{fin}}V\!C$, $i_a\!\leftarrow\!w$.

Let $x^\* = (A^\*,V^\*,L^\*)$ be the chosen plan. For each scenario $\omega\in\{1..N\}$, with **closed-form recourse**
$$m^{op}_{s,t}=\lceil Q_{s,t}/u^{\max}_s\rceil,\qquad \text{Cost}_{s,t}=\max(c^u_sQ_{s,t},c^{\min}_sm^{op}_{s,t}),$$
compute $\text{EBITDA}_t(\omega)$, cash, and:
$$V(x^\*,\xi_\omega)=\text{VAN}_\omega,\quad \text{gap}_\omega=\max_t(\text{floor}-\text{Caja}_t),\quad \text{BE}_\omega=\min\{t:\textstyle\sum_{\tau\le t}\text{EBITDA}_\tau\ge0\}.$$

**Aggregates [I]:** $\mathbb{E}[\text{VAN}]=\sum_\omega p_\omega\text{VAN}_\omega$; empirical $p_{10},p_{50},p_{90}$, min/max/std; $P(\text{VAN}<0)$, $P(\text{gap}>0)$, $\mathbb{E}[\text{gap}]$, $\max\text{gap}$; break-even median and $P(\text{no BE})$.

**[P] add for thesis:** $P(\text{ARR}^{\$}_{\text{yr3}}\ge \text{target})$, $P(\text{EV}\ge \lambda\cdot\text{investment})$. **Honest claim:** Part 2A alone is *robustness evaluation*, not stochastic optimization.

---

## Part 2B — Stochastic optimization actually implemented (two-stage SAA) [I]

> Implemented in `stochastic/model.py`. This **is** stochastic optimization (expected-value).

**Scenario set** $\Omega$, probabilities $p_\omega$ (SAA: $p_\omega=1/N$). Per-scenario instance data $\phi^\omega,\delta^\omega,\alpha^\omega,d^\omega,m^\omega,V\!C^\omega$.

**First-stage (shared):** $A_{s,t},V_t,L_t$ — same growth-smoothing, span, monotonicity, and 1–12 fixing as §1.5.
**Recourse (per $\omega$):** $m^{op}_{s,t,\omega}$ and all financials $C,R,Q,I,\text{Cost},\text{CAC},\text{EBITDA},\text{Caja},\text{gap}$.

**Objective [I]:**
$$\max\ \sum_{\omega}p_\omega\Big(\sum_t d^\omega_t\,\text{EBITDA}_{t,\omega}+d^\omega_H\,\mu\,\text{EBITDA}_{H,\omega}\Big)$$
(linear terminal proxy $\mu$, default 1; no tax, no $\max$, $V\!C$ excluded as a constant). Capacity uses $m^\omega$; funding gap diagnostic only: $\text{gap}_{t,\omega}\ge\text{floor}-\text{Caja}_{t,\omega},\ \ge0$ (no hard floor).

Solve once with CBC → first-stage $x^\*$ → feed Part 2A for the distribution.

---

## Part 2C — Future stochastic optimization [F]

**Risk-adjusted / chance-constrained two-stage program** (documented, not built — ADR 0004):
$$\max\ (1-\beta)\,\mathbb{E}_\omega[\text{NPV}_\omega]+\beta\big(\text{CVaR}_{\eta}[\text{NPV}_\omega]\big)$$
$$\text{s.t. } P_\omega(\text{Caja}_{t,\omega}\ge \text{floor})\ge a\ \ \forall t \quad(\text{cash-survival chance constraint})$$
$$P_\omega(\text{ARR}^{\$}_{\text{yr3},\omega}\ge \text{target})\ge b \quad(\text{investment-thesis chance constraint})$$
with optional emergency-financing recourse $z_{t,\omega}\ge0$ at penalty cost. Scenario-dependent churn/CAC/discount/financing as in §2A.

**Code changes required to go from 2A/2B → 2C [INF]:**
1. CVaR: add aux var $\eta$ + per-scenario $u_\omega\ge0,\ u_\omega\ge \eta-\text{NPV}_\omega$; objective term $\eta-\tfrac1{1-\eta}\sum p_\omega u_\omega$.
2. Chance constraints: add binary $y_{t,\omega}$ (big-M) for $\text{Caja}_{t,\omega}\ge\text{floor}$; constrain $\sum_\omega p_\omega y_{t,\omega}\ge a$. (Raises solve cost sharply.)
3. After-tax in objective: linearize $\max(\tau\,\text{EBITDA},0)$ with an aux non-negative tax variable.
4. Thesis constraint: add ARR-$ accounting variables + target binary.
5. Emergency financing recourse + cost in objective.

---

## Part 3 — Implemented vs proposed (summary)

| Component | Status |
|---|---|
| Deterministic MILP (§1) | **[I]** |
| EV / DCF, terminal value (§1.7) | **[I]** |
| Two-stage SAA stochastic optimization (§2B) | **[I]** |
| Monte Carlo robustness evaluation (§2A) | **[I]** |
| Equity Value, after-tax-in-objective | **[F]** |
| CVaR / chance constraints / thesis constraint (§2C) | **[F]** |
| ARR-$ / MRR-$ accounting, clients-to-thesis | **[F]** |
