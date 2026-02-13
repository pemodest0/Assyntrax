from __future__ import annotations

import numpy as np
import pytest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from engine.graph.embedding import select_tau, takens_embed


def test_takens_embed_shape_and_order() -> None:
    series = np.array([1, 2, 3, 4, 5], dtype=float)
    out = takens_embed(series, m=3, tau=1)
    expected = np.array(
        [
            [3.0, 2.0, 1.0],
            [4.0, 3.0, 2.0],
            [5.0, 4.0, 3.0],
        ]
    )
    np.testing.assert_allclose(out, expected)


def test_takens_embed_raises_when_series_too_short() -> None:
    with pytest.raises(ValueError, match="series too short"):
        takens_embed(np.array([1, 2, 3, 4, 5, 6], dtype=float), m=4, tau=2)


def test_select_tau_constant_series_defaults_to_one() -> None:
    series = np.ones(64, dtype=float)
    assert select_tau(series, max_lag=10, max_tau=3, method="ami") == 1
    assert select_tau(series, max_lag=10, max_tau=3, method="autocorr") == 1


def test_select_tau_respects_max_tau_cap() -> None:
    x = np.linspace(0, 8 * np.pi, 240)
    series = np.sin(x) + 0.1 * np.cos(3 * x)
    tau = select_tau(series, max_lag=20, max_tau=2, method="ami")
    assert 1 <= tau <= 2
