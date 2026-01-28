#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from spa.sanity import ensure_sorted_dates, split_hash, validate_time_split

def load_metrics(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    if df["date"].dt.tz is not None:
        df["date"] = df["date"].dt.tz_convert("UTC").dt.tz_localize(None)
    return df[df["mode"] == "classical"].copy()


def prepare_dataset(
    df: pd.DataFrame,
    mode: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    train_end: pd.Timestamp,
) -> Tuple[
    np.ndarray,
    pd.Series,
    np.ndarray,
    pd.Series,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    Tuple[str, ...],
    str,
]:
    col_pred = f"{mode}_price_pred"
    if col_pred not in df.columns:
        raise ValueError(
            f"Coluna {col_pred} não encontrada. Reexecute run_daily_forecast.py com backend quântico."
        )

    df = df[(df["date"] >= start) & (df["date"] <= end)].copy()
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    ensure_sorted_dates(df["date"])
    diff = df[col_pred] - df["price_pred"]
    residual = df["price_real"] - df["price_pred"]
    mask = diff.abs() > 1e-8
    df = df[mask].copy()
    diff = diff[mask]
    residual = residual[mask]

    raw_alpha = residual / diff
    df["alpha_target"] = raw_alpha.clip(-2.0, 2.0)

    feature_cols = [
        "expected_return",
        "alpha",
        "entropy",
        "vol_ratio",
        "vol_ewm_30",
        "abs_return_short",
        "drawdown_long",
        "vol_of_vol",
        "expected_return_lag1",
        "expected_return_lag2",
        "vol_ratio_lag1",
        "vol_ratio_lag2",
        "noise_used",
        f"{mode}_expected_return",
        f"{mode}_alpha",
        f"{mode}_entropy",
        f"{mode}_delta_price",
    ]

    available = [c for c in feature_cols if c in df.columns]
    X = df[available].replace([np.inf, -np.inf], np.nan).fillna(0.0)

    mask_train = df["date"] <= train_end
    validate_time_split(df["date"], mask_train, ~mask_train, train_end=train_end)

    phase = df["phase"].fillna("indefinido").to_numpy().reshape(-1, 1)
    ohe = OneHotEncoder(sparse=False, handle_unknown="ignore")
    ohe.fit(phase[mask_train])
    phase_ohe = ohe.transform(phase)
    phase_df = pd.DataFrame(
        phase_ohe,
        columns=[f"phase_{cat}" for cat in ohe.categories_[0]],
        index=X.index,
    )
    X = pd.concat([X, phase_df], axis=1)

    y = df["alpha_target"].astype(float)

    X_train, X_test = X[mask_train], X[~mask_train]
    y_train, y_test = y[mask_train], y[~mask_train]

    dataset = pd.concat(
        [
            df[["date", "price_pred", col_pred, "price_real", "phase"]],
            X,
        ],
        axis=1,
    )
    dataset["alpha_target"] = y
    dataset["split"] = np.where(mask_train, "train", "test")

    meta_train = dataset[dataset["split"] == "train"][["date", "price_pred", col_pred, "price_real"]]
    meta_test = dataset[dataset["split"] == "test"][["date", "price_pred", col_pred, "price_real"]]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    return (
        X_train_scaled,
        y_train,
        X_test_scaled,
        y_test,
        meta_train,
        meta_test,
        dataset,
        tuple(X.columns),
        col_pred,
    )


def evaluate_blend(alpha_pred: np.ndarray, meta: pd.DataFrame, mode: str) -> Dict[str, float]:
    c_pred = meta["price_pred"].to_numpy()
    q_pred = meta[f"{mode}_price_pred"].to_numpy()
    true = meta["price_real"].to_numpy()
    blend_pred = c_pred + alpha_pred * (q_pred - c_pred)
    mae = float(mean_absolute_error(true, blend_pred))
    mae_pct = float(np.mean(np.abs(blend_pred - true) / np.maximum(np.abs(true), 1e-6)) * 100.0)
    return {"mae": mae, "mae_pct": mae_pct}


def main() -> None:
    np.random.seed(42)
    parser = argparse.ArgumentParser(description="Treina regressão para blend quântico dinâmico.")
    parser.add_argument("metrics", type=str, help="Arquivo daily_forecast_metrics.csv.")
    parser.add_argument("--mode", type=str, default="quantum_hadamard", help="Modo quântico (quantum_hadamard ou quantum_grover).")
    parser.add_argument("--start", type=str, default="2015-01-01", help="Data inicial.")
    parser.add_argument("--end", type=str, default="2025-12-31", help="Data final.")
    parser.add_argument("--train-end", type=str, default="2023-12-31", help="Data limite do treino.")
    parser.add_argument("--output", type=str, default="results/crypto_blend", help="Diretório de saída.")
    parser.add_argument("--n-estimators", type=int, default=400, help="Número de árvores do Gradient Boosting.")
    parser.add_argument("--learning-rate", type=float, default=0.05, help="Learning rate do Gradient Boosting.")
    parser.add_argument("--max-depth", type=int, default=3, help="Profundidade máxima das árvores.")
    args = parser.parse_args()

    metrics_path = Path(args.metrics)
    df = load_metrics(metrics_path)
    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)
    train_end = pd.Timestamp(args.train_end)

    (
        X_train,
        y_train,
        X_test,
        y_test,
        meta_train,
        meta_test,
        dataset,
        feature_names,
        quantum_col,
    ) = prepare_dataset(
        df,
        args.mode,
        start,
        end,
        train_end,
    )

    if meta_train.empty or meta_test.empty:
        raise ValueError("Conjunto de treino ou teste vazio após os filtros selecionados; ajuste --train-end ou período.")

    reg = GradientBoostingRegressor(
        random_state=42,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        learning_rate=args.learning_rate,
    )
    reg.fit(X_train, y_train)

    y_pred_train = reg.predict(X_train)
    y_pred_test = reg.predict(X_test)

    result = {
        "alpha_stats": {
            "train_mae": float(mean_absolute_error(y_train, y_pred_train)),
            "test_mae": float(mean_absolute_error(y_test, y_pred_test)),
            "train_mean": float(y_pred_train.mean()),
            "test_mean": float(y_pred_test.mean()),
        },
        "blend_train": evaluate_blend(y_pred_train, meta_train, args.mode),
        "blend_test": evaluate_blend(y_pred_test, meta_test, args.mode),
        "baseline_classical": evaluate_blend(np.zeros_like(y_pred_test), meta_test, args.mode),
        "baseline_quantum": evaluate_blend(np.ones_like(y_pred_test), meta_test, args.mode),
        "n_train": int(y_train.shape[0]),
        "n_test": int(y_test.shape[0]),
        "train_end": train_end.date().isoformat(),
        "split_hash": split_hash(
            np.where(dataset["split"] == "train")[0], np.where(dataset["split"] == "test")[0]
        ),
        "feature_columns": list(feature_names),
    }

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    asset_label = metrics_path.parent.name

    dataset_export = dataset.copy()
    dataset_export["alpha_target"] = dataset_export["alpha_target"].astype(float)
    dataset_export["date"] = pd.to_datetime(dataset_export["date"])
    if dataset_export["date"].dt.tz is not None:
        dataset_export["date"] = dataset_export["date"].dt.tz_convert("UTC").dt.tz_localize(None)

    alpha_pred_series = pd.Series(index=dataset_export.index, dtype=float)
    train_mask = dataset_export["split"] == "train"
    test_mask = dataset_export["split"] == "test"
    alpha_pred_series.loc[train_mask] = y_pred_train
    alpha_pred_series.loc[test_mask] = y_pred_test
    dataset_export["alpha_pred"] = alpha_pred_series

    delta_quantum = dataset_export[quantum_col] - dataset_export["price_pred"]
    dataset_export["blend_price_pred"] = dataset_export["price_pred"] + dataset_export["alpha_pred"] * delta_quantum
    dataset_export["classical_abs_error"] = np.abs(dataset_export["price_pred"] - dataset_export["price_real"])
    dataset_export["quantum_abs_error"] = np.abs(dataset_export[quantum_col] - dataset_export["price_real"])
    dataset_export["blend_abs_error"] = np.abs(dataset_export["blend_price_pred"] - dataset_export["price_real"])
    dataset_export["blend_abs_error_pct"] = (
        dataset_export["blend_abs_error"] / np.maximum(np.abs(dataset_export["price_real"]), 1e-6)
    ) * 100.0

    predictions_export = dataset_export[
        [
            "date",
            "split",
            "price_real",
            "price_pred",
            quantum_col,
            "alpha_target",
            "alpha_pred",
            "blend_price_pred",
            "blend_abs_error",
            "blend_abs_error_pct",
        ]
    ].copy()

    dataset_path = output_dir / f"{asset_label}_{args.mode}_blend_dataset.csv"
    predictions_path = output_dir / f"{asset_label}_{args.mode}_dynamic_blend_predictions.csv"
    report_path = output_dir / f"{asset_label}_{args.mode}_dynamic_blend.json"

    dataset_export.to_csv(dataset_path, index=False)
    predictions_export.to_csv(predictions_path, index=False)
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
