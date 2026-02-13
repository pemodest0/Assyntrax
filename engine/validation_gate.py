from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class GateResult:
    status: str
    domain: str
    quality: float | None
    confidence: float | None
    transition_rate: float | None
    novelty: float | None
    reasons: list[str]
    thresholds: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "domain": self.domain,
            "quality": self.quality,
            "confidence": self.confidence,
            "transition_rate": self.transition_rate,
            "novelty": self.novelty,
            "reasons": self.reasons,
            "thresholds": self.thresholds,
        }


def _root_from_here() -> Path:
    return Path(__file__).resolve().parents[1]


def load_gate_config(path: str | Path | None = None) -> dict[str, Any]:
    cfg_path = Path(path) if path else (_root_from_here() / "config" / "validation_gates.json")
    if not cfg_path.exists():
        raise FileNotFoundError(f"validation gate config not found: {cfg_path}")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


def infer_domain(asset: str, group: str | None = None) -> str:
    g = (group or "").lower()
    a = (asset or "").upper()
    if g in {"realestate", "imobiliario", "real_estate"} or a.startswith("RE_"):
        return "realestate"
    if g in {"energy", "ons_grid", "logistics_energy"}:
        return "energy"
    return "finance"


def _to_float(value: Any) -> float | None:
    try:
        v = float(value)
        if v == v and v != float("inf") and v != float("-inf"):
            return v
    except Exception:
        return None
    return None


def evaluate_gate(
    *,
    asset: str,
    group: str | None = None,
    quality: Any = None,
    confidence: Any = None,
    transition_rate: Any = None,
    novelty: Any = None,
    config: dict[str, Any] | None = None,
) -> GateResult:
    cfg = config or load_gate_config()
    domain = infer_domain(asset=asset, group=group)
    default = dict(cfg.get("default") or {})
    per_domain = dict((cfg.get("domains") or {}).get(domain) or {})
    thresholds = {**default, **per_domain}

    q = _to_float(quality)
    c = _to_float(confidence)
    tr = _to_float(transition_rate)
    nv = _to_float(novelty)

    reasons: list[str] = []
    min_q = _to_float(thresholds.get("min_quality")) or 0.0
    min_c = _to_float(thresholds.get("min_confidence")) or 0.0
    max_tr = _to_float(thresholds.get("max_transition_rate"))
    max_nv = _to_float(thresholds.get("max_novelty"))

    if q is None:
        reasons.append("quality_missing")
    elif q < min_q:
        reasons.append("quality_below_gate")

    if c is None:
        reasons.append("confidence_missing")
    elif c < min_c:
        reasons.append("confidence_below_gate")

    if max_tr is not None and tr is not None and tr > max_tr:
        reasons.append("transition_rate_above_gate")
    if max_nv is not None and nv is not None and nv > max_nv:
        reasons.append("novelty_above_gate")

    status = "validated" if not reasons else "inconclusive"
    return GateResult(
        status=status,
        domain=domain,
        quality=q,
        confidence=c,
        transition_rate=tr,
        novelty=nv,
        reasons=reasons,
        thresholds={k: float(v) for k, v in thresholds.items() if _to_float(v) is not None},
    )
