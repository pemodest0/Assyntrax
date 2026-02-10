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
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from engine.sanity import ensure_sorted_dates, split_hash, validate_time_split

def load_metrics(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    if "mode" in df.columns:
        df = df[df["mode"] == "classical"].copy()
    return df


def _detect_asset_label(metrics_path: Path) -> str:
    parent = metrics_path.parent.name
    if parent:
        return parent
    return metrics_path.stem


def _select_feature_columns(df: pd.DataFrame, target_col: str, target_kind: str) -> Tuple[pd.DataFrame, List[str]]:
    numeric_df = df.select_dtypes(include=[np.number]).copy()
    leak_cols = {"error_pct", "error_scale", "direction_match", "blend_abs_error", "blend_abs_error_pct"}
    if target_kind == "price":
        leak_cols.update({"price_real", "actual_return"})
    else:
        leak_cols.update({"actual_return"})
    columns = [col for col in numeric_df.columns if col not in leak_cols and col != target_col]
    return numeric_df[columns], columns


def _build_preprocessor(feature_names: List[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    return ColumnTransformer(transformers=[("num", numeric_pipeline, feature_names)])


def _evaluate_models(
    X_train,
    y_train,
    X_test,
    y_test,
    models: Dict[str, object],
) -> Dict[str, Dict[str, float]]:
    results: Dict[str, Dict[str, float]] = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred_train = model.predict(X_train)
        pred_test = model.predict(X_test)
        results[name] = {
            "train_mae": float(mean_absolute_error(y_train, pred_train)),
            "test_mae": float(mean_absolute_error(y_test, pred_test)),
            "train_mape": float(mean_absolute_percentage_error(np.maximum(np.abs(y_train), 1e-6), np.maximum(np.abs(pred_train), 1e-6))),
            "test_mape": float(mean_absolute_percentage_error(np.maximum(np.abs(y_test), 1e-6), np.maximum(np.abs(pred_test), 1e-6))),
            "train_r2": float(r2_score(y_train, pred_train)),
            "test_r2": float(r2_score(y_test, pred_test)),
            "train_predictions": pred_train,
            "test_predictions": pred_test,
        }
    return results


def _baseline_metrics(target_kind: str, df_test: pd.DataFrame, y_test: pd.Series) -> Dict[str, float]:
    if target_kind == "price":
        baseline_series = df_test["price_pred"]
    else:
        baseline_series = df_test["expected_return"]
    mae = float(mean_absolute_error(y_test, baseline_series))
    mape = float(mean_absolute_percentage_error(np.maximum(np.abs(y_test), 1e-6), np.maximum(np.abs(baseline_series), 1e-6)))
    return {"baseline_mae": mae, "baseline_mape": mape}


def main() -> None:
    np.random.seed(42)
    parser = argparse.ArgumentParser(description="Treina regressÃµes tradicionais para corrigir previsÃµes clÃ¡ssicas/quÃ¢nticas.")
    parser.add_argument("metrics", type=str, help="Arquivo daily_forecast_metrics.csv (modo clÃ¡ssico).")
    parser.add_argument("--target", type=str, choices=("price", "return"), default="price", help="Seleciona o alvo (preÃ§o ou retorno log).")
    parser.add_argument("--train-end", type=str, default="2023-12-31", help="Data de corte para treino (inclusive).")
    parser.add_argument("--start", type=str, default=None, help="Data inicial filtrada (opcional).")
    parser.add_argument("--end", type=str, default=None, help="Data final filtrada (opcional).")
    parser.add_argument("--output", type=str, default="results/ml_forecast", help="DiretÃ³rio de saÃ­da.")
    args = parser.parse_args()

    metrics_path = Path(args.metrics)
    df = load_metrics(metrics_path)
    if df["date"].dt.tz is not None:
        df["date"] = df["date"].dt.tz_convert("UTC").dt.tz_localize(None)
    if args.start:
        df = df[df["date"] >= pd.Timestamp(args.start)]
    if args.end:
        df = df[df["date"] <= pd.Timestamp(args.end)]
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    ensure_sorted_dates(df["date"])

    target_col = "price_real" if args.target == "price" else "actual_return"
    if target_col not in df.columns:
        raise ValueError(f"Coluna alvo {target_col} nÃ£o encontrada.")

    features_df, feature_cols = _select_feature_columns(df, target_col, args.target)
    y = df[target_col].astype(float)

    train_end = pd.Timestamp(args.train_end)
    mask_train = df["date"] <= train_end
    if mask_train.sum() == 0 or (~mask_train).sum() == 0:
        raise ValueError("Datas insuficientes para treino/teste com o corte fornecido.")
    mask_test = ~mask_train
    validate_time_split(df["date"], mask_train, mask_test, train_end=train_end)

    preprocessor = _build_preprocessor(feature_cols)
    X_train = preprocessor.fit_transform(features_df[mask_train])
    X_test = preprocessor.transform(features_df[mask_test])
    y_train, y_test = y[mask_train], y[~mask_train]
    df_test = df[~mask_train].copy()

    models = {
        "gradient_boosting": GradientBoostingRegressor(random_state=42, n_estimators=800, learning_rate=0.03, max_depth=3, subsample=0.8),
        "hist_gradient_boosting": HistGradientBoostingRegressor(random_state=42, learning_rate=0.03, max_depth=7, max_bins=255),
        "random_forest": RandomForestRegressor(random_state=42, n_estimators=500, min_samples_leaf=2, n_jobs=-1),
    }

    model_results = _evaluate_models(X_train, y_train, X_test, y_test, models)
    baseline = _baseline_metrics(args.target, df_test, y_test)

    predictions = df[["date"]].copy()
    predictions["target_true"] = y
    for name, info in model_results.items():
        pred = np.concatenate([info["train_predictions"], info["test_predictions"]])
        info.pop("train_predictions")
        info.pop("test_predictions")
        predictions[f"{name}_pred"] = pred
    predictions["split"] = np.where(mask_train, "train", "test")

    asset_label = _detect_asset_label(metrics_path)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "asset": asset_label,
        "target": args.target,
        "train_end": train_end.date().isoformat(),
        "split_hash": split_hash(np.where(mask_train)[0], np.where(mask_test)[0]),
        "train_samples": int(mask_train.sum()),
        "test_samples": int((~mask_train).sum()),
        "baseline": baseline,
        "models": {name: {k: v for k, v in metrics.items()} for name, metrics in model_results.items()},
    }

    summary_path = output_dir / f"{asset_label}_{args.target}_ml_summary.json"
    prediction_path = output_dir / f"{asset_label}_{args.target}_ml_predictions.csv"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    predictions.to_csv(prediction_path, index=False)
    print(f"Resumo salvo em {summary_path}")
    print(f"PrediÃ§Ãµes salvas em {prediction_path}")


if __name__ == "__main__":
    main()

