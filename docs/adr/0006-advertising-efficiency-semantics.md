# Advertising efficiency semantics

Status: Accepted (header añadido 2026-07-12; decisión vigente, sin revisión desde su creación)

The advertising acquisition channel uses **one** formulation: a continuous linear
recta `A_ad_total[t] = a + b * I_ad[t]`, where `I_ad[t]` is advertising investment
(USD) and `A_ad_total[t]` is advertising-acquired customers. Coefficients are
preprocessed from instance YAML as `b = (A_max - A_min) / (I_max - I_min)` and
`a = A_min - b * I_min`.

## Decisions

- **More investment → more customers** (`b > 0`, enforced by the validator). The
  implied USD/customer (`I_ad / A_ad_total`) improves as investment rises — a volume
  discount, by business assumption of the mandante.
- **Activation is exogenous.** `channels.advertising.active` is a YAML parameter, never
  a decision variable. There is no channel-activation binary in the model.
- **Continuous only.** `I_ad[t]`, `A_ad_total[t]`, and `advertising_cac_cost[t] = I_ad[t]`
  are continuous. No binaries, no discretization, no piecewise segments.
- **Saturation cap.** `A_ad_total[t] <= A_ad_cap` bounds per-period advertising volume.
- **Investment range applies to the optimized horizon only.** `I_min <= I_ad[t] <= I_max`
  for `t >= 13`. Months 1-12 are the exogenous Fixed Acquisition Period; the recta still
  holds there but the investment range does not constrain it.
- **Share constraints are linear parameter bounds**, not decision variables:
  `A_ch_total[t] >= min_share * A_total[t]` and `<= max_share * A_total[t]`. Effective
  channel proportions are post-solve diagnostics. This deliberately avoids the bilinear
  products that proportion decision variables would introduce.

No alternative advertising formulations (response curves, diminishing-returns concavity,
binary activation) are planned. If one is ever needed it supersedes this ADR.
