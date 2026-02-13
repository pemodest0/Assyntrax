from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.graph.multilayer import run_multilayer_engine


def test_multilayer_engine_smoke() -> None:
    x = np.linspace(0.0, 10.0 * np.pi, 1200)
    stable = np.sin(x[:600]) + 0.01 * np.random.default_rng(7).normal(size=600)
    unstable = 0.5 * np.sin(2.0 * x[:600]) + 0.08 * np.random.default_rng(8).normal(size=600)
    series = np.concatenate([stable, unstable])
    out = run_multilayer_engine(series, timeframe="daily")
    assert out["status"] in {"ok", "insufficient"}
    assert "decision" in out
    if out["status"] == "ok":
        assert out["decision"]["label"] in {"STABLE", "TRANSITION", "UNSTABLE", "NOISY"}
        assert 0.0 <= float(out["decision"]["confidence"]) <= 1.0
        assert isinstance(out["decision"]["alert_triggered"], bool)
        assert "eigen_persist_ok" in out["layers"]["layer4"]
