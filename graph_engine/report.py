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

    report = f"""# {asset} ({timeframe}) — Graph Regime Report

## A) Leitura para leigos

**O que é regime?**  
Regime é o estado atual do sistema: estável, em transição ou instável. Ele indica se a dinâmica é confiável.

**O que significa o regime atual?**  
Regime atual: **{state_label}** com confiança **{confidence:.2f}**.

**Confiança e escape (resumo):**
- Confiança mede quanto o sistema permanece no mesmo estado.
- Escape indica quão fácil é sair do estado atual.

**O que fazer agora?**  
Recomendação: **{recommendation}**.
"""
    if gating:
        report += f"""

**Confiabilidade do forecast (governança):**
- Forecast confiável: **{gating.get("forecast_reliable", False)}**
- Razões: **{", ".join(gating.get("reasons") or [])}**
"""

    report += f"""

## B) Leitura científica

**Grafo de microestados**  
O embedding de Takens é discretizado em microestados (KMeans). As transições temporais formam uma matriz P.

**Estiramento local**  
\\( \\ell_t = \\log\\frac{{d_1 + \\epsilon}}{{d_0 + \\epsilon}} \\) onde d0/d1 são distâncias no embedding.
O estiramento é limitado por quantis (q05/q95) para evitar saturação.

**Regimes metastáveis**  
Regimes são extraídos via spectral clustering no grafo de transições.

**Confiança e escape**  
Confiança = soma de transições dentro do mesmo regime.  
Escape = 1 - confiança.

**Parâmetros**
- {graph_params}

**Thresholds**
- {thresholds}

**Métricas**
- {metrics}

**Qualidade do grafo**
- {quality}
"""
    if diagnostics:
        report += f"""

**Diagnósticos de dinâmica (experimental)**
- {diagnostics}
"""
    report += f"""

## Arquivos gerados
- embedding: assets/{base}_embedding.csv
- regimes: assets/{base}_regimes.csv
- micrograph: assets/{base}_micrograph.json
- transitions: assets/{base}_transitions.json
- plots: assets/{base}_plots/
"""
    report_path.write_text(report, encoding="utf-8")
    return report_path
