"""Compatibility package for legacy graph_engine imports.

This package keeps old import paths working after the engine refactor.
"""

from __future__ import annotations

from pathlib import Path
from pkgutil import extend_path

_ROOT = Path(__file__).resolve().parents[1]
_LEGACY = _ROOT / "legacy" / "graph_engine_legacy"

__path__ = extend_path(__path__, __name__)  # type: ignore[name-defined]
if _LEGACY.exists():
    __path__.append(str(_LEGACY))  # type: ignore[attr-defined]

