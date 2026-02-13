from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.diagnostics.predictability import (
    classify_predictability,
    compute_acf,
    hurst_exponent_rs,
    lyapunov_proxy,
)


def test_predictability_diagnostics_smoke() -> None:
    x = np.linspace(0.0, 12.0 * np.pi, 600)
    series = np.sin(x) + 0.05 * np.random.default_rng(11).normal(size=x.size)

    acf = compute_acf(series, max_lag=30)
    hurst = hurst_exponent_rs(series, min_window=10, max_window=120)
    lyap = lyapunov_proxy(errors_by_horizon=[0.05, 0.07, 0.11, 0.17], horizons=[1, 5, 10, 20])
    label = classify_predictability(
        acf=acf,
        hurst=hurst,
        lyap=lyap,
        win_rate=0.62,
        avg_improvement=0.03,
    )

    assert np.isfinite(acf.acf1)
    assert acf.max_lag <= 30
    assert label in {
        "PREVISIVEL_CURTO_PRAZO",
        "REGIME_DEPENDENTE",
        "INSTAVEL_OU_CAOTICO",
        "ESSENCIALMENTE_RUIDOSO",
    }
