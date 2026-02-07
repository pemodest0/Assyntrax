#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from hmmlearn.hmm import GaussianHMM


def _load_series(path: Path) -> pd.Series:
    df = pd.read_csv(path)
    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError(f"missing columns in {path.name} (need date,value)")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "value"]).sort_values("date")
    return pd.Series(df["value"].astype(float).values, index=df["date"])


def main() -> None:
    parser = argparse.ArgumentParser(description="HMM regimes (realestate).")
    parser.add_argument("--input-dir", default="data/realestate/normalized")
    parser.add_argument("--outdir", default="results/realestate/hmm")
    parser.add_argument("--states", type=int, default=4)
    parser.add_argument("--min-samples", type=int, default=60)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for csv in sorted(Path(args.input_dir).glob("*.csv")):
        series = _load_series(csv)
        if len(series) < args.min_samples:
            continue
        vals = series.values.astype(float)
        ret = pd.Series(vals).pct_change().replace([np.inf, -np.inf], np.nan).dropna().values
        if ret.size < args.states * 5:
            continue
        vol = pd.Series(ret).rolling(6).std().fillna(0.0).values
        X = np.column_stack([ret, vol])
        X = X[np.isfinite(X).all(axis=1)]
        if X.shape[0] < args.states * 5:
            continue

        model = GaussianHMM(
            n_components=args.states,
            covariance_type="diag",
            n_iter=200,
            random_state=42,
            min_covar=1e-6,
        )
        model.fit(X)
        states = model.predict(X)
        probs = model.predict_proba(X)

        out = {
            "asset": csv.stem.upper(),
            "states": int(args.states),
            "transmat": model.transmat_.tolist(),
            "means": model.means_.tolist(),
            "covars": model.covars_.tolist(),
            "sequence": states.tolist(),
            "probabilities": probs.tolist(),
        }
        dest = outdir / f"{csv.stem.upper()}_hmm.json"
        dest.write_text(json.dumps(out, indent=2))
    print(f"[ok] wrote HMM outputs to {outdir}")


if __name__ == "__main__":
    main()
