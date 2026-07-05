# HANDOFF — núcleo de crecimiento (para el próximo agente)

Fecha: 2026-07-05 (cierre de sesión) · Branch: `growth-law-adr14` (worktree aislado)
· `entrega-tesis` = fallback intacto, NO tocar · Defensa: lunes 6-jul 8:15.
Decisión vigente: **corrección de Alonso de esta fecha — la fricción de contratación
NO es core**. Este documento reemplaza cualquier recomendación anterior que la
presentara como mecanismo principal (growth_dynamics_final.md, implementation_plan
REV 2 §1, unbounded_path_diagnosis §0 quedan SUPERSEDIDOS en ese punto).

## 1. Metodología core (decisión conceptual de Alonso)

**`growth_commitment` (piso de tesis VC) + `aggregate_acquisition_envelope`
(envolvente agregada de adquisición).** Todo proyectado se ancla en el plan
consensuado de 12 meses. Si el plan consensuado no soporta los benchmarks VC, el
modelo NO está malo: las métricas del emprendedor no alcanzan y deben recalibrarse.
**Diagnóstico de negocio, no falla del solver.**

PROHIBIDO el framing "ceiling/techo arbitrario". Nomenclatura correcta:
*aggregate acquisition envelope / planning envelope / growth plausibility envelope /
máxima trayectoria de adquisición derivada del plan consensuado*. (Honestidad
técnica para ti, próximo agente: matemáticamente sigue siendo una cota superior;
la diferencia REAL y defendible es la derivación — anclada al plan del cliente y
al benchmark VC, no a un múltiplo de mercado M exógeno — y que viene emparejada
con un piso. No vendas la diferencia como matemática; véndela como trazabilidad.)

## 2. Arquitectura conceptual requerida

```text
(1) Meses 1-12:   A_t fija/anclada al plan consensuado (A_base). [YA ES ASÍ]
(2) Meses 13-36:  A_total_t optimizada, acotada por la envolvente:
(3)               Σ_s A[s,t] ≤ U_t
(4) U_t derivada de (fuentes, en jerarquía):
      U_plan_t = Ā12 · (1+g_mom)^(t−12)         g_mom = MoM del plan consensuado
      U_vc_t   = adquisición requerida por la senda mínima VC dado churn:
                 A_req_t = B_t − B_{t−1}·(1−churn_m_t)   con B_t = C12·3^((t−12)/24)
      U_t      = max(U_plan_t, U_vc_t) · (1 + δ_t)
      δ_t      = holgura CRECIENTE (honra upside startup), declarada:
                 p.ej. δ = 0.25 año 2, 0.50 año 3 — SUPUESTO DE TESIS marcado,
                 o derivada (traction/escenario) en versión futura
      custom   = override de Alejandro con justificación obligatoria (W4)
(5) Piso VC (YA IMPLEMENTADO): C24 ≥ √3·C12, C36 ≥ 3·C12.
(6) Conflicto envolvente vs piso ⇒ Infeasible ⇒ diagnóstico estructurado de
    negocio (rutina R1-R8 YA implementada; extender el mapeo a las 6 lecturas:
    plan no soporta tesis VC / ritmo de adquisición insuficiente / unit economics
    insuficientes / carga de costo fijo / caja-runway / estructura CAC-canales).
```

### Propuesta de config (implementar)

```yaml
acquisition_envelope:
  enabled: false            # opt-in hasta decisión de default
  source: max_plan_vc       # plan_mom | vc_minimum | max_plan_vc | custom
  slack_year2: 0.25         # supuesto de tesis declarado
  slack_year3: 0.50
  custom_path: null         # lista mensual opcional (override Alejandro)
  custom_justification: null
```

Precomputar U_t en `instance.py` (constantes → restricciones lineales, MILP
intacto; patrón idéntico a checkpoint_targets). Paridad estocástica: U_t sobre el
plan de primera etapa (mismo criterio piso-planeado ya decidido).

## 3. Qué se intentó y por qué se corrige

Cronología (evidencia en docs/analysis/): media móvil (diverge) → ceiling log ×M
(ADR 0010; M = driver del valor, objeción válida) → convex-CAC (ADR 0013; no
funciona para demo) → **fricción de contratación como freno endógeno** (E4 +
band experiment + benchmarks destino: Optimal en las 4, VAN 0.6-27M).

**Por qué fricción-como-core estaba mal:** (a) Alonso lo había excluido
explícitamente como mecanismo principal de acotamiento; (b) empíricamente el VAN
escala ~lineal en h ⇒ h se convierte en EL driver del valor — la misma objeción
que mató al M del ceiling, con otro nombre; (c) desancla la proyección del plan
consensuado (25-50 vendedores en año 3 sobre planes de 1-2 vendedores: plausible
operacionalmente discutible, indefendible como compromiso ante el comité).
**Queda como feature opcional experimental/de sensibilidad** (ya opt-in,
default-off — no requiere revert), etiquetada NO-core.

**Por qué la envolvente es la dirección correcta:** ancla al plan consensuado
(fuente = el cliente), incorpora el benchmark VC (fuente = tesis de inversión),
holgura declarada honra el upside sin dejar el valor en manos de un parámetro
libre, y su violación produce el diagnóstico de negocio que Alejandro quiere
mostrar a inversionistas.

## 4. Estado del branch `growth-law-adr14` (commits e6e7c6e → c9a3509)

**Suite: 172 passed, 3 skipped.** Archivos tocados vs entrega-tesis (`38f9da3`):
`config.py`, `instance.py`, `model.py`, `reporting.py`, `due_diligence/rules.py`,
`due_diligence/workflow.py`, `stochastic/{model,evaluate}.py`,
`scripts/{diagnose_infeasibility,growth_commitment_benchmarks,unbounded_path_matrix}.py`,
`tests/test_growth_commitment.py` (11 tests), ADR 0014, y docs/analysis/
(growth_commitment_benchmarks, final_growth_decision, unbounded_path_diagnosis,
WORKLOG).

### KEEP (alineado con el nuevo core)
- `growth_commitment` completo (piso ×3, checkpoints, sugerencias g, W1-W5
  cableados a DD, paridad estocástica piso-planeado, tests). ES la mitad del core.
- Rutina diagnóstico R1-R8 (`scripts/diagnose_infeasibility.py`) — pieza (6).
- `growth_suggestions.json` (MoM adquisición + MoM stock) — insumo de U_t.
- Tests y no-op guarantees.

### RE-ETIQUETAR (no borrar código)
- `hiring` → docstrings/ADR 0014/docs: "optional sensitivity/experimental feature,
  NOT the core methodology". Ya es opt-in default-off; solo cambia el relato.
- ADR 0014: añadir sección de enmienda (core = commitment + envelope; hiring
  experimental) + sección rollback (gap 3 pendiente del review).

### DEPRECAR EN DOCS (marcar supersedido, no borrar)
- Recomendación "fricción como default" en `growth_dynamics_final.md`,
  `implementation_plan_growth_law.md` REV 2 §1 y `unbounded_path_diagnosis.md` §0
  (la EVIDENCIA sigue válida; la RECOMENDACIÓN cambia).
- Todo uso de "ceiling" como framing del mecanismo nuevo.

### IMPLEMENTAR (próximos pasos exactos, en orden)
1. `acquisition_envelope` en config.py (schema §2 + validaciones + Σ compat piso:
   si U_t hace inalcanzable B_t ⇒ error temprano con mensaje de diagnóstico).
2. `instance.py`: precomputar U_t (U_plan, U_vc con churn del año corriente, max,
   slack schedule); exportar a growth_suggestions.json.
3. `model.py`: `Σ_s A[s,t] ≤ U_t` (t≥13) — bloque aditivo opt-in.
4. `stochastic/model.py`: mismo U_t sobre plan_total primera etapa.
5. Third-party (decisión 7): NO sobre-modelar. Validación MVP: si
   `third_party.active` ⇒ exigir clave de capacidad explícita (`A_tp_cap`) o
   error claro; default inactivo. Cierra el agujero unbounded documentado
   (unbounded_path_diagnosis §5-6) sin modelarlo más.
6. Tests: envelope respeta U_t; envelope+piso conflicto ⇒ Infeasible + diagnóstico
   con las 6 lecturas; no-op off; paridad; tp sin capacidad ⇒ error validación.
7. Benchmarks 4 instancias con core nuevo (commitment + envelope) + tabla deltas.
8. Actualizar final_growth_decision.md → re-veredicto.

### Antes de mergear con UI (NO ahora)
Re-veredicto PASS + firma Alonso en final_growth_decision.md + rebaseline según
criterios (plan §8: deltas explicados, paridad, artefactos, gate humano) + flip
de defaults como commit separado. **NO merge, NO UI, NO rebaseline en esta fase.**

## 5. Rollback

- Feature-level: `acquisition_envelope.enabled: false` + `growth_commitment.enabled:
  false` + `hiring.enabled: false` ⇒ no-op total (garantía ya testeada para las 2
  existentes; exigirla para envelope).
- Branch-level: abandonar `growth-law-adr14`; `entrega-tesis` (HEAD `dd0cc08`) es
  el fallback estable con suite verde (161) y demo funcional.

## 6. Narrativa de defensa (lunes)

1. Problema: crecimiento startup dentro de un MILP — sin cota, el problema es
   no acotado (probado); la pregunta correcta es QUÉ cota tiene significado.
2. Respuesta metodológica: **todo se ancla al plan consensuado** — piso = tesis de
   inversión VC (×3 en 3 años, checkpoints anuales) y envolvente = máxima
   trayectoria plausible derivada del propio plan + benchmark + holgura declarada.
3. Si no cabe: el sistema NO fuerza el resultado — entrega diagnóstico de negocio
   (qué palanca: ritmo comercial, unit economics, costo fijo, caja, canales).
   "Plan auditable + punto de equilibrio + diagnóstico" = exactamente lo que los
   VC exigen hoy (Maureira).
4. Evidencia de rigor: alternativas evaluadas y descartadas con datos (media
   móvil, ceiling×M, convex-CAC, fricción-como-core), suite 172 tests, paridad
   determinista/estocástico, opt-in con no-op garantizado.
5. Demo corre sobre `entrega-tesis` (estable); el core nuevo se muestra como
   resultado de investigación implementado en branch.

## 7. Estado de sesión al cierre

- `entrega-tesis`: HEAD `dd0cc08`, 161 tests, demo estable. INTACTO.
- `growth-law-adr14`: HEAD `c9a3509`, 172 tests, commitment+W1-W5+diagnóstico
  listos; hiring implementado pero re-etiquetado experimental; envelope PENDIENTE
  (pasos §4). Veredicto de supervisión: PARTIAL (gaps 1-2 cerrados; queda rollback
  en ADR + este cambio de core).
- Sesión UI (`ui-pro`) corre aparte — no mezclar hasta cerrar el core.
