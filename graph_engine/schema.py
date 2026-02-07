from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def iso_now() -> str:
    return datetime.now(timezone.utc).date().isoformat()


@dataclass
class GraphState:
    label: str
    confidence: float


@dataclass
class GraphConfig:
    n_micro: int
    k_nn: int
    theiler: int
    alpha: float
    method: str = "spectral"


@dataclass
class GraphMetrics:
    stay_prob: float
    escape_prob: float
    stretch_mu: float
    stretch_frac_pos: float


@dataclass
class GraphLinks:
    regimes_csv: str
    embedding_csv: str
    micrograph_json: str
    transitions_json: str


@dataclass
class GraphAsset:
    asset: str
    timeframe: str
    asof: str
    state: GraphState
    graph: GraphConfig
    metrics: GraphMetrics
    alerts: List[str]
    links: GraphLinks
    schema_version: str = "1.0"
    engine_version: Optional[str] = None
    group: Optional[str] = None
    quality: Optional[Dict[str, Any]] = None
    forecast_diag: Optional[Dict[str, Any]] = None
    risk: Optional[Dict[str, Any]] = None
    thresholds: Optional[Dict[str, Any]] = None
    gating: Optional[Dict[str, Any]] = None
    governance: Optional[Dict[str, Any]] = None
    diagnostics: Optional[Dict[str, Any]] = None
    recommendation: Optional[str] = None
    scores: Optional[Dict[str, Any]] = None
    badges: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.engine_version is None:
            data.pop("engine_version", None)
        if self.group is None:
            data.pop("group", None)
        if self.forecast_diag is None:
            data.pop("forecast_diag", None)
        if self.risk is None:
            data.pop("risk", None)
        if self.quality is None:
            data.pop("quality", None)
        if self.thresholds is None:
            data.pop("thresholds", None)
        if self.gating is None:
            data.pop("gating", None)
        if self.governance is None:
            data.pop("governance", None)
        if self.diagnostics is None:
            data.pop("diagnostics", None)
        if self.recommendation is None:
            data.pop("recommendation", None)
        if self.scores is None:
            data.pop("scores", None)
        if self.badges is None:
            data.pop("badges", None)
        return data
