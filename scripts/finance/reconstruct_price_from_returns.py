#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd


def load_metrics(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    if "mode" in df.columns:
        df = df[df["mode"] == "classical"].copy()
    if df["date"].dt.tz is not None:
        df["date"] = df["date"].dt.tz_convert("UTC").dt.tz_localize(None)
    return df


def reconstruct_prices(return_preds: pd.DataFrame, model_cols: List[str], seed_price: float) -> Dict[str, np.ndarray]:
    prices = {col: np.zeros(len(return_preds)) for col in model_cols}
    prev_prices = {col: seed_price for col in model_cols}
    for idx in range(len(return_preds)):
        row = return_preds.iloc[idx]
        for col in model_cols:
            pred_ret = row.get(col, 0.0)
            if not np.isfinite(pred_ret):
                pred_ret = 0.0
            new_price = prev_prices[col] * float(np.exp(pred_ret))
            prices[col][idx] = new_price
            prev_prices[col] = new_price
    return prices


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconstrói preços a partir de previsões de retorno (log) e avalia MAE/MAPE.")
    parser.add_argument("metrics", type=str, help="Arquivo daily_forecast_metrics.csv (modo clássico).")
    parser.add_argument("predictions", type=str, help="Arquivo *_return_ml_predictions.csv gerado por train_ml_forecaster.py.")
    parser.add_argument("--train-end", type=str, default="2023-12-31", help="Data final do conjunto de treino.")
    parser.add_argument("--output", type=str, default="results/ml_forecast", help="Diretório para salvar avaliação.")
    args = parser.parse_args()

    metrics_path = Path(args.metrics)
    predictions_path = Path(args.predictions)

    df_metrics = load_metrics(metrics_path)
    df_pred = pd.read_csv(predictions_path, parse_dates=["date"])
    if df_pred["date"].dt.tz is not None:
        df_pred["date"] = df_pred["date"].dt.tz_convert("UTC").dt.tz_localize(None)
    df_pred.sort_values("date", inplace=True)
    df_pred.reset_index(drop=True, inplace=True)

    train_end = pd.Timestamp(args.train_end)
    split_mask = df_metrics["date"] <= train_end
    if split_mask.sum() == 0:
        raise ValueError("Conjunto de treino vazio; ajuste --train-end.")

    test_metrics = df_metrics[~split_mask].copy().reset_index(drop=True)
    test_predictions = df_pred[df_pred["split"] == "test"].copy().reset_index(drop=True)
    model_cols = [col for col in test_predictions.columns if col.endswith("_pred")]
    if not model_cols:
        raise ValueError("Nenhuma coluna *_pred encontrada no arquivo de predições.")

    last_train_price = float(df_metrics.loc[split_mask, "price_real"].iloc[-1])
    start_idx = split_mask.sum()
    recon = reconstruct_prices(test_predictions, model_cols, last_train_price)

    baseline_mae = float(np.mean(np.abs(test_metrics["price_real"].to_numpy() - test_metrics["price_pred"].to_numpy())))
    baseline_mape = float(np.mean(np.abs((test_metrics["price_real"].to_numpy() - test_metrics["price_pred"].to_numpy()) / np.maximum(np.abs(test_metrics["price_real"].to_numpy()), 1e-6))))

    records: List[dict] = []
    for col, series in recon.items():
        mae = float(np.mean(np.abs(test_metrics["price_real"].to_numpy() - series)))
        mape = float(np.mean(np.abs((test_metrics["price_real"].to_numpy() - series) / np.maximum(np.abs(test_metrics["price_real"].to_numpy()), 1e-6))))
        records.append(
            {
                "model": col,
                "mae": mae,
                "mape": mape,
                "gain_vs_classical_pct": (baseline_mae - mae) / baseline_mae * 100,
            }
        )
    summary = pd.DataFrame(records)
    asset = metrics_path.parent.name or metrics_path.stem
    summary["baseline_mae"] = baseline_mae
    summary["baseline_mape"] = baseline_mape
    output_path = Path(args.output) / f"{asset}_return_reconstruction_summary.csv"
    summary.to_csv(output_path, index=False)
    print(summary)
    print(f"Resumo salvo em {output_path}")


if __name__ == "__main__":
    main()
