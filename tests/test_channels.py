"""Phase 2 — acquisition channel split, advertising recta, share bounds."""

import pytest

from adventure_capital.config import default_config, validate_config
from adventure_capital.config import load_config
from adventure_capital.instance import generate_instance
from adventure_capital.model import solve_growth_plan
from adventure_capital.results import extract_results

CHANNEL_COLS = [
    "A_salesforce",
    "A_advertising",
    "A_third_party",
    "advertising_cac_cost",
    "share_salesforce",
]


def _solve(path):
    config = load_config(path)
    instance = generate_instance(config)
    solution = solve_growth_plan(instance)
    df = extract_results(instance, solution)
    return config, instance, solution, df


def test_legacy_no_channels_regression():
    """A config without a channels block keeps salesforce-only behavior, no channel columns."""
    config, instance, solution, df = _solve("configs/demo-complex.yaml")
    assert solution["status"] == "Optimal"
    assert instance["channels"]["any_split"] is False
    for col in CHANNEL_COLS:
        assert col not in df.columns
    # Year 1 acquisition still fixed from A_base.
    for s, service in enumerate(instance["servicios"]):
        name = service["nombre"]
        for t in range(1, 13):
            assert df.loc[df["t"] == t, f"A_{name}"].iloc[0] == pytest.approx(
                instance["A_base"][(s, t)]
            )


def test_advertising_only_solves():
    config, instance, solution, df = _solve("configs/demo-advertising-only.yaml")
    assert solution["status"] == "Optimal"
    assert (df["A_advertising"] > 0).any()
    assert (df["A_salesforce"].abs() < 1e-6).all()
    assert (abs(df["advertising_cac_cost"] - df["advertising_investment"]) < 1e-6).all()


def test_advertising_recta_identity():
    config, instance, solution, df = _solve("configs/demo-advertising-only.yaml")
    a = instance["channels"]["advertising"]["a"]
    b = instance["channels"]["advertising"]["b"]
    for _, row in df.iterrows():
        assert row["A_advertising"] == pytest.approx(a + b * row["advertising_investment"], abs=1e-4)


def test_advertising_respects_saturation():
    config, instance, solution, df = _solve("configs/demo-advertising-only.yaml")
    cap = instance["channels"]["advertising"]["A_ad_cap"]
    assert (df["A_advertising"] <= cap + 1e-6).all()


def test_ceiling_still_binds_with_channels():
    config, instance, solution, df = _solve("configs/demo-mixed-channels.yaml")
    ceiling = instance["log_ceiling"]
    slack = instance["ceiling_slack"]
    for t, value in ceiling.items():
        total = df.loc[df["t"] == t, "Adq_clientes"].iloc[0]
        assert total <= value * (1 + slack) + 1e-6


def test_share_bounds():
    config, instance, solution, df = _solve("configs/demo-mixed-channels.yaml")
    channels = instance["channels"]
    for _, row in df.iterrows():
        total = row["Adq_clientes"]
        sf = channels["salesforce"]
        if sf["min_share"] > 0.0:
            assert row["A_salesforce"] >= sf["min_share"] * total - 1e-6
        ad = channels["advertising"]
        if ad["max_share"] < 1.0:
            assert row["A_advertising"] <= ad["max_share"] * total + 1e-6


def test_channel_share_validator():
    # Sum of active max_share < 1.0 is rejected.
    cfg = default_config()
    cfg["channels"]["salesforce"]["max_share"] = 0.5
    cfg["channels"]["advertising"] = {
        "active": True, "I_min": 0, "I_max": 100, "A_min": 0, "A_max": 10,
        "A_ad_cap": 10, "min_share": 0.0, "max_share": 0.3,
    }
    with pytest.raises(ValueError, match="max_share"):
        validate_config(cfg)

    # A_max <= A_min rejected.
    cfg = default_config()
    cfg["channels"]["advertising"] = {
        "active": True, "I_min": 0, "I_max": 100, "A_min": 10, "A_max": 10,
        "A_ad_cap": 10, "min_share": 0.0, "max_share": 1.0,
    }
    with pytest.raises(ValueError, match="A_max"):
        validate_config(cfg)

    # I_max <= I_min rejected.
    cfg = default_config()
    cfg["channels"]["advertising"] = {
        "active": True, "I_min": 100, "I_max": 100, "A_min": 0, "A_max": 10,
        "A_ad_cap": 10, "min_share": 0.0, "max_share": 1.0,
    }
    with pytest.raises(ValueError, match="I_max"):
        validate_config(cfg)


def test_advertising_cap_below_a_min_rejected():
    """A_ad_cap is a derived technical parameter, not a product input: absent/None/0
    is silently derived from A_max (Free The Mama fix), so it can no longer cause
    the historical A_ad_cap=0 infeasibility trap. An *explicit* positive cap that
    still contradicts the recta's own lower bound (A_min) for t>=13 must still be
    rejected — that is a genuine user override, not a default-value trap."""
    cfg = default_config()
    cfg["channels"]["advertising"] = {
        "active": True, "I_min": 4461, "I_max": 8000, "A_min": 373, "A_max": 13000,
        "A_ad_cap": 0, "min_share": 0.0, "max_share": 1.0,
    }
    validate_config(cfg)
    assert cfg["channels"]["advertising"]["A_ad_cap"] == pytest.approx(13000)

    # Explicit positive cap below A_min is still a genuine error.
    cfg = default_config()
    cfg["channels"]["advertising"] = {
        "active": True, "I_min": 4461, "I_max": 8000, "A_min": 373, "A_max": 13000,
        "A_ad_cap": 50, "min_share": 0.0, "max_share": 1.0,
    }
    with pytest.raises(ValueError, match="A_ad_cap"):
        validate_config(cfg)

    # cap >= A_min passes this check
    cfg["channels"]["advertising"]["A_ad_cap"] = 373
    validate_config(cfg)


def test_advertising_active_without_cap_key_derives_a_max():
    """Advertising active with no A_ad_cap key at all: validate_config passes and
    derives A_ad_cap == A_max in place, matching the case where a product-facing
    form never asks for the cap."""
    cfg = default_config()
    cfg["channels"]["advertising"] = {
        "active": True, "I_min": 0, "I_max": 100, "A_min": 0, "A_max": 10,
        "min_share": 0.0, "max_share": 1.0,
    }
    validate_config(cfg)
    assert cfg["channels"]["advertising"]["A_ad_cap"] == pytest.approx(10.0)


def test_salesforce_capacity_only_binds_salesforce():
    config, instance, solution, df = _solve("configs/demo-mixed-channels.yaml")
    lag = config.get("commercial_productivity_lag", 0)
    meta = instance["meta"]
    sellers = {int(r["t"]): r["Vendedores"] for _, r in df.iterrows()}
    for _, row in df.iterrows():
        t = int(row["t"])
        if t < 13:
            continue
        cap_period = max(1, t - lag)
        # Salesforce acquisition is bounded by salesforce capacity ...
        assert row["A_salesforce"] <= meta * sellers[cap_period] + 1e-6
    # ... while total acquisition can exceed it thanks to advertising.
    assert (df["A_advertising"] > 0).any()
