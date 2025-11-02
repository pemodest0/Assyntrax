#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd


def load_and_pivot(metrics_path: Path) -> pd.DataFrame:
    df = pd.read_csv(metrics_path, parse_dates=["date"])
    if df["date"].dt.tz is not None:
        df["date"] = df["date"].dt.tz_convert("UTC").dt.tz_localize(None)
    pivot_cols = ["price_pred", "expected_return", "alpha", "entropy"]
    pivot_df = (
        df.pivot_table(
            index=["date", "price_real", "price_today", "symbol"],
            columns="mode",
            values=pivot_cols,
            aggfunc="first",
        )
        .dropna(axis=0, how="any")
        .reset_index()
    )
    pivot_df.columns = ["_".join(col).strip("_") for col in pivot_df.columns.to_flat_index()]
    return pivot_df


def compute_blend_alpha(
    frame: pd.DataFrame,
    train_end: pd.Timestamp,
    mode_quantum: str,
) -> float:
    mask_train = frame["date"] <= train_end
    if not mask_train.any():
        raise ValueError("Nenhum dado disponível para calibrar alpha.")
    c_pred = frame.loc[mask_train, "price_pred_classical"].astype(float).to_numpy()
    q_pred = frame.loc[mask_train, f"price_pred_{mode_quantum}"].astype(float).to_numpy()
    real = frame.loc[mask_train, "price_real"].astype(float).to_numpy()
    diff = q_pred - c_pred
    denom = np.dot(diff, diff)
    if denom == 0.0:
        return 0.0
    alpha = float(np.dot(real - c_pred, diff) / denom)
    return alpha


def evaluate_mae(frame: pd.DataFrame, column: str, start: pd.Timestamp, end: pd.Timestamp) -> Dict[str, float]:
    mask = (frame["date"] >= start) & (frame["date"] <= end)
    sub = frame.loc[mask].copy()
    if sub.empty:
        return {"records": 0, "mae": float("nan")}
    err = (sub[column] - sub["price_real"]).abs()
    return {
        "records": int(sub.shape[0]),
        "mae": float(err.mean()),
        "mae_pct": float((err / sub["price_real"].abs().clip(lower=1e-6)).mean() * 100.0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Blenda previsões clássicas e quânticas via alpha otimizado.")
    parser.add_argument("metrics", type=str, help="Arquivo daily_forecast_metrics.csv com modos classical e quantum.")
    parser.add_argument("--mode", type=str, default="grover", help="Modo quântico a usar para blend (ex.: grover, hadamard).")
    parser.add_argument("--train-end", type=str, default="2023-12-31", help="Data limite para calibrar alpha.")
    parser.add_argument("--test-start", type=str, default="2024-01-01", help="Data inicial para relatório de teste.")
    parser.add_argument("--output", type=str, default="results/crypto_blend", help="Diretório para salvar resultados.")
    args = parser.parse_args()

    metrics_path = Path(args.metrics)
    if not metrics_path.exists():
        raise SystemExit(f"Arquivo não encontrado: {metrics_path}")
    mode_quantum = args.mode.lower()

    frame = load_and_pivot(metrics_path)
    required_cols = {f"price_pred_{mode_quantum}", "price_pred_classical"}
    if not required_cols.issubset(frame.columns):
        raise SystemExit(f"Colunas necessárias não encontradas no arquivo para modo '{mode_quantum}'.")

    frame["date"] = pd.to_datetime(frame["date"])
    train_end = pd.Timestamp(args.train_end)
    test_start = pd.Timestamp(args.test_start)
    alpha = compute_blend_alpha(frame, train_end, mode_quantum)

    frame["price_pred_blend"] = frame["price_pred_classical"] + alpha * (
        frame[f"price_pred_{mode_quantum}"] - frame["price_pred_classical"]
    )

    last_five_start = frame["date"].max() - pd.DateOffset(years=5)
    if last_five_start < frame["date"].min():
        last_five_start = frame["date"].min()

    comparison = {
        "alpha": alpha,
        "train_end": train_end.strftime("%Y-%m-%d"),
        "test_start": test_start.strftime("%Y-%m-%d"),
        "mae_last5_classical": evaluate_mae(frame, "price_pred_classical", last_five_start, frame["date"].max()),
        "mae_last5_quantum": evaluate_mae(frame, f"price_pred_{mode_quantum}", last_five_start, frame["date"].max()),
        "mae_last5_blend": evaluate_mae(frame, "price_pred_blend", last_five_start, frame["date"].max()),
        "mae_test_classical": evaluate_mae(frame, "price_pred_classical", test_start, frame["date"].max()),
        "mae_test_quantum": evaluate_mae(frame, f"price_pred_{mode_quantum}", test_start, frame["date"].max()),
        "mae_test_blend": evaluate_mae(frame, "price_pred_blend", test_start, frame["date"].max()),
    }

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    asset_label = metrics_path.parent.name
    out_path = output_dir / f"{asset_label}_{mode_quantum}_blend.json"
    out_path.write_text(json.dumps(comparison, indent=2), encoding="utf-8")

    print(f"Alpha otimizado ({mode_quantum}): {alpha:.4f}")
    print(json.dumps(comparison, indent=2))


if __name__ == "__main__":
    main()
