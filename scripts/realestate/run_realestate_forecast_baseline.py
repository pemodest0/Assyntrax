#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _load_series(path: Path) -> pd.Series:
    df = pd.read_csv(path)
    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError(f"missing columns in {path.name} (need date,value)")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "value"]).sort_values("date")
    return pd.Series(df["value"].astype(float).values, index=df["date"])


def _mase(y_true: np.ndarray, y_pred: np.ndarray, y_insample: np.ndarray) -> float:
    mae = np.mean(np.abs(y_true - y_pred))
    denom = np.mean(np.abs(np.diff(y_insample)))
    if denom <= 1e-12:
        return float("nan")
    return float(mae / denom)


def _walk_forward(series: pd.Series, horizon: int, min_train: int = 48):
    values = series.values
    preds = []
    actuals = []
    for t in range(min_train, len(values) - horizon):
        train = values[:t]
        last = train[-1]
        drift = train[-1] + (train[-1] - train[0]) / max(1, len(train) - 1) * horizon
        preds.append((last, drift))
        actuals.append(values[t + horizon])
    return np.array(actuals), np.array(preds)


def main() -> None:
    parser = argparse.ArgumentParser(description="Forecast baseline (realestate).")
    parser.add_argument("--input-dir", default="data/realestate/normalized")
    parser.add_argument("--outdir", default="results/realestate/forecast")
    parser.add_argument("--horizons", default="1,3,6,12")
    parser.add_argument("--min-train", type=int, default=48)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    horizons = [int(h.strip()) for h in args.horizons.split(",") if h.strip()]
    summary = {}

    for csv in sorted(Path(args.input_dir).glob("*.csv")):
        series = _load_series(csv)
        asset = csv.stem.upper()
        asset_out = {}
        for h in horizons:
            y_true, y_pred = _walk_forward(series, horizon=h, min_train=args.min_train)
            if y_true.size == 0:
                continue
            last_pred = y_pred[:, 0]
            drift_pred = y_pred[:, 1]
            mase_last = _mase(y_true, last_pred, series.values)
            mase_drift = _mase(y_true, drift_pred, series.values)
            asset_out[str(h)] = {
                "mase_naive": mase_last,
                "mase_drift": mase_drift,
                "n": int(y_true.size),
            }
        if asset_out:
            summary[asset] = asset_out
            (outdir / f"{asset}_forecast_baseline.json").write_text(json.dumps(asset_out, indent=2))

    (outdir / "forecast_baseline_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"[ok] wrote {outdir / 'forecast_baseline_summary.json'}")


if __name__ == "__main__":
    main()
