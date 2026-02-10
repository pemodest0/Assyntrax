#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from engine.sanity import ensure_sorted_dates, split_hash, validate_time_split

from hybrid_forecast import (
    DEFAULT_FEATURES,
    apply_residual_model,
    evaluate_adjusted_predictions,
    load_metrics,
    prepare_residual_dataset,
    time_series_grid_search,
    train_residual_model,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Treina modelo residual para ajustar previsÃµes de preÃ§o.")
    parser.add_argument(
        "--metrics",
        type=str,
        default="results/benchmark_2023/ibov_reconstructed/daily_forecast_metrics.csv",
        help="CSV com mÃ©tricas diÃ¡rias (previsto/real).",
    )
    parser.add_argument("--start", type=str, default="2016-01-01", help="InÃ­cio da janela de treino.")
    parser.add_argument("--train-end", type=str, default="2023-12-31", help="Data limite para treino.")
    parser.add_argument("--test-start", type=str, default="2024-01-01", help="InÃ­cio da janela de teste.")
    parser.add_argument("--model", choices=("gbr", "rf"), default="gbr", help="Regressor residual.")
    parser.add_argument("--output", type=str, default="results/hybrid_residual", help="DiretÃ³rio de saÃ­da.")
    parser.add_argument("--tune", action="store_true", help="Efetua busca em grade com validaÃ§Ã£o temporal antes do treino.")
    parser.add_argument("--tune-splits", type=int, default=3, help="NÃºmero de divisÃµes de TimeSeriesSplit ao tunar.")
    parser.add_argument(
        "--calibration-days",
        type=int,
        default=252,
        help="NÃºmero de dias mais recentes do perÃ­odo de treino usados para calibrar o peso do residual.",
    )
    parser.add_argument(
        "--target-mode",
        choices=("points", "pct"),
        default="points",
        help="Escala do alvo residual (pontos absolutos ou percentual).",
    )
    args = parser.parse_args()

    path = Path(args.metrics)
    df = load_metrics(path, start=args.start)
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    ensure_sorted_dates(df["date"])

    # ensure derived columns exist
    if "price_residual" not in df.columns:
        df["price_residual"] = df["price_real"] - df["price_pred"]
    if "expected_minus_actual" not in df.columns:
        df["expected_minus_actual"] = df["expected_return"] - df["actual_return"]
    if "error_abs" not in df.columns:
        df["error_abs"] = (df["price_pred"] - df["price_real"]).abs()
    if "error_pct_abs" not in df.columns:
        df["error_pct_abs"] = (
            (df["price_pred"] - df["price_real"]).abs() / df["price_real"].clip(lower=1e-6)
        )
    group = df.groupby("symbol", group_keys=False)
    for col in ("expected_return", "vol_ratio", "noise_used"):
        for lag in (1, 2):
            name = f"{col}_lag{lag}"
            if name not in df.columns:
                df[name] = group[col].shift(lag)
    if "rolling_alpha_mean_5" not in df.columns:
        df["rolling_alpha_mean_5"] = group["alpha"].transform(lambda x: x.rolling(5, min_periods=1).mean())
    if "rolling_entropy_mean_5" not in df.columns:
        df["rolling_entropy_mean_5"] = group["entropy"].transform(lambda x: x.rolling(5, min_periods=1).mean())
    if "rolling_vol_ratio_mean_5" not in df.columns:
        df["rolling_vol_ratio_mean_5"] = group["vol_ratio"].transform(lambda x: x.rolling(5, min_periods=1).mean())
    df = df.ffill().bfill()

    dataset = prepare_residual_dataset(df, DEFAULT_FEATURES, target_scaling=args.target_mode)
    dataset.frame.sort_values("date", inplace=True)
    dataset.frame.reset_index(drop=True, inplace=True)
    ensure_sorted_dates(dataset.frame["date"])
    train_mask = dataset.frame["date"] <= pd.Timestamp(args.train_end)
    test_mask = dataset.frame["date"] >= pd.Timestamp(args.test_start)
    validate_time_split(
        dataset.frame["date"],
        train_mask.values,
        test_mask.values,
        train_end=pd.Timestamp(args.train_end),
        test_start=pd.Timestamp(args.test_start),
    )

    best_params = None
    tune_score = None
    mask_values = train_mask.values

    if args.tune:
        if args.model == "gbr":
            param_grid = {
                "learning_rate": [0.02, 0.03, 0.05],
                "n_estimators": [200, 400, 600],
                "max_depth": [2, 3],
                "subsample": [0.6, 0.8],
            }
        else:
            param_grid = {
                "n_estimators": [200, 400, 600],
                "max_depth": [None, 6, 10],
            }
        best_params, tune_score = time_series_grid_search(
            dataset, param_grid, model_type=args.model, n_splits=args.tune_splits
        )
        print(f"Melhor conjunto de parÃ¢metros: {best_params} (MAE={tune_score:.4f})")

    reg, scaler, metrics = train_residual_model(
        dataset, train_mask=mask_values, model=args.model, model_params=best_params
    )
    explain_dir = Path(args.output) / "explainability" if args.tune else None

    if args.calibration_days > 0:
        cutoff = pd.Timestamp(args.train_end) - pd.Timedelta(days=args.calibration_days)
        calibration_mask = (dataset.frame["date"] >= cutoff) & train_mask
        calibration_mask = calibration_mask.values
    else:
        calibration_mask = mask_values if train_mask is not None else None

    adjusted = apply_residual_model(
        dataset,
        reg,
        scaler,
        explainability_output=explain_dir,
        calibration_mask=calibration_mask,
    )

    eval_all = evaluate_adjusted_predictions(adjusted)
    test_mask = (adjusted["date"] >= pd.Timestamp(args.test_start)) & (
        adjusted["date"] <= pd.Timestamp(args.test_start).replace(year=pd.Timestamp(args.test_start).year + 1)
    )
    eval_test = evaluate_adjusted_predictions(adjusted.loc[test_mask].copy())

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    adjusted.to_csv(output_dir / "residual_adjusted_predictions.csv", index=False)

    calibration = adjusted.attrs.get("residual_calibration")

    summary = {
        "train_metrics": metrics,
        "evaluation_all": eval_all,
        "evaluation_test": eval_test,
        "train_records": int(train_mask.sum()),
        "test_records": int(test_mask.sum()),
        "train_end": pd.Timestamp(args.train_end).date().isoformat(),
        "test_start": pd.Timestamp(args.test_start).date().isoformat(),
        "split_hash": split_hash(
            np.where(train_mask.values)[0], np.where(test_mask.values)[0]
        ),
        "feature_count": len(DEFAULT_FEATURES),
        "tuning": {
            "enabled": args.tune,
            "best_params": best_params,
            "validation_mae": tune_score,
        },
        "calibration": calibration,
        "target_mode": args.target_mode,
    }
    with (output_dir / "residual_metrics.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=float)

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

