"""Document YAML loading for standard valuation reports."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_document(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError("Document YAML must contain a mapping at root.")
    return data
