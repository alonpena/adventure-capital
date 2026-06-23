# YAML Extraction Summary — Real Cases from Alejandro's Excel
## Adventure Capital Pipeline Validation Configs

**Date:** 2026-06-22
**Exchange Rate:** CLP 900 = 1 USD
**Beta Standard:** 0.35 (configurable)
**Tolerance Target:** ±20% VAN

---

## 1. GoDemos (`godemos.yaml`) — PRIORITY 1 (cleanest mapping)

**Model:** B2C platform (memberships) + B2B services (casting/demos/mentorías)
**Complexity:** Medium — 2 revenue streams with different dynamics

| Parameter | Excel Value | YAML Value | Simplification |
|-----------|-------------|------------|----------------|
| B2C ticket | $20.6/month Basic/Pro mix | $47/month | Collapsed to monthly ARPU (includes quarterly recurrence pattern) |
| B2B ticket | Casting $546 + Demos $600 + Mentorías $150 | $510/event | Weighted by service volume (casting-dominant) |
| B2C churn | 3.51%→3.32%→3.20% monthly | 35%/33%/33% annual | Standard conversion 1-(1-r)^12 |
| B2B churn | 6%→3%→2.5% monthly | 52%/31%/26% annual | Standard conversion |
| meta | 5 nominal, 2 sellers | 15 effective | Adjusted: platform-driven acquisition, not pure salesforce |
| Advertising | CLP 200K/month +1% MoM | Absorbed in g_adm | Model treats ads as decision variable |
| VC | 0 (already operational) | 0 | Breakeven from month 1 |

**Validation Targets:** VAN ≈ 2,005 MUS$, EBITDA yr1 ≈ 177 MUS$, Revenue yr1 ≈ 303 MUS$

---

## 2. Entrena en Casa (`entrena-en-casa.yaml`) — PRIORITY 2

**Model:** Session-based fitness (Individual/Duo/Grupal/Empresa)
**Complexity:** High simplification needed — 4 service types × 3 package sizes × 2 modalities

| Parameter | Excel Value | YAML Value | Simplification |
|-----------|-------------|------------|----------------|
| Ticket | $2.64/session, $29.25/package | $143/month | Monthly ARPU = Revenue/avg_clients/12 |
| Service types | Individual(56%)/Duo(26%)/Grupal(9%)/Empresa(8%) | Single service | Weighted average of all types |
| Frequency | 9.69 sessions/client/month, 3.22 purchases/year | 1 (monthly) | Monthly aggregation of all session purchases |
| Churn | Individual 2.07%/month, weighted ~1.4% | 22%/15%/7% annual | Stock-based monthly rate converted to annual |
| Cost | $10.53/session presencial | c_u=$10, c_min=$8K | Session cost × capacity structure |
| VC | CLP M$ 114,471 → $127K | $114K | Direct conversion |

**⚠ Key Gap:** The ARPU ($143/month) vs. the stated ticket ($167.59) divergence occurs because the Excel's "ticket" is per-package while clients buy multiple packages/month. The ARPU-based approach matches revenue output better.

**Validation Targets:** VAN ≈ 1,413 MUS$, EBITDA yr1 ≈ -17.8 MUS$ (negative!), Revenue yr1 ≈ 173 MUS$

---

## 3. Beloop (`beloop.yaml`) — PRIORITY 3

**Model:** SaaS B2B (Simple/Pro/Enterprise plans)
**Complexity:** Medium — plan downgrades not capturable

| Parameter | Excel Value | YAML Value | Simplification |
|-----------|-------------|------------|----------------|
| Plans | Simple/Pro/Enterprise with different pricing | 2 services | Recurrente (Simple+Pro) + Enterprise |
| Plan downgrades | Enterprise→Pro at 12mo, Pro→Simple at 12mo | NOT modeled | Would require state transitions beyond MILP scope |
| Currency | CLP M$ (thousands of pesos) | USD at 900 | All values divided by 900 |
| VC | M$ 218,735 CLP → $243K | $243K | Direct conversion |
| Enterprise churn | 0% all years | 0% | Direct — highly sticky enterprise contracts |
| RRHH | Varies significantly yr1→yr3 | [6860, 25273, 37373] | Reflects hiring ramp (team grows significantly) |

**⚠ Key Gap:** Plan downgrades (Enterprise→Pro→Simple) represent revenue compression that our model cannot capture. This may cause the optimizer to overestimate Enterprise revenue in years 2-3. The ±20% tolerance should absorb this, but it's the weakest point of this instance.

**Validation Targets:** VAN ≈ 1,923 MUS$, EBITDA yr1 ≈ 440 MUS$, Revenue yr1 ≈ 828 MUS$

---

## 4. KavaComex (`kavacomex.yaml`) — PRIORITY 4 (most complex)

**Model:** Wine distribution (HORECA/Retail/Distribuidores) + Software licenses
**Complexity:** Very high — product-based logistics chain, channel-varying margins

| Parameter | Excel Value | YAML Value | Simplification |
|-----------|-------------|------------|----------------|
| Channels | 3 wine channels with different tickets ($12.5/$10.5/$9 per bottle) | Single blended service | Volume-weighted ARPU per client |
| Logistics | Full chain: Chile→Port→Container→Miami→FL/MA warehouses | Absorbed in c_u | $3.68/bottle logistics cost × volume per client |
| Products | Cases of 6 (A) and 12 (B), samples, pallets | Not modeled | Collapsed to bottle-equivalent volume |
| Stock management | Warehouse inventory, lead times, container scheduling | NOT modeled | Beyond MILP scope — future extension |
| Freelance sellers | 1 seller, grows to 2 at month 26 | Standard MILP | Model will optimize seller count endogenously |
| Quality bonuses | Performance-based bonus on top of 20% commission | NOT modeled | Approximated by higher com_v |

**⚠ Key Gap:** This is the highest-risk instance for convergence. The product-based business model with logistics costs, channel margins, and inventory dynamics is structurally different from the SaaS-oriented model. The ±20% tolerance may be insufficient. **Recommend running this case last and evaluating whether schema extensions are needed.**

**Validation Targets:** VAN ≈ 1,789 MUS$, Revenue yr1 ≈ 135 MUS$, Revenue yr3 ≈ 2,361 MUS$

---

## Schema Limitations Discovered

1. **Logistics costs not representable** — KavaComex has supply chain costs (shipping, warehousing, lead times) that don't fit the c_u/c_min/u_max structure designed for service delivery costs.

2. **Plan downgrades not capturable** — Beloop's Enterprise→Pro→Simple transitions would need state machine logic (Markov chain on plan transitions), not available in current MILP.

3. **Session-package bundling** — Entrena en Casa sells packages of 8/12/24 sessions with different pricing. The YAML's single ticket+frequency can't capture multi-tier pricing within a service.

4. **Product vs. client economics** — KavaComex prices per bottle, not per client. The conversion to per-client ARPU loses the unit-level margin detail that's relevant for logistics optimization.

5. **Variable commercial structures** — Freelance sellers (KavaComex), organic acquisition (GoDemos/Entrena), and plan-based pricing (Beloop) all get forced into the uniform meta/rem_v/com_v structure.

---

## Recommended Execution Order

```
1. godemos.yaml      → cleanest, should converge first
2. entrena-en-casa.yaml → negative EBITDA yr1, tests cash constraint handling
3. beloop.yaml       → SaaS with enterprise tier, tests multi-service
4. kavacomex.yaml    → highest risk, product-based, may need schema extension
```

For each: `uv run adventure-capital run --config configs/<file>.yaml --output outputs/<name>`
Then compare VAN, EBITDA trajectory, revenue, and breakeven against Excel targets.
