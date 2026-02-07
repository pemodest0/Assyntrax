from __future__ import annotations

import argparse
from pathlib import Path
import json

import numpy as np
import pandas as pd


def _load_series(path: Path) -> pd.Series:
    df = pd.read_csv(path)
    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError(f"missing columns in {path.name} (need date,value)")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "value"]).sort_values("date")
    return pd.Series(df["value"].values, index=df["date"])


def km_drift_diffusion(values: np.ndarray, bins: int = 12) -> dict:
    x = values.astype(float)
    dx = np.diff(x)
    x0 = x[:-1]
    if x0.size < bins + 2:
        bins = max(4, x0.size // 2)
    qs = np.linspace(0.0, 1.0, bins + 1)
    edges = np.quantile(x0, qs)
    if np.unique(edges).size < bins + 1:
        edges = np.linspace(float(x0.min()), float(x0.max()), bins + 1)
    drift = []
    diffusion = []
    centers = []
    for i in range(bins):
        lo, hi = edges[i], edges[i + 1]
        mask = (x0 >= lo) & (x0 <= hi)
        if mask.sum() < 3:
            continue
        m1 = float(np.mean(dx[mask]))
        m2 = float(np.mean(dx[mask] ** 2))
        d1 = m1
        d2 = max(0.0, 0.5 * (m2 - m1 ** 2))
        centers.append(float((lo + hi) / 2.0))
        drift.append(d1)
        diffusion.append(d2)
    return {"centers": centers, "drift": drift, "diffusion": diffusion}


def main() -> None:
    parser = argparse.ArgumentParser(description="Kramers-Moyal drift/diffusion (simplificado).")
    parser.add_argument("--input", required=True, help="CSV com colunas date,value")
    parser.add_argument("--bins", type=int, default=12)
    parser.add_argument("--outdir", default="results/realestate/km")
    args = parser.parse_args()

    series = _load_series(Path(args.input))
    out = km_drift_diffusion(series.values, bins=args.bins)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out_path = outdir / f"{Path(args.input).stem}_km.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[ok] wrote {out_path}")


if __name__ == "__main__":
    main()
