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
    parser = argparse.ArgumentParser(description="Forecast por regime (realestate).")
    parser.add_argument("--input-dir", default="data/realestate/normalized")
    parser.add_argument("--hmm-dir", default="results/realestate/hmm")
    parser.add_argument("--outdir", default="results/realestate/forecast_by_regime")
    parser.add_argument("--horizons", default="1,3,6,12")
    parser.add_argument("--min-train", type=int, default=48)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    horizons = [int(h.strip()) for h in args.horizons.split(",") if h.strip()]
    summary = {}

    for csv in sorted(Path(args.input_dir).glob("*.csv")):
        asset = csv.stem.upper()
        hmm_path = Path(args.hmm_dir) / f"{asset}_hmm.json"
        if not hmm_path.exists():
            continue
        series = _load_series(csv)
        hmm = json.loads(hmm_path.read_text())
        seq = np.asarray(hmm.get("sequence", []), dtype=int)
        if seq.size == 0:
            continue

        # align HMM sequence to returns (sequence length == len(ret))
        values = series.values
        ret_len = len(values) - 1
        if seq.size > ret_len:
            seq = seq[-ret_len:]
        if seq.size < ret_len:
            # pad front
            pad = np.full(ret_len - seq.size, seq[0], dtype=int)
            seq = np.concatenate([pad, seq])

        asset_out = {}
        for h in horizons:
            y_true, y_pred = _walk_forward(series, horizon=h, min_train=args.min_train)
            if y_true.size == 0:
                continue
            last_pred = y_pred[:, 0]
            drift_pred = y_pred[:, 1]

            # map regime index to each forecast point (uses t index on series)
            # walk_forward uses t from min_train .. len(values)-h-1
            regimes = []
            for t in range(args.min_train, len(values) - h):
                # regime at t-1 corresponds to return index
                regimes.append(int(seq[t - 1]))
            regimes = np.asarray(regimes)

            by_reg = {}
            for reg in np.unique(regimes):
                mask = regimes == reg
                if mask.sum() < 5:
                    continue
                mase_naive = _mase(y_true[mask], last_pred[mask], values)
                mase_drift = _mase(y_true[mask], drift_pred[mask], values)
                best = "drift" if (mase_drift is not None and (mase_naive is None or mase_drift <= mase_naive)) else "naive"
                best_mase = min([m for m in [mase_naive, mase_drift] if m is not None], default=None)
                by_reg[str(reg)] = {
                    "mase_naive": mase_naive,
                    "mase_drift": mase_drift,
                    "best_model": best,
                    "best_mase": best_mase,
                    "n": int(mask.sum()),
                }
            asset_out[str(h)] = {"by_regime": by_reg}

        if asset_out:
            summary[asset] = asset_out
            (outdir / f"{asset}_forecast_by_regime.json").write_text(json.dumps(asset_out, indent=2))

    (outdir / "forecast_by_regime_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"[ok] wrote {outdir / 'forecast_by_regime_summary.json'}")


if __name__ == "__main__":
    main()
