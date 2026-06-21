"""Ensure the repo root is importable so root-level modules (app.py,
streamlit_pages/) can be imported by tests under the src-layout package."""

import sys
from pathlib import Path

ROOT = str(Path(__file__).parent.resolve())
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
