#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from graph_engine.schema import GraphAsset, GraphConfig, GraphLinks, GraphMetrics, GraphState, iso_now  # noqa: E402
from graph_engine.export import write_asset_bundle, write_universe  # noqa: E402
from graph_engine.core import run_graph_engine  # noqa: E402


def build_example(asset: str, timeframe: str, outdir: Path) -> GraphAsset:
    base = f"{asset}_{timeframe}"
    links = GraphLinks(
        regimes_csv=f"assets/{base}_regimes.csv",
        embedding_csv=f"assets/{base}_embedding.csv",
        micrograph_json=f"assets/{base}_micrograph.json",
        transitions_json=f"assets/{base}_transitions.json",
    )

    return GraphAsset(
        asset=asset,
        timeframe=timeframe,
        asof=iso_now(),
        state=GraphState(label="STABLE", confidence=0.82),
        graph=GraphConfig(n_micro=200, k_nn=0, theiler=10, alpha=2.0),
        metrics=GraphMetrics(stay_prob=0.73, escape_prob=0.27, stretch_mu=-0.12, stretch_frac_pos=0.22),
        alerts=[],
        links=links,
    )


def main() -> None:
    outdir = Path("results/latest_graph")
    outdir.mkdir(parents=True, exist_ok=True)

    asset = build_example("SPY", "weekly", outdir)

    series = [0.1 * i for i in range(300)]
    result = run_graph_engine(
        np.array(series),
        m=3,
        tau=1,
        n_micro=50,
        n_regimes=3,
        k_nn=5,
        theiler=5,
        alpha=2.0,
        seed=7,
    )

    micrograph = result.micrograph
    transitions = {
        "matrix": result.p_matrix.tolist(),
        "labels": [f"R{i}" for i in range(result.p_matrix.shape[0])],
    }

    write_asset_bundle(
        asset,
        outdir,
        embedding=result.embedding[:, :2],
        regimes=[{"t": int(i), "regime": str(r), "confidence": float(c)} for i, (r, c) in enumerate(zip(result.state_labels, result.confidence))],
        micrograph=micrograph,
        transitions=transitions,
    )

    write_universe([asset], outdir / "universe_weekly.json")
    write_universe([asset], outdir / "universe_daily.json")

    print("Example written to results/latest_graph/")


if __name__ == "__main__":
    main()
