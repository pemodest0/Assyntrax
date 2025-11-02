#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler


def load_dataset(path: Path, feature_cols=None):
    df = pd.read_csv(path, parse_dates=['date'])
    df.sort_values('date', inplace=True)
    if feature_cols is None:
        ignore = {'date', 'symbol', 'mode', 'mode_label', 'phase', 'return_mode'}
        feature_cols = [col for col in df.columns if col not in ignore]
    features = df[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(method='ffill').fillna(method='bfill').fillna(0.0)
    numeric_cols = [col for col in features.columns if pd.api.types.is_numeric_dtype(features[col])]
    features = features[numeric_cols]
    baseline_price = df['price_pred'].astype(float) if 'price_pred' in df.columns else df['price_today'].astype(float)
    features = features.drop(columns=['price_real', 'price_pred'], errors='ignore')
    target = (df['price_real'] - baseline_price).astype(float)
    valid_mask = baseline_price.notna() & target.notna()
    features = features.loc[valid_mask].copy()
    target = target.loc[valid_mask].copy()
    baseline_price = baseline_price.loc[valid_mask].copy()
    return df, features, target, feature_cols, baseline_price


def evaluate_models(
    features: pd.DataFrame,
    baseline: pd.Series,
    target: pd.Series,
    n_splits: int = 3,
):
    tscv = TimeSeriesSplit(n_splits=n_splits)
    results = {
        'naive': {'pred': [], 'true': []},
        'linear': {'pred': [], 'true': []},
        'random_forest': {'pred': [], 'true': []},
        'gboost': {'pred': [], 'true': []},
    }

    for train_idx, test_idx in tscv.split(features):
        X_train, X_test = features.iloc[train_idx], features.iloc[test_idx]
        y_train, y_test = target.iloc[train_idx], target.iloc[test_idx]
        baseline_train = baseline.iloc[train_idx]
        baseline_test = baseline.iloc[test_idx]

        # naive baseline: usar a previsão original (residual zero)
        results['naive']['pred'].extend(baseline_test.to_list())
        results['naive']['true'].extend((baseline_test + y_test).to_list())

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)

        models = {
            'linear': LinearRegression(),
            'random_forest': RandomForestRegressor(n_estimators=150, max_depth=8, random_state=42, n_jobs=-1),
            'gboost': GradientBoostingRegressor(random_state=42, n_estimators=150, max_depth=3, learning_rate=0.05),
        }

        for key, model in models.items():
            model.fit(X_train_scaled, y_train)
            preds_residual = model.predict(X_test_scaled)
            preds = baseline_test + preds_residual
            results[key]['pred'].extend(preds)
            results[key]['true'].extend((baseline_test + y_test).to_list())

    summary = {}
    for key, stats in results.items():
        y_true = np.array(stats['true'], dtype=float)
        y_pred = np.array(stats['pred'], dtype=float)
        summary[key] = {
            'mae': float(mean_absolute_error(y_true, y_pred)),
            'rmse': float(mean_squared_error(y_true, y_pred, squared=False)),
        }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara modelos de previsão em walk-forward.")
    parser.add_argument('metrics', type=str, help='Arquivo daily_forecast_metrics.csv')
    parser.add_argument('--output', type=str, default='results/model_comparison', help='Diretório de saída')
    parser.add_argument('--splits', type=int, default=3, help='N de splits no TimeSeriesSplit')
    args = parser.parse_args()

    metrics_path = Path(args.metrics)
    if not metrics_path.exists():
        raise SystemExit(f"Metrics não encontrado: {metrics_path}")

    df, features, target, feature_cols, baseline = load_dataset(metrics_path)
    summary = evaluate_models(features, baseline, target, n_splits=args.splits)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    asset_label = metrics_path.parent.name
    report_path = output_dir / f"{asset_label}_comparison.json"
    with report_path.open('w', encoding='utf-8') as fh:
        json.dump({'features': feature_cols, 'summary': summary}, fh, indent=2)

    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
