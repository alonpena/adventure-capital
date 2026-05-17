"""Simple YAML schema checks for document YAML."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

DEFAULT_SCHEMA_PATH = Path("reports/schema/valuation-document.schema.yaml")


def load_schema(path: str | Path = DEFAULT_SCHEMA_PATH) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f) or {}
    if not isinstance(schema, dict):
        raise ValueError("Schema YAML must contain a mapping at root.")
    return schema


def get_path(data: dict[str, Any], dotted_path: str) -> Any:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def is_missing(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def validate_required_paths(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for path in schema.get("required", []):
        if is_missing(get_path(data, path)):
            missing.append(path)
    for path, rules in schema.get("collections", {}).items():
        value = get_path(data, path)
        min_items = int(rules.get("min_items", 1))
        if not isinstance(value, list) or len(value) < min_items:
            missing.append(path)
    return sorted(set(missing))
