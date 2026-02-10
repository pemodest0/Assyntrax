#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from engine.graph.embedding import takens_embed
from engine.graph.diagnostics import _rqa_metrics, estimate_tau_adaptive, estimate_embedding_dim


def _load_series(path: Path) -> pd.Series:
    df = pd.read_csv(path)
    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError(f"missing columns in {path.name} (need date,value)")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "value"]).sort_values("date")
    return pd.Series(df["value"].astype(float).values, index=df["date"])


def main() -> None:
    parser = argparse.ArgumentParser(description="RQA metrics (realestate).")
    parser.add_argument("--input-dir", default="data/realestate/normalized")
    parser.add_argument("--outdir", default="results/realestate/rqa")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    summary = {}
    for csv in sorted(Path(args.input_dir).glob("*.csv")):
        series = _load_series(csv)
        values = series.values.astype(float)
        tau, tau_info = estimate_tau_adaptive(values, max_lag=min(20, max(5, len(values) // 4)))
        emb_dim = estimate_embedding_dim(values, tau=tau, max_dim=min(10, max(3, len(values) // 10)))
        m = emb_dim["m_opt"]
        emb = takens_embed(values, m=m, tau=tau)
        rqa = _rqa_metrics(emb)
        out = {
            "asset": csv.stem.upper(),
            "tau": tau,
            "m": m,
            "tau_info": tau_info,
            "cao": emb_dim,
            "rqa": rqa,
        }
        dest = outdir / f"{csv.stem.upper()}_rqa.json"
        dest.write_text(json.dumps(out, indent=2))
        summary[csv.stem.upper()] = out

    (outdir / "rqa_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"[ok] wrote {outdir / 'rqa_summary.json'}")


if __name__ == "__main__":
    main()

