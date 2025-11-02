#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def load_metrics(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    if df["date"].dt.tz is not None:
        df["date"] = df["date"].dt.tz_convert("UTC").dt.tz_localize(None)
    return df[df["mode"] == "classical"].copy()


def main() -> None:
    parser = argparse.ArgumentParser(description="Avalia limites da moeda adaptativa (momentum, vol_ratio, drawdown).")
    parser.add_argument("metrics", type=str, help="Arquivo daily_forecast_metrics.csv.")
    parser.add_argument("--momentum-scale", type=float, default=0.03)
    parser.add_argument("--vol-scale", type=float, default=0.12)
    parser.add_argument("--drawdown-scale", type=float, default=0.08)
    parser.add_argument("--clamp", type=float, default=3.0)
    parser.add_argument("--vol-threshold", type=float, default=1.6)
    parser.add_argument("--drawdown-threshold", type=float, default=-0.12)
    parser.add_argument("--risk-scale", type=float, default=0.35)
    parser.add_argument("--floor", type=float, default=0.05)
    parser.add_argument("--momentum-weight", type=float, default=1.0)
    parser.add_argument("--vol-weight", type=float, default=0.5)
    parser.add_argument("--drawdown-weight", type=float, default=0.4)
    args = parser.parse_args()

    df = load_metrics(Path(args.metrics))
    mom = df["momentum_10"].to_numpy()
    vol = df["vol_ratio"].to_numpy()
    draw = df["drawdown_long"].to_numpy()

    def _signal(values, scale):
        scale = max(scale, 1e-6)
        clamp = max(args.clamp, 0.5)
        norm = np.clip(values / scale, -clamp, clamp)
        return np.tanh(norm)

    score = args.momentum_weight * _signal(mom, args.momentum_scale)
    score += args.vol_weight * _signal(vol - 1.0, args.vol_scale)
    score += args.drawdown_weight * _signal(draw, args.drawdown_scale)

    score = np.clip(score, -args.clamp, args.clamp)
    trend = np.tanh(score)
    risk_flag = ((np.isfinite(vol) & (vol >= args.vol_threshold)) | (np.isfinite(draw) & (draw <= args.drawdown_threshold)))
    trend_adjusted = trend.copy()
    trend_adjusted[risk_flag] *= (1.0 - args.risk_scale)
    bias_right = 0.5 + 0.5 * trend_adjusted
    floor = min(max(args.floor, 0.0), 0.49)
    bias_right = np.clip(bias_right, floor, 1.0 - floor)

    print(f"Total registros: {len(df)}")
    print(f"Momentum | min={np.nanmin(mom):.4f} max={np.nanmax(mom):.4f}")
    print(f"Vol ratio | min={np.nanmin(vol):.4f} max={np.nanmax(vol):.4f}")
    print(f"Drawdown | min={np.nanmin(draw):.4f} max={np.nanmax(draw):.4f}")
    print(f"Score | min={np.nanmin(score):.4f} max={np.nanmax(score):.4f}")
    print(f"Trend (tanh) | min={np.nanmin(trend):.4f} max={np.nanmax(trend):.4f}")
    print(f"Bias_right após risco | min={np.nanmin(bias_right):.4f} max={np.nanmax(bias_right):.4f}")
    print(f"Eventos risco: {int(risk_flag.sum())} ({risk_flag.sum() / len(df) * 100:.2f}%)")


if __name__ == "__main__":
    main()
