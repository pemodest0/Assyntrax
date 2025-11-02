#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from explainability import ExplainabilityHelper, SHAP_AVAILABLE


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera artefatos de explainability (importances e SHAP).")
    parser.add_argument("metrics", type=str, help="CSV daily_forecast_metrics gerado pelo pipeline.")
    parser.add_argument("model", type=str, help="Arquivo .joblib contendo (model, scaler).")
    parser.add_argument("output", type=str, help="Diretório de saída.")
    parser.add_argument("features", nargs="*", help="Lista de features a usar; padrão usa todas numéricas.")
    parser.add_argument("--sample", type=int, default=200, help="Número de registros para SHAP (0 = todos).")
    args = parser.parse_args()

    import joblib  # type: ignore

    metrics_path = Path(args.metrics)
    model_path = Path(args.model)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(metrics_path)
    features = args.features or [
        col for col in df.columns if col not in {"date", "price_real", "price_pred", "symbol", "mode"}
    ]
    X = df[features].replace([np.inf, -np.inf], np.nan).fillna(method="ffill").fillna(method="bfill").fillna(0.0)
    bundle = joblib.load(model_path)
    if isinstance(bundle, tuple):
        model, scaler = bundle
    else:
        model, scaler = bundle, None

    helper = ExplainabilityHelper(features)
    helper.export_feature_importance(model, output_dir / "feature_importance.csv")

    if not SHAP_AVAILABLE:
        print("[WARN] shap não disponível; pulei geração de SHAP plots.")
        return

    sample_size = args.sample if args.sample > 0 else len(X)
    sample = X.iloc[:sample_size].to_numpy()
    helper.save_shap_summary(model, sample, output_dir / "shap_summary.png", scaler=scaler)


if __name__ == "__main__":
    main()
