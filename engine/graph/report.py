from __future__ import annotations

from pathlib import Path
from typing import Any


def write_asset_report(
    outdir: Path,
    asset: str,
    timeframe: str,
    state_label: str,
    confidence: float,
    quality: dict[str, Any],
    metrics: dict[str, Any],
    thresholds: dict[str, Any],
    graph_params: dict[str, Any],
    recommendation: str,
    gating: dict[str, Any] | None = None,
    diagnostics: dict[str, Any] | None = None,
    **_: Any,
) -> Path:
    base = f"{asset}_{timeframe}"
    report_path = outdir / "assets" / f"{base}_report.md"

    report = f"""# {asset} ({timeframe}) - Graph Regime Report

## A) Plain-language read

**What is a regime?**
A regime is the current state of the system: stable, transition, or unstable.

**Current regime**
Current regime: **{state_label}** with confidence **{confidence:.2f}**.

**Confidence and escape**
- Confidence measures how much the system stays in the same state.
- Escape measures how likely it is to leave the current state.

**Action**
Recommendation: **{recommendation}**.
"""
    if gating:
        report += f"""

**Forecast governance**
- Forecast reliable: **{gating.get("forecast_reliable", False)}**
- Reasons: **{", ".join(gating.get("reasons") or [])}**
"""

    report += f"""

## B) Technical read

**Microstate graph**
Takens embedding is discretized into microstates, and temporal transitions form matrix P.

**Local stretch**
\\( \\ell_t = \\log\\frac{{d_1 + \\epsilon}}{{d_0 + \\epsilon}} \\), with distances measured in embedding space.
Stretch is clipped by quantiles (q05/q95).

**Metastable regimes**
Regimes are extracted with spectral clustering over transition structure.

**Confidence and escape**
Confidence = transition mass staying inside same regime.
Escape = 1 - confidence.

**Parameters**
- {graph_params}

**Thresholds**
- {thresholds}

**Metrics**
- {metrics}

**Graph quality**
- {quality}
"""
    if diagnostics:
        report += f"""

**Dynamics diagnostics (experimental)**
- {diagnostics}
"""
    report += f"""

## Generated artifacts
- embedding: assets/{base}_embedding.csv
- regimes: assets/{base}_regimes.csv
- micrograph: assets/{base}_micrograph.json
- transitions: assets/{base}_transitions.json
- plots: assets/{base}_plots/
"""
    report_path.write_text(report, encoding="utf-8")
    return report_path
