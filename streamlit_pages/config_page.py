"""Configuración: form builder -> YAML config -> run pipeline.

This is the ONLY page allowed to call run_pipeline. It builds a config dict with
the exact shape of config._DEFAULT_CONFIG, validates it, runs the existing
pipeline, and stores the output directory in session_state for the result pages.
"""

from __future__ import annotations

import tempfile
from copy import deepcopy
from pathlib import Path

import yaml

from adventure_capital.config import default_config, validate_config
from streamlit_pages import components as C


def _seed_services(st, base: dict) -> None:
    if "services" not in st.session_state:
        st.session_state["services"] = deepcopy(base["servicios"])


def _service_form(st, idx: int, service: dict) -> dict:
    st.markdown(f"**Servicio {idx + 1}**")
    c1, c2, c3 = st.columns(3)
    service["nombre"] = c1.text_input("Nombre", value=service["nombre"], key=f"svc_name_{idx}")
    service["ticket"] = c2.number_input("Ticket (precio)", value=float(service["ticket"]), min_value=0.0, step=50.0, key=f"svc_ticket_{idx}")
    service["frecuencia"] = c3.number_input("Frecuencia (meses entre recompra)", value=int(service["frecuencia"]), min_value=1, step=1, key=f"svc_freq_{idx}")

    c4, c5, c6 = st.columns(3)
    service["alpha"] = c4.number_input("Tasa de recompra (alpha)", value=float(service["alpha"]), min_value=0.0, max_value=1.0, step=0.05, key=f"svc_alpha_{idx}")
    service["c_u"] = c5.number_input("Costo unitario (c_u)", value=float(service["c_u"]), min_value=0.0, step=10.0, key=f"svc_cu_{idx}")
    service["c_min"] = c6.number_input("Costo op. mínimo (c_min)", value=float(service["c_min"]), min_value=0.0, step=100.0, key=f"svc_cmin_{idx}")

    c7, c8 = st.columns(2)
    service["u_max"] = c7.number_input("Capacidad por paso (u_max)", value=int(service["u_max"]), min_value=1, step=5, key=f"svc_umax_{idx}")
    churn_txt = c8.text_input(
        "Churn anual por año (coma)", value=", ".join(str(x) for x in service["churn_anual"]), key=f"svc_churn_{idx}"
    )
    service["churn_anual"] = [float(x.strip()) for x in churn_txt.split(",") if x.strip()]

    abase_txt = st.text_input(
        "A_base — adquisición fija 12 meses (coma)",
        value=", ".join(str(x) for x in service["A_base"]),
        key=f"svc_abase_{idx}",
        help="Exactamente 12 valores. Año 1 inmutable.",
    )
    service["A_base"] = [float(x.strip()) for x in abase_txt.split(",") if x.strip()]
    return service


def _channels_form(st, base: dict) -> dict:
    channels = deepcopy(base["channels"])
    st.markdown("#### Canales comerciales")

    sf = channels["salesforce"]
    sf["active"] = st.checkbox("Fuerza de ventas (salesforce)", value=sf["active"])
    if sf["active"]:
        cc1, cc2 = st.columns(2)
        sf["min_share"] = cc1.slider("Salesforce min_share", 0.0, 1.0, float(sf["min_share"]), 0.05)
        sf["max_share"] = cc2.slider("Salesforce max_share", 0.0, 1.0, float(sf["max_share"]), 0.05)

    ad = channels["advertising"]
    ad["active"] = st.checkbox("Publicidad (advertising)", value=ad["active"])
    if ad["active"]:
        a1, a2, a3 = st.columns(3)
        ad["I_min"] = a1.number_input("Inversión I_min", value=float(ad["I_min"]), min_value=0.0, step=500.0)
        ad["I_max"] = a2.number_input("Inversión I_max", value=float(ad["I_max"]), min_value=0.0, step=500.0)
        ad["A_ad_cap"] = a3.number_input("Tope adquisición A_ad_cap", value=float(ad["A_ad_cap"]), min_value=0.0, step=5.0)
        a4, a5 = st.columns(2)
        ad["A_min"] = a4.number_input("Recta A_min", value=float(ad["A_min"]), min_value=0.0, step=1.0)
        ad["A_max"] = a5.number_input("Recta A_max", value=float(ad["A_max"]), min_value=0.0, step=1.0)
        a6, a7 = st.columns(2)
        ad["min_share"] = a6.slider("Publicidad min_share", 0.0, 1.0, float(ad["min_share"]), 0.05)
        ad["max_share"] = a7.slider("Publicidad max_share", 0.0, 1.0, float(ad["max_share"]), 0.05)
        C.note(st, "Publicidad = recta lineal A_ad = a + b·I_ad (continua, no escalonada).")

    tp = channels["third_party"]
    tp["active"] = st.checkbox("Canal de terceros (third_party)", value=tp["active"])
    if tp["active"]:
        t1, t2, t3 = st.columns(3)
        tp["commission"] = t1.number_input("Comisión", value=float(tp["commission"]), min_value=0.0, step=0.01)
        tp["min_share"] = t2.slider("Terceros min_share", 0.0, 1.0, float(tp["min_share"]), 0.05)
        tp["max_share"] = t3.slider("Terceros max_share", 0.0, 1.0, float(tp["max_share"]), 0.05)

    return channels


def _build_config(st) -> dict:
    base = default_config()
    config = deepcopy(base)

    config["H"] = int(st.session_state["f_H"])
    config["VC"] = float(st.session_state["f_VC"])
    config["beta"] = float(st.session_state["f_beta"])
    config["g_max_suavizado"] = float(st.session_state["f_gmax"])
    config["meta"] = float(st.session_state["f_meta"])
    config["sup"] = float(st.session_state["f_sup"])
    config["rem_v"] = float(st.session_state["f_remv"])
    config["rem_l"] = float(st.session_state["f_reml"])
    config["com_v"] = float(st.session_state["f_comv"])
    config["com_l"] = float(st.session_state["f_coml"])
    config["g_adm"] = float(st.session_state["f_gadm"])
    config["tax"] = float(st.session_state["f_tax"])
    config["RRHH_mensual"] = [float(x.strip()) for x in st.session_state["f_rrhh"].split(",") if x.strip()]
    config["ciclo_op"] = [float(x.strip()) for x in st.session_state["f_ciclo"].split(",") if x.strip()]
    config["commercial_productivity_lag"] = int(st.session_state["f_lag"])
    config["servicios"] = deepcopy(st.session_state["services"])
    config["channels"] = st.session_state["f_channels"]
    config["liquidity_policy"] = {"type": st.session_state["f_liq"]}
    if st.session_state["f_liq"] == "minimum_cash":
        config["liquidity_policy"]["value"] = float(st.session_state["f_liq_value"])
    config["solver"] = {"name": "cbc", "time_limit": int(st.session_state["f_time"]), "verbose": False}
    return config


def render(st) -> None:
    st.title("Configuración del caso")
    st.caption("Configura la startup, genera el YAML y ejecuta el pipeline. Las páginas de resultados leen los artefactos generados.")
    base = default_config()
    _seed_services(st, base)

    # --- optional YAML upload --------------------------------------------
    uploaded = st.file_uploader("Cargar YAML existente (opcional)", type=["yaml", "yml"])
    if uploaded is not None and st.button("Aplicar YAML cargado"):
        loaded = yaml.safe_load(uploaded.getvalue().decode("utf-8")) or {}
        st.session_state["services"] = loaded.get("servicios", st.session_state["services"])
        st.session_state["loaded_scalars"] = loaded
        st.success("YAML cargado. Revisa y ajusta los campos abajo.")

    loaded = st.session_state.get("loaded_scalars", {})

    def _dv(key, default):
        return loaded.get(key, default)

    st.markdown("#### Parámetros generales")
    g1, g2, g3 = st.columns(3)
    g1.number_input("Horizonte H (meses, ≥14)", value=int(_dv("H", base["H"])), min_value=14, step=1, key="f_H")
    g2.number_input("Capital inicial VC", value=float(_dv("VC", base["VC"])), min_value=0.0, step=10000.0, key="f_VC")
    g3.number_input("Tasa de descuento anual (beta)", value=float(_dv("beta", base["beta"])), min_value=0.0, max_value=2.0, step=0.01, key="f_beta")
    g4, g5, g6 = st.columns(3)
    g4.number_input("Impuesto (tax)", value=float(_dv("tax", base["tax"])), min_value=0.0, max_value=1.0, step=0.005, key="f_tax")
    g5.number_input("Gasto administrativo (g_adm)", value=float(_dv("g_adm", base["g_adm"])), min_value=0.0, step=250.0, key="f_gadm")
    g6.number_input("Suavizado máx. (g_max_suavizado)", value=float(_dv("g_max_suavizado", base["g_max_suavizado"])), min_value=0.0, max_value=1.0, step=0.05, key="f_gmax")

    st.markdown("#### Equipo comercial")
    e1, e2, e3 = st.columns(3)
    e1.number_input("Meta productividad (meta)", value=float(_dv("meta", base["meta"])), min_value=0.1, step=0.5, key="f_meta")
    e2.number_input("Supervisión (sup)", value=float(_dv("sup", base["sup"])), min_value=0.1, step=0.5, key="f_sup")
    e3.number_input("Lag productividad (meses)", value=int(_dv("commercial_productivity_lag", base["commercial_productivity_lag"])), min_value=0, step=1, key="f_lag")
    e4, e5, e6, e7 = st.columns(4)
    e4.number_input("Remuneración vendedor (rem_v)", value=float(_dv("rem_v", base["rem_v"])), min_value=0.0, step=100.0, key="f_remv")
    e5.number_input("Remuneración líder (rem_l)", value=float(_dv("rem_l", base["rem_l"])), min_value=0.0, step=100.0, key="f_reml")
    e6.number_input("Comisión vendedor (com_v)", value=float(_dv("com_v", base["com_v"])), min_value=0.0, max_value=1.0, step=0.01, key="f_comv")
    e7.number_input("Comisión líder (com_l)", value=float(_dv("com_l", base["com_l"])), min_value=0.0, max_value=1.0, step=0.01, key="f_coml")

    st.text_input("RRHH mensual por año (coma)", value=", ".join(str(x) for x in _dv("RRHH_mensual", base["RRHH_mensual"])), key="f_rrhh")
    st.text_input("Ciclo operacional por año (coma)", value=", ".join(str(x) for x in _dv("ciclo_op", base["ciclo_op"])), key="f_ciclo")

    # --- services (dynamic) ----------------------------------------------
    st.markdown("#### Servicios")
    sc1, sc2 = st.columns(2)
    if sc1.button("➕ Agregar servicio"):
        st.session_state["services"].append(deepcopy(base["servicios"][0]))
    if sc2.button("➖ Quitar último") and len(st.session_state["services"]) > 1:
        st.session_state["services"].pop()

    updated = []
    for idx, service in enumerate(st.session_state["services"]):
        with st.expander(f"{service['nombre']}", expanded=(idx == 0)):
            updated.append(_service_form(st, idx, deepcopy(service)))
    st.session_state["services"] = updated

    # --- channels + liquidity --------------------------------------------
    st.session_state["f_channels"] = _channels_form(st, base)

    st.markdown("#### Liquidez y solver")
    l1, l2, l3 = st.columns(3)
    l1.selectbox("Política de liquidez", ["none", "nonnegative", "minimum_cash"], key="f_liq")
    if st.session_state.get("f_liq") == "minimum_cash":
        l2.number_input("Caja mínima", value=0.0, step=1000.0, key="f_liq_value")
    l3.number_input("Solver time_limit (s)", value=int(base["solver"]["time_limit"]), min_value=10, step=10, key="f_time")

    full = st.checkbox("Análisis completo (Due Diligence + estocástico)", value=True,
                       help="Si está desactivado, solo corre el plan determinista (más rápido).")

    # --- run -------------------------------------------------------------
    st.markdown("---")
    if st.button("Generar YAML y ejecutar pipeline", type="primary"):
        try:
            config = _build_config(st)
            validate_config(config)
        except Exception as exc:  # noqa: BLE001 - surfaced to user
            st.error(f"Configuración inválida: {exc}")
            return

        out_dir = Path(tempfile.mkdtemp(prefix="ac_run_"))
        st.session_state["yaml_preview"] = yaml.safe_dump(config, allow_unicode=True, sort_keys=False)
        with st.spinner("Ejecutando pipeline… (puede tardar según el horizonte y el solver)"):
            try:
                from adventure_capital.pipeline import run_pipeline
                run_pipeline(config, output_dir=str(out_dir), baseline_only=not full)
            except Exception as exc:  # noqa: BLE001 - surfaced to user
                st.error(f"El pipeline falló: {exc}")
                st.session_state["output_dir"] = str(out_dir)  # still allow browsing partial artifacts
                return
        st.session_state["output_dir"] = str(out_dir)
        st.success(f"Pipeline ejecutado. Artefactos en: {out_dir}")
        st.info("Revisa las páginas de resultados en la barra lateral.")

    if st.session_state.get("yaml_preview"):
        with st.expander("YAML generado"):
            st.code(st.session_state["yaml_preview"], language="yaml")
