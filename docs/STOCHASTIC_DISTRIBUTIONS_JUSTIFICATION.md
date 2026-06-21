# Stochastic Distributions Justification

Status: design specification.  
Scope: stochastic optimization distribution choices and rationale. No implementation implied.

## 1. Methodological position

The stochastic extension is part of the full Adventure Capital pipeline, not an isolated simulation:

```text
deterministic optimization
→ due diligence filter
→ stochastic optimization if DD allows
→ Monte Carlo ex-post evaluation
→ report/UI artifacts
```

Target stochastic method:

1. Latin Hypercube Sampling (LHS) for scenario generation.
2. Sample Average Approximation (SAA) for stochastic optimization.
3. Independent Monte Carlo evaluation of the selected SAA plan.

Base objective:

```text
maximize expected NPV / expected valuation across SAA scenarios
```

Risk metrics are evaluation outputs unless a later academic argument justifies adding CVaR, chance constraints, or another risk-averse objective.

## 2. Distribution selection principles

Do not use triangular distribution blindly. Choose by variable properties:

| Variable property | Candidate distribution |
|---|---|
| bounded rate in [0,1], expert min/mode/max | Beta-PERT |
| bounded multiplier with scarce data | triangular or Beta-PERT |
| positive right-skewed cost/effect multiplier | truncated lognormal |
| financial rate with practical min/max | truncated normal or discrete stress scenarios |
| strategic unknown with no credible distribution | sensitivity-only |
| rare event / regime shift | discrete scenarios |

LHS samples quantiles from chosen marginal distributions. Correlations may be added later, but first version can assume independent marginals while documenting this limitation.

## 3. Distribution matrix

| Variable | Proposed distribution | Parameterization | SAA? | MC? | Sensitivity? | Exclude? | Rationale |
|---|---|---|---:|---:|---:|---:|---|
| Churn | Beta-PERT on annual churn or churn multiplier | min / mode / max per service-year | yes | yes | yes | no | bounded [0,1], expert-estimated, strong effect on cohort survival |
| Salesforce productivity | Beta-PERT or triangular multiplier | min / mode / max around `meta` | yes | yes | yes | no | bounded commercial productivity uncertainty; can affect feasibility/capacity |
| Advertising effectiveness | truncated lognormal or Beta-PERT multiplier on `b` | median=1, low/high quantiles, cap | yes if advertising active | yes if active | yes | no if inactive | ad response often multiplicative and right-skewed; activation comes from YAML |
| B2B/third-party productivity | discrete scenarios or Beta-PERT multiplier | low/base/high conversion or commission productivity | yes if third-party active | yes if active | yes | no if inactive | partner channels often have regime-like uncertainty and scarce data |
| Discount rate / WACC | truncated normal or discrete scenarios | mean/base WACC, sd, min/max; optional stress levels | yes | yes | yes | no | financial uncertainty; bounded to avoid nonsensical rates |
| ARPU / ticket | sensitivity-only by default; optional truncated normal per service | base ticket, ± range | no by default | optional | yes | no | price is a strategic decision/input, not usually random unless explicitly modeled |
| Operating cost multiplier | truncated lognormal or Beta-PERT | service-level multiplier on `c_u`, `c_min` | yes | yes | yes | no | costs are positive and may be skewed upward |
| Recurrence / alpha | Beta-PERT bounded multiplier or direct alpha | min/mode/max, clamp [0,1] | yes | yes | yes | no | recurrence is bounded and materially affects revenue |
| VC financing ticket | sensitivity-only or discrete scenarios | committed/base, downside/upside availability | no by default | yes diagnostic | yes | no | DD handles financing feasibility; should not drive objective unless financing uncertainty is real decision context |

## 4. Variable-by-variable justification

### 4.1 Churn

Recommended representation:

```yaml
churn:
  distribution: beta_pert
  level: service_year
  parameters:
    Consultoria_Estrategica:
      year_1: {min: 0.35, mode: 0.45, max: 0.60}
      year_2: {min: 0.22, mode: 0.30, max: 0.45}
    Taller_Formacion:
      year_1: {min: 0.40, mode: 0.50, max: 0.70}
```

Justification:

- Annual churn is naturally bounded between 0 and 1.
- Startup churn is usually elicited from expert/benchmark assumptions, not large historical samples.
- Beta-PERT uses min/mode/max like triangular but produces smoother, less extreme mass at endpoints.

Belongs in:

- SAA: yes, changes optimal acquisition intensity through survival/recurrence.
- MC: yes, key downside distribution driver.
- Sensitivity: yes, report should show churn sensitivity.

### 4.2 Salesforce productivity

Recommended representation:

```yaml
salesforce_productivity:
  distribution: beta_pert
  multiplier_on: meta
  parameters: {min: 0.65, mode: 1.0, max: 1.20}
```

Justification:

- Commercial productivity is bounded by staffing/process limits.
- `meta` already controls acquisition capacity per seller.
- Beta-PERT is preferred when a business expert can define optimistic/base/pessimistic values.
- Triangular acceptable for MVP if implementation complexity must stay low.

Belongs in:

- SAA: yes.
- MC: yes.
- Sensitivity: yes.

### 4.3 Advertising effectiveness

Advertising exists only when enabled in YAML. Activation is not stochastic and not a model decision.

Recommended representation:

```yaml
advertising_effectiveness:
  distribution: truncated_lognormal
  multiplier_on: advertising.b
  parameters:
    median: 1.0
    p10: 0.65
    p90: 1.35
    min: 0.30
    max: 2.00
```

Alternative for scarce data:

```yaml
advertising_effectiveness:
  distribution: beta_pert
  multiplier_on: advertising.b
  parameters: {min: 0.6, mode: 1.0, max: 1.4}
```

Justification:

- Digital/ad response is often multiplicative and right-skewed.
- A lognormal multiplier allows upside while preserving positivity.
- Truncation prevents extreme unrealizable response rates.
- The deterministic advertising recta remains: `A_ad = a + b_ω I_ad`; scenario uncertainty may multiply slope `b` and/or cap `A_ad_cap` if justified.

Belongs in:

- SAA: yes if advertising active.
- MC: yes if advertising active.
- Sensitivity: yes.
- Exclude if `channels.advertising.active = false`.

### 4.4 B2B / third-party productivity

Recommended representation when third-party channel is active:

```yaml
third_party_productivity:
  distribution: discrete
  multiplier_on: third_party_conversion
  scenarios:
    - {name: low_partner_yield, probability: 0.25, multiplier: 0.60}
    - {name: base_partner_yield, probability: 0.50, multiplier: 1.00}
    - {name: high_partner_yield, probability: 0.25, multiplier: 1.30}
```

Alternative:

```yaml
third_party_productivity:
  distribution: beta_pert
  parameters: {min: 0.5, mode: 1.0, max: 1.4}
```

Justification:

- B2B/partner channels often have regime-like uncertainty: partner activates, underperforms, or overperforms.
- If there is no empirical data, discrete scenarios are easier to justify than continuous precision.
- Commission rate itself should usually remain contractual/fixed; productivity/conversion is uncertain.

Belongs in:

- SAA: yes if third-party active and the SAA model includes third-party mechanics.
- MC: yes.
- Sensitivity: yes.
- Exclude if inactive.

### 4.5 Discount rate / WACC

Recommended representation:

```yaml
wacc:
  distribution: truncated_normal
  value_type: annual_rate
  parameters:
    mean: 0.35
    sd: 0.05
    min: 0.15
    max: 0.70
```

Alternative for academic/report clarity:

```yaml
wacc:
  distribution: discrete
  scenarios:
    - {name: low_rate, probability: 0.25, value: 0.25}
    - {name: base_rate, probability: 0.50, value: 0.35}
    - {name: high_rate, probability: 0.25, value: 0.50}
```

Justification:

- WACC is not naturally triangular; it is a financial assumption with bounded plausible range.
- Truncated normal works for local uncertainty around a base estimate.
- Discrete scenarios are more transparent when WACC is an investor-case assumption rather than observed random variable.

Belongs in:

- SAA: yes if objective is expected NPV under valuation uncertainty.
- MC: yes.
- Sensitivity: yes, especially WACC × multiple matrix.

### 4.6 ARPU / ticket

Default recommendation: sensitivity-only.

```yaml
ticket_sensitivity:
  Consultoria_Estrategica: [-0.15, 0.0, 0.15]
  Taller_Formacion: [-0.10, 0.0, 0.10]
```

Optional stochastic representation:

```yaml
ticket_multiplier:
  distribution: truncated_normal
  parameters: {mean: 1.0, sd: 0.08, min: 0.75, max: 1.25}
```

Justification:

- Ticket/price is often a management decision and a YAML input, not exogenous randomness.
- Treating ticket as random inside SAA can blur decision vs uncertainty.
- Use stochastic ticket only when there is evidence of realized price dispersion or contract uncertainty.

Belongs in:

- SAA: no by default.
- MC: optional.
- Sensitivity: yes.

### 4.7 Operating cost multiplier

Recommended representation:

```yaml
operating_cost_multiplier:
  distribution: truncated_lognormal
  level: service
  multiplier_on: [c_u, c_min]
  parameters:
    median: 1.0
    p10: 0.90
    p90: 1.25
    min: 0.75
    max: 1.75
```

Alternative: Beta-PERT if expert min/mode/max is easier.

Justification:

- Cost overruns are positive and commonly right-skewed.
- Multiplicative uncertainty preserves cost positivity.
- Can affect optimal scale and channel intensity.

Belongs in:

- SAA: yes if operating-cost uncertainty is central to plan choice.
- MC: yes.
- Sensitivity: yes.

### 4.8 Recurrence / alpha

Recommended representation:

```yaml
recurrence:
  distribution: beta_pert
  level: service
  multiplier_on: alpha
  clamp: [0.0, 1.0]
  parameters:
    Consultoria_Estrategica: {min: 0.65, mode: 0.80, max: 0.90}
    Taller_Formacion: {min: 0.50, mode: 0.70, max: 0.85}
```

Justification:

- Repurchase probability is bounded in [0,1].
- It can materially change recurring revenue and valuation.
- Beta-PERT fits expert-elicited probability assumptions.

Belongs in:

- SAA: yes.
- MC: yes.
- Sensitivity: yes.

### 4.9 VC financing ticket

Default recommendation: not in SAA objective. Use DD and MC diagnostics.

```yaml
vc_financing:
  treatment: monte_carlo_diagnostic
  distribution: discrete
  scenarios:
    - {name: committed_ticket, probability: 0.70, multiplier: 1.00}
    - {name: partial_ticket, probability: 0.20, multiplier: 0.80}
    - {name: bridge_required, probability: 0.10, multiplier: 0.60}
```

Justification:

- Financing feasibility is already handled by DD.
- Penalizing financing gap in the SAA objective would double-count the DD role and distort the goal of finding the expected-NPV-optimal growth plan.
- VC uncertainty is better reported as probability of needing bridge capital or missing startup criteria.

Belongs in:

- SAA: no by default.
- MC: yes as diagnostic if financing availability is uncertain.
- Sensitivity: yes.
- Objective: no, unless future methodology explicitly optimizes under financing availability constraints.

## 5. SAA vs Monte Carlo inclusion policy

| Variable | Include in SAA when... | Include only in MC/sensitivity when... |
|---|---|---|
| churn | acquisition plan should adapt to retention uncertainty | churn used only for downside communication |
| salesforce productivity | staffing/acquisition constraints affected | productivity is fixed by contract/team plan |
| advertising effectiveness | advertising active and spend is a decision | advertising inactive or only narrative |
| third-party productivity | third-party active and channel share decision exists | partner channel inactive or fixed quota |
| WACC | expected valuation is objective | WACC only used for sensitivity table |
| ticket | price realization uncertain and not decision-controlled | ticket is strategic input |
| operating cost | cost uncertainty affects optimal scale | cost variation only used in sensitivity |
| recurrence | recurring revenue materially drives value | recurrence assumed fixed |
| VC financing | rarely; only if financing availability changes feasible decision set | default: DD/MC diagnostic |

## 6. LHS scenario artifact schema

Target `lhs_scenarios.csv` should include:

| Field | Meaning |
|---|---|
| `scenario` | scenario ID |
| `sample_index` | LHS stratum index |
| `probability` | usually `1/N` |
| `seed` | scenario generation seed |
| `generation_method` | `lhs` |
| `distribution_version` | config/schema version |
| `churn_<service>_year_<n>` | sampled annual churn or multiplier |
| `salesforce_productivity_multiplier` | sampled `meta` multiplier |
| `advertising_effectiveness_multiplier` | sampled ad slope/cap multiplier if active |
| `third_party_productivity_multiplier` | sampled partner productivity if active |
| `wacc_value` | annual WACC |
| `ticket_multiplier_<service>` | optional |
| `op_cost_multiplier_<service>` | optional |
| `recurrence_<service>` | sampled alpha or multiplier |
| `vc_multiplier` | optional MC diagnostic |

## 7. Correlation policy

Initial version may assume independence but must document it. Later correlation examples:

| Pair | Expected relationship |
|---|---|
| high churn and low recurrence | negative customer quality / retention regime |
| low sales productivity and high CAC | poor commercial execution |
| high WACC and lower financing availability | market stress regime |
| high operating cost and low gross margin | cost-inflation regime |

Do not introduce correlation until it can be explained in the report and reproduced in scenario artifacts.

## 8. Safe academic wording

Use:

> “Las variables inciertas se parametrizan mediante distribuciones acotadas y trazables, seleccionadas según la naturaleza de cada variable: Beta-PERT para tasas acotadas, lognormal truncada para multiplicadores positivos sesgados y escenarios discretos para incertidumbre estratégica.”

Use:

> “La primera versión SAA utiliza una función objetivo neutral al riesgo basada en VAN esperado. Las métricas de riesgo se reportan ex-post sobre una muestra Monte Carlo independiente.”

Avoid:

- “Todas las variables siguen distribución triangular.”
- “El modelo es robusto” unless a robust or risk-averse objective is implemented.
- “La probabilidad de éxito VC está optimizada” unless DD criteria are embedded in the objective or chance constraints.
- “LHS calibra distribuciones” — LHS samples; calibration requires data/evidence.

## 9. P1 stochastic/distribution gaps

1. Replace triangular random sampling with LHS over declared marginals.
2. Add distribution schema validation.
3. Make scenario generation channel-aware.
4. Add `lhs_scenarios.csv` as auditable artifact.
5. Align stochastic SAA model with deterministic commercial channels and acquisition ceiling.
6. Add MC diagnostics for DD/VC criteria without adding objective penalties.
7. Document independence assumption and later correlation roadmap.
