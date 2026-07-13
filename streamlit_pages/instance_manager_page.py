"""Gestor de Instancias — create, list, delete instances and trigger executions.

Landing page of the Streamlit UI. Users can:
- Upload a YAML file to pre-fill the form
- Fill the config form manually
- Create an instance (frozen config)
- Browse existing instances
- Trigger an execution for an instance
- Delete an instance
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import yaml
from adventure_capital.config import default_config, validate_config
from streamlit_pages import components as C


# --------------------------------------------------------------------------- #
# Form builders
# --------------------------------------------------------------------------- #


def _parse_float_list(st, text: str, label: str, fallback: list[float]) -> list[float]:
    """Parse a comma-separated list of numbers typed by the user.

    On a typo (e.g. ``0.5, 0,3``) show a business-readable error and keep the
    previous value instead of crashing the page with a traceback.
    """
    try:
        values = [float(x.strip()) for x in text.split(",") if x.strip()]
    except ValueError:
        st.error(f"**{label}**: hay un valor que no es número — revisa comas y puntos decimales. "
                 "Se mantiene el valor anterior.")
        return fallback
    return values or fallback


def _service_form(st, idx: int, service: dict) -> dict:
    st.markdown(f"**Servicio {idx + 1}**")
    c1, c2, c3 = st.columns(3)
    service["nombre"] = c1.text_input("Nombre", value=service["nombre"], key=f"svc_name_{idx}")
    service["ticket"] = c2.number_input(
        "Ticket (precio)", value=float(service["ticket"]), min_value=0.0, step=50.0, key=f"svc_ticket_{idx}"
    )
    service["frecuencia"] = c3.number_input(
        "Frecuencia (meses entre recompra)", value=int(service["frecuencia"]), min_value=1, step=1, key=f"svc_freq_{idx}"
    )
    horizon = int(st.session_state.get("f_H", 36) or 36)
    if service["frecuencia"] > horizon:
        st.warning(
            f"Frecuencia {service['frecuencia']} > horizonte {horizon} meses: **ningún cliente "
            f"recompra jamás** dentro del plan — el negocio se modela como venta única. "
            f"Si el servicio es recurrente (suscripción/consumible), la frecuencia real suele ser 1–3."
        )
    c4, c5, c6 = st.columns(3)
    service["alpha"] = c4.number_input(
        "Tasa de recompra (alpha)", value=float(service["alpha"]), min_value=0.0, max_value=1.0, step=0.05, key=f"svc_alpha_{idx}"
    )
    service["c_u"] = c5.number_input(
        "Costo unitario (c_u)", value=float(service["c_u"]), min_value=0.0, step=10.0, key=f"svc_cu_{idx}"
    )
    service["c_min"] = c6.number_input(
        "Costo op. mínimo (c_min)", value=float(service["c_min"]), min_value=0.0, step=100.0, key=f"svc_cmin_{idx}"
    )
    c7, c8 = st.columns(2)
    service["u_max"] = c7.number_input(
        "Capacidad por paso (u_max)", value=int(service["u_max"]), min_value=1, step=5, key=f"svc_umax_{idx}"
    )
    churn_txt = c8.text_input(
        "Churn anual por año (coma)",
        value=", ".join(str(x) for x in service["churn_anual"]),
        key=f"svc_churn_{idx}",
    )
    service["churn_anual"] = _parse_float_list(st, churn_txt, "Churn anual", service["churn_anual"])
    abase_txt = st.text_input(
        "A_base — adquisición fija 12 meses (coma)",
        value=", ".join(str(x) for x in service["A_base"]),
        key=f"svc_abase_{idx}",
        help="Exactamente 12 valores. Meses 1–12 del Plan Consensuado.",
    )
    service["A_base"] = _parse_float_list(st, abase_txt, "A_base", service["A_base"])
    if len(service["A_base"]) != 12:
        st.warning(f"A_base tiene {len(service['A_base'])} valores — deben ser exactamente 12 "
                   "(meses 1–12 del Plan Consensuado).")
    return service


def _channels_form(st, base: dict) -> dict:
    # If the user loaded a YAML with channel settings, use those as defaults
    # instead of the base config. This lets optional channels (advertising,
    # third_party) that are inactive in base.yaml appear checked when the
    # loaded YAML has them active.
    source = st.session_state.get("yaml_channels", base["channels"])
    channels = deepcopy(source)
    st.markdown("#### Canales comerciales")

    def _dv(key: str, fallback):
        return st.session_state.get("loaded_scalars", {}).get(key, fallback)

    sf = channels["salesforce"]
    sf["active"] = st.checkbox("Fuerza de ventas (salesforce)", value=sf["active"], key="ch_sf_active")
    if sf["active"]:
        cc1, cc2 = st.columns(2)
        sf["min_share"] = cc1.slider("Salesforce min_share", 0.0, 1.0, float(sf["min_share"]), 0.05, key="ch_sf_min")
        sf["max_share"] = cc2.slider("Salesforce max_share", 0.0, 1.0, float(sf["max_share"]), 0.05, key="ch_sf_max")

        st.markdown("**Estrategia comercial** — productividad y estructura del equipo de ventas")
        e1, e2, e3 = st.columns(3)
        e1.number_input("Clientes por vendedor/mes (meta)", value=float(_dv("meta", base["meta"])), min_value=0.1, step=0.5, key="f_meta")
        e2.number_input("Vendedores por líder (sup)", value=float(_dv("sup", base["sup"])), min_value=0.1, step=0.5, key="f_sup")
        e3.number_input("Lag productividad (meses)", value=int(_dv("commercial_productivity_lag", base["commercial_productivity_lag"])), min_value=0, step=1, key="f_lag",
                        help="Meses que tarda un vendedor nuevo en alcanzar la meta.")
        e4, e5, e6, e7 = st.columns(4)
        e4.number_input("Rem. vendedor (rem_v)", value=float(_dv("rem_v", base["rem_v"])), min_value=0.0, step=100.0, key="f_remv")
        e5.number_input("Rem. líder (rem_l)", value=float(_dv("rem_l", base["rem_l"])), min_value=0.0, step=100.0, key="f_reml")
        e6.number_input("Comisión vendedor (com_v)", value=float(_dv("com_v", base["com_v"])), min_value=0.0, max_value=1.0, step=0.01, key="f_comv")
        e7.number_input("Comisión líder (com_l)", value=float(_dv("com_l", base["com_l"])), min_value=0.0, max_value=1.0, step=0.01, key="f_coml")

    ad = channels["advertising"]
    ad["active"] = st.checkbox("Publicidad (advertising)", value=ad["active"], key="ch_ad_active")
    if ad["active"]:
        a1, a2 = st.columns(2)
        ad["I_min"] = a1.number_input("Inversión I_min", value=float(ad["I_min"]), min_value=0.0, step=500.0, key="ch_ad_imin")
        ad["I_max"] = a2.number_input("Inversión I_max", value=float(ad["I_max"]), min_value=0.0, step=500.0, key="ch_ad_imax")
        a4, a5 = st.columns(2)
        ad["A_min"] = a4.number_input("Recta A_min", value=float(ad["A_min"]), min_value=0.0, step=1.0, key="ch_ad_amin")
        ad["A_max"] = a5.number_input("Recta A_max", value=float(ad["A_max"]), min_value=0.0, step=1.0, key="ch_ad_amax")
        ad["A_ad_cap"] = max(float(ad.get("A_ad_cap") or 0), ad["A_max"])
        C.note(st, "Tope publicitario (A_ad_cap) = A_max automático, no se declara.")
        a6, a7 = st.columns(2)
        ad["min_share"] = a6.slider("Publicidad min_share", 0.0, 1.0, float(ad["min_share"]), 0.05, key="ch_ad_minshare")
        ad["max_share"] = a7.slider("Publicidad max_share", 0.0, 1.0, float(ad["max_share"]), 0.05, key="ch_ad_maxshare")
        C.note(st, "Publicidad = recta lineal A_ad = a + b·I_ad (continua, no escalonada).")

    tp = channels["third_party"]
    tp["active"] = st.checkbox("Canal de terceros (third_party)", value=tp["active"], key="ch_tp_active")
    if tp["active"]:
        t1, t2, t3 = st.columns(3)
        tp["commission"] = t1.number_input("Comisión", value=float(tp["commission"]), min_value=0.0, step=0.01, key="ch_tp_comm")
        tp["min_share"] = t2.slider("Terceros min_share", 0.0, 1.0, float(tp["min_share"]), 0.05, key="ch_tp_min")
        tp["max_share"] = t3.slider("Terceros max_share", 0.0, 1.0, float(tp["max_share"]), 0.05, key="ch_tp_max")
    return channels


def _build_config(st, base: dict) -> dict:
    # Start from the merged config (base + loaded YAML extra fields) so that
    # fields without dedicated form widgets (empresa, target_market,
    # working_capital, acquisition_ceiling, …) are preserved from the YAML.
    config = deepcopy(st.session_state.get("merged_config", base))

    # Override with session-state values from form widgets
    nombre = (st.session_state.get("f_nombre") or "").strip()
    if nombre:
        config["nombre"] = nombre
    config["H"] = int(st.session_state.get("f_H", config.get("H", base["H"])))
    config["VC"] = float(st.session_state.get("f_VC", config.get("VC", base["VC"])))
    config["beta"] = float(st.session_state.get("f_beta", config.get("beta", base["beta"])))
    config["g_max_suavizado"] = float(st.session_state.get("f_gmax", config.get("g_max_suavizado", base["g_max_suavizado"])))
    config["meta"] = float(st.session_state.get("f_meta", config.get("meta", base["meta"])))
    config["sup"] = float(st.session_state.get("f_sup", config.get("sup", base["sup"])))
    config["rem_v"] = float(st.session_state.get("f_remv", config.get("rem_v", base["rem_v"])))
    config["rem_l"] = float(st.session_state.get("f_reml", config.get("rem_l", base["rem_l"])))
    config["com_v"] = float(st.session_state.get("f_comv", config.get("com_v", base["com_v"])))
    config["com_l"] = float(st.session_state.get("f_coml", config.get("com_l", base["com_l"])))
    config["g_adm"] = float(st.session_state.get("f_gadm", config.get("g_adm", base["g_adm"])))
    config["tax"] = float(st.session_state.get("f_tax", config.get("tax", base["tax"])))
    config["RRHH_mensual"] = [float(x.strip()) for x in st.session_state.get("f_rrhh", "").split(",") if x.strip()]
    config["ciclo_op"] = [float(x.strip()) for x in st.session_state.get("f_ciclo", "").split(",") if x.strip()]
    config["commercial_productivity_lag"] = int(st.session_state.get("f_lag", config.get("commercial_productivity_lag", base["commercial_productivity_lag"])))
    config["servicios"] = deepcopy(st.session_state.get("services", config.get("servicios", base["servicios"])))
    config["channels"] = st.session_state.get("f_channels", config.get("channels", base["channels"]))
    config["liquidity_policy"] = {"type": st.session_state.get("f_liq", config.get("liquidity_policy", {}).get("type", "none"))}
    if st.session_state.get("f_liq") == "minimum_cash":
        config["liquidity_policy"]["value"] = float(st.session_state.get("f_liq_value", 0.0))
    config["solver"] = {"name": "cbc", "time_limit": int(st.session_state.get("f_time", config.get("solver", {}).get("time_limit", base["solver"]["time_limit"]))), "verbose": False}
    return config


def _seed_services(st, base: dict) -> None:
    if "services" not in st.session_state:
        st.session_state["services"] = deepcopy(base["servicios"])


# --------------------------------------------------------------------------- #
# Main render
# --------------------------------------------------------------------------- #


def render(st) -> None:
    C.page_header(
        st,
        "Gestor de instancias",
        "Crea una instancia (configuración congelada) y ejecuta el pipeline de valoración: "
        "instancia → ejecución → veredicto de due diligence → análisis de robustez → informe ejecutivo.",
    )

    base = default_config()
    _seed_services(st, base)

    # ── tabs for the page ─────────────────────────────────────────
    tab_new, tab_list = st.tabs(["Nueva instancia", "Instancias existentes"])

    # ──────────────────── TAB: Create ─────────────────────────────
    with tab_new:
        _render_create_tab(st, base)

    # ──────────────────── TAB: List ───────────────────────────────
    with tab_list:
        _render_list_tab(st)


# --------------------------------------------------------------------------- #
# YAML loader — directly populates widget session state
# --------------------------------------------------------------------------- #


def _apply_loaded_yaml(st, loaded: dict, base: dict) -> None:
    """Set every form widget's session_state value from a loaded YAML dict.

    This is the most reliable approach in Streamlit: widget keys (``f_H``,
    ``f_VC``, …) are set directly in ``st.session_state`` so they take effect
    on the next render without relying on the ``value=`` parameter or key
    deletion tricks.
    """
    # Scalar scalar_map: (session_state_key, yaml_key, cast_fn)
    scalar_map = [
        ("f_nombre", "nombre", str),
        ("f_H", "H", int),
        ("f_VC", "VC", float),
        ("f_beta", "beta", float),
        ("f_gmax", "g_max_suavizado", float),
        ("f_meta", "meta", float),
        ("f_sup", "sup", float),
        ("f_remv", "rem_v", float),
        ("f_reml", "rem_l", float),
        ("f_comv", "com_v", float),
        ("f_coml", "com_l", float),
        ("f_gadm", "g_adm", float),
        ("f_tax", "tax", float),
        ("f_lag", "commercial_productivity_lag", int),
    ]
    for ses_key, yaml_key, cast in scalar_map:
        if yaml_key in loaded:
            try:
                st.session_state[ses_key] = cast(loaded[yaml_key])
            except (TypeError, ValueError):
                pass  # skip invalid values

    # Comma-separated lists
    if "RRHH_mensual" in loaded:
        st.session_state["f_rrhh"] = ", ".join(str(x) for x in loaded["RRHH_mensual"])
    if "ciclo_op" in loaded:
        st.session_state["f_ciclo"] = ", ".join(str(x) for x in loaded["ciclo_op"])

    # Liquidity policy
    liq = loaded.get("liquidity_policy", {})
    if isinstance(liq, dict):
        liq_type = liq.get("type", "none")
        st.session_state["f_liq"] = liq_type
        if liq_type == "minimum_cash" and "value" in liq:
            st.session_state["f_liq_value"] = float(liq["value"])

    # Solver
    solver = loaded.get("solver", {})
    if isinstance(solver, dict) and "time_limit" in solver:
        st.session_state["f_time"] = int(solver["time_limit"])

    # Services (complex structure, not individual fields).
    # Drop stale per-widget keys (svc_*) so each service widget re-initialises
    # from value= against the freshly loaded list. Without this, Streamlit keeps
    # the previous widget state and the loaded services are silently dropped.
    st.session_state["services"] = loaded.get(
        "servicios", st.session_state.get("services", base["servicios"])
    )
    for k in [k for k in list(st.session_state) if k.startswith("svc_")]:
        del st.session_state[k]

    # Channels (checkboxes + nested sub-forms). Same fix: channel widgets are
    # keyed ch_*; drop them so value= from yaml_channels takes effect on rerun.
    if "channels" in loaded:
        st.session_state["yaml_channels"] = loaded["channels"]
        for k in [k for k in list(st.session_state) if k.startswith("ch_")]:
            del st.session_state[k]

    # Build and store the full merged config (base + loaded YAML extra fields).
    # This preserves fields that don't have form widgets (empresa, target_market,
    # working_capital, acquisition_ceiling, …) so _build_config can use them.
    merged = _deep_merge(deepcopy(base), loaded)
    # But SERVICES and CHANNELS are handled by their own form widgets, so we
    # respect those form values rather than the raw loaded YAML.
    merged["servicios"] = st.session_state.get("services", base["servicios"])
    if "channels" in loaded:
        merged["channels"] = loaded["channels"]
    st.session_state["merged_config"] = merged

    # Keep the raw dict for _dv() to read from (for any field not covered above)
    st.session_state["loaded_scalars"] = loaded


def _deep_merge(base: dict, overlay: dict) -> dict:
    """Recursively merge ``overlay`` into ``base``, returning a new dict.

    For keys that exist in both, nested dicts are merged recursively;
    non-dict values in ``overlay`` replace ``base`` values.
    """
    result = deepcopy(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


# --------------------------------------------------------------------------- #
# Create tab
# --------------------------------------------------------------------------- #


def _clear_yaml_state(st) -> None:
    """Forget everything a previously loaded YAML left in session state.

    Without this, the next instance silently inherits hidden fields
    (working_capital, acquisition_ceiling, empresa, …) from the last YAML.
    """
    for key in ("loaded_scalars", "merged_config", "yaml_channels",
                "yaml_applied_hash", "yaml_applied_name"):
        st.session_state.pop(key, None)


def _render_created_panel(st) -> None:
    """After creating an instance, offer the next step right here instead of
    making the user hunt for it in the 'Instancias existentes' tab."""
    created = st.session_state.get("created_instance")
    if not created:
        return
    st.success(f"Instancia **{created['name']}** creada (`{created['id']}`). ¿Qué sigue?")
    c1, c2, _ = st.columns([1, 1, 2])
    if c1.button("Ejecutar ahora", type="primary", key="created_run_now"):
        st.session_state.pop("created_instance", None)
        _trigger_execution(st, created["id"])
    if c2.button("Crear otra instancia", key="created_dismiss"):
        st.session_state.pop("created_instance", None)
        st.rerun()
    st.markdown("---")


def _render_create_tab(st, base: dict) -> None:
    _render_created_panel(st)

    # YAML upload — applies to the form automatically (one step, no extra click)
    uploaded = st.file_uploader(
        "Cargar YAML existente (opcional)",
        type=["yaml", "yml"],
        help="Al subir el archivo el formulario se completa automáticamente con sus valores.",
    )
    if uploaded is not None:
        import hashlib

        file_hash = hashlib.sha256(uploaded.getvalue()).hexdigest()
        if st.session_state.get("yaml_applied_hash") != file_hash:
            loaded = None
            try:
                loaded = yaml.safe_load(uploaded.getvalue().decode("utf-8"))
            except (yaml.YAMLError, UnicodeDecodeError) as exc:
                st.error(f"El archivo no es YAML válido y no se aplicó al formulario. Detalle: {exc}")
            if loaded is not None and not isinstance(loaded, dict):
                st.error("El YAML debe ser una configuración (pares clave: valor), "
                         f"no `{type(loaded).__name__}`. No se aplicó al formulario.")
                loaded = None
            if loaded:
                _apply_loaded_yaml(st, loaded, base)
                st.session_state["yaml_applied_hash"] = file_hash
                st.session_state["yaml_applied_name"] = uploaded.name
                st.rerun()
        elif st.session_state.get("yaml_applied_name"):
            st.success(f"Formulario completado desde **{st.session_state['yaml_applied_name']}**. "
                       "Revisa los valores y pulsa *Crear instancia*.")

    def _dv(key: str, fallback: Any) -> Any:
        scalars = st.session_state.get("loaded_scalars", {})
        return scalars.get(key, fallback)

    # ══ Nivel 1 · Caso ══
    # Las perillas que definen el caso de inversión. Siempre visibles.
    st.markdown("#### Caso")
    st.text_input("Nombre de la instancia", value=_dv("nombre", ""),
                  key="f_nombre", placeholder="Ej: Caso base Q3")
    g1, g2, g3, g4 = st.columns(4)
    g1.number_input("Horizonte (meses)", value=int(_dv("H", base["H"])), min_value=14, step=1, key="f_H",
                    help="Meses del plan; mínimo 14 (el horizonte optimizado parte en el mes 13).")
    g2.number_input("Capital disponible (VC)", value=float(_dv("VC", base["VC"])), min_value=0.0, step=10000.0, key="f_VC",
                    help="USD efectivamente comprometidos por el inversionista.")
    g3.number_input("Tasa de descuento anual (beta)", value=float(_dv("beta", base["beta"])), min_value=0.0, max_value=2.0, step=0.01, key="f_beta",
                    help="0.35 = 35% anual.")
    g4.number_input("Impuesto (tax)", value=float(_dv("tax", base["tax"])), min_value=0.0, max_value=1.0, step=0.005, key="f_tax",
                    help="Tasa efectiva sobre EBITDA positivo. 0.125 = 12,5%.")

    # ══ Nivel 2 · Negocio ══
    # Lo que Alejandro movería: servicios y canales.
    st.markdown("#### Negocio — Servicios")
    sc1, sc2 = st.columns(2)
    default_service = deepcopy(base["servicios"][0])
    if sc1.button("Agregar servicio"):
        st.session_state["services"].append(deepcopy(default_service))
    if sc2.button("Quitar último") and len(st.session_state.get("services", [])) > 1:
        st.session_state["services"].pop()

    updated = []
    for idx, service in enumerate(st.session_state.get("services", [])):
        with st.expander(f"{service['nombre']}", expanded=(idx == 0)):
            updated.append(_service_form(st, idx, deepcopy(service)))
    st.session_state["services"] = updated

    st.session_state["f_channels"] = _channels_form(st, base)

    # ══ Nivel 3 · Supuestos técnicos ══
    # Colapsados: casi nunca se tocan; defaults a la vista al expandir.
    # (La estrategia comercial vive bajo el toggle de Fuerza de ventas.)
    with st.expander("Supuestos técnicos (costos fijos, liquidez, solver)", expanded=False):
        st.markdown("**Costos fijos y operación**")
        f1, f2 = st.columns(2)
        f1.number_input("Gasto administrativo mensual (g_adm)", value=float(_dv("g_adm", base["g_adm"])), min_value=0.0, step=250.0, key="f_gadm")
        f2.number_input("Suavizado máx. de crecimiento (g_max_suavizado)", value=float(_dv("g_max_suavizado", base["g_max_suavizado"])), min_value=0.0, max_value=1.0, step=0.05, key="f_gmax",
                        help="Límite de variación mensual del plan. 0.25 = 25%.")
        st.text_input("RRHH mensual por año (coma)", value=", ".join(str(x) for x in _dv("RRHH_mensual", base["RRHH_mensual"])), key="f_rrhh",
                      help="Un valor por año del horizonte, USD/mes.")
        st.text_input("Ciclo operacional por año (coma)", value=", ".join(str(x) for x in _dv("ciclo_op", base["ciclo_op"])), key="f_ciclo",
                      help="Días de ciclo caja por año del horizonte.")

        st.markdown("**Liquidez y solver**")
        l1, l2, l3 = st.columns(3)
        l1.selectbox("Política de liquidez", ["none", "nonnegative", "minimum_cash"], key="f_liq")
        if st.session_state.get("f_liq") == "minimum_cash":
            l2.number_input("Caja mínima", value=0.0, step=1000.0, key="f_liq_value")
        l3.number_input("Solver time_limit (s)", value=int(base["solver"]["time_limit"]), min_value=10, step=10, key="f_time")

    C.note(st, "El análisis de robustez (M4) se decide en la página Due diligence tras el veredicto "
               "(automático si aprueba limpio; con confirmación si hay advertencias).")

    # ── Create button ──
    st.markdown("---")
    c1, c2 = st.columns([1, 3])
    with c1:
        if st.button("Crear instancia", type="primary"):
            try:
                config = _build_config(st, base)
                validate_config(config)
            except Exception as exc:
                st.error(f"Configuración inválida: {exc}")
                return

            # Duplicate guard: warn once if an identical frozen config exists
            # (this is how ten copies of the same case got created by repeated
            # clicks). A second click creates it anyway.
            import hashlib

            config_hash = hashlib.sha256(
                yaml.safe_dump(config, allow_unicode=True, sort_keys=True).encode("utf-8")
            ).hexdigest()[:8]
            dup = next((m for m in C.list_instances() if m.get("config_hash") == config_hash), None)
            if dup and st.session_state.get("allow_duplicate_hash") != config_hash:
                st.session_state["allow_duplicate_hash"] = config_hash
                st.warning(
                    f"Ya existe una instancia con esta misma configuración: **{dup['name']}** "
                    f"(`{dup['id']}`). Ejecútala desde *Instancias existentes*, o pulsa "
                    f"**Crear instancia** de nuevo para crear una copia de todos modos."
                )
                return

            meta = C.create_instance(config, name=config.get("nombre", None))
            st.session_state["created_instance"] = meta
            st.session_state["last_instance_id"] = meta["id"]
            st.session_state.pop("allow_duplicate_hash", None)
            _clear_yaml_state(st)
            st.rerun()

    # ── Preview ──
    with c2:
        if st.button("Vista previa YAML"):
            try:
                config = _build_config(st, base)
                preview = yaml.safe_dump(config, allow_unicode=True, sort_keys=False)
                st.code(preview, language="yaml")
            except Exception:
                st.warning("Completa la configuración primero.")


# --------------------------------------------------------------------------- #
# List tab
# --------------------------------------------------------------------------- #


def _render_list_tab(st) -> None:
    instances = C.list_instances()

    if not instances:
        st.info("No hay instancias aún. Crea una desde la pestaña **Nueva instancia**.")
        return

    for meta in instances:
        with st.container():
            cols = st.columns([3, 1, 1, 1])
            with cols[0]:
                st.markdown(f"**{meta['name']}**")
                st.caption(f"ID: `{meta['id']}` · Creada: {meta['created_at']}")
            with cols[1]:
                if st.button("Ejecutar", key=f"run_{meta['id']}"):
                    _trigger_execution(st, meta["id"], run_stochastic=True)
            with cols[2]:
                if st.button("Detalle", key=f"detail_{meta['id']}"):
                    _show_instance_detail(st, meta["id"])
            with cols[3]:
                if st.button("Eliminar", key=f"del_{meta['id']}"):
                    C.delete_instance(meta["id"])
                    st.rerun()
            st.markdown("---")


def _trigger_execution(st, instance_id: str, run_stochastic: bool = True) -> None:
    """Phase 1: run M1–M3 (deterministic plan + valuation + due diligence) only.

    M4 (stochastic) is gated behind the DD verdict; after phase 1 the UI
    navigates to the Due diligence page, where the gate lives (P0-3 de la
    auditoría UX: el veredicto se decide en el contexto del run, no sobre el
    formulario de creación).
    """
    from adventure_capital.workflow_registry import run_execution as _run_exec

    with st.spinner("Ejecutando plan determinista, valoración y due diligence…"):
        try:
            record = _run_exec(instance_id, run_stochastic=False)
            st.session_state["current_run_id"] = record["id"]
            st.session_state["m4_gate_run_id"] = record["id"]
            st.session_state["current_page"] = C.PAGE_DD
            st.rerun()
        except Exception as exc:
            st.error(f"La ejecución falló: {exc}. Revisa la configuración de la instancia e intenta de nuevo.")
            import traceback
            with st.expander("Detalle técnico"):
                st.code(traceback.format_exc())


def _show_instance_detail(st, instance_id: str) -> None:
    config = C.load_instance_config(instance_id)
    if config:
        st.code(yaml.safe_dump(config, allow_unicode=True, sort_keys=False), language="yaml")
    else:
        st.warning("No se pudo cargar la configuración.")
