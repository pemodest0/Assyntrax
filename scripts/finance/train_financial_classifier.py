#!/usr/bin/env python3
import os
import sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from spa.sanity import ensure_sorted_dates, split_hash, validate_time_split

try:
    import seaborn as sns
except ImportError:  # pragma: no cover - seaborn is optional
    sns = None

from sklearn.metrics import accuracy_score, precision_recall_fscore_support

from financial_classifier import (
    augment_with_derived_features,
    evaluate_direction_classifier,
    load_financial_metrics,
    prepare_features,
    save_metrics,
    split_train_test,
    train_direction_classifier,
)


DEFAULT_FEATURES = [
    "expected_return",
    "actual_return",
    "alpha",
    "entropy",
    "vol_realized_short",
    "vol_realized_long",
    "vol_ratio",
    "vol_ewm_30",
    "abs_return_short",
    "drawdown_long",
    "vol_of_vol",
    "noise_used",
    "expected_minus_actual",
    "error_abs",
    "error_pct_abs",
    "rolling_alpha_mean_5",
    "rolling_entropy_mean_5",
    "rolling_vol_ratio_mean_5",
    "expected_return_lag1",
    "expected_return_lag2",
    "vol_ratio_lag1",
    "vol_ratio_lag2",
    "noise_used_lag1",
]


def _plot_confusion_matrix(confusion: np.ndarray, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(5, 4))
    if sns is not None:
        sns.heatmap(confusion, annot=True, fmt="d", cmap="Blues", cbar=False, ax=ax)
    else:
        im = ax.imshow(confusion, cmap="Blues")
        for (i, j), val in np.ndenumerate(confusion):
            ax.text(j, i, f"{val:d}", ha="center", va="center", color="black")
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_xlabel("Predito")
    ax.set_ylabel("Real")
    ax.set_title("Matriz de confusão — direção")
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def _plot_feature_importance(importances: dict, output: Path) -> None:
    items = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    names = [name for name, _ in items]
    values = [val for _, val in items]
    fig, ax = plt.subplots(figsize=(8, 4))
    if sns is not None:
        sns.barplot(x=values, y=names, ax=ax, palette="viridis")
    else:
        ax.barh(names, values, color="steelblue")
    ax.set_title("Importância das features")
    ax.set_xlabel("Importância (RandomForest)")
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def _plot_probability_distributions(proba: np.ndarray, y_true: np.ndarray, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    if sns is not None:
        sns.kdeplot(proba[y_true == 1], label="Acertou direção", fill=True, alpha=0.4, ax=ax)
        sns.kdeplot(proba[y_true == 0], label="Errou direção", fill=True, alpha=0.4, ax=ax)
    else:
        ax.hist(proba[y_true == 1], bins=15, density=True, alpha=0.5, label="Acertou direção")
        ax.hist(proba[y_true == 0], bins=15, density=True, alpha=0.5, label="Errou direção")
    ax.set_xlabel("Probabilidade predita (classe=1)")
    ax.set_ylabel("Densidade")
    ax.set_title("Distribuição das probabilidades previstas")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=200)
    plt.close(fig)


def _compute_rolling_metrics(test_df: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    df = test_df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df.set_index("date", inplace=True)
    rows: List[Dict[str, object]] = []
    for period, group in df.groupby(pd.Grouper(freq=freq)):
        if group.empty:
            continue
        y_true = group["y_true"].to_numpy()
        y_pred = group["y_pred"].to_numpy()
        proba = group["proba"].to_numpy()
        accuracy = accuracy_score(y_true, y_pred)
        precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary")
        row = {
            "period": period.strftime("%Y-%m") if isinstance(period, pd.Timestamp) else str(period),
            "records": int(group.shape[0]),
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
            "coverage_p60": float((proba >= 0.6).mean()),
            "coverage_p80": float((proba >= 0.8).mean()),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Treina classificador de direção (acerto vs erro) usando features diárias.")
    parser.add_argument(
        "--metrics",
        nargs="+",
        default=[
            "results/benchmark_2023/spy_stooq/daily_forecast_metrics.csv",
            "results/benchmark_2023/ibov_reconstructed/daily_forecast_metrics.csv",
        ],
        help="Arquivos CSV de métricas diárias.",
    )
    parser.add_argument("--start", type=str, default="2019-01-01", help="Data inicial (YYYY-MM-DD).")
    parser.add_argument("--end", type=str, default="2023-12-31", help="Data final (YYYY-MM-DD).")
    parser.add_argument(
        "--test-start",
        type=str,
        default="2023-01-01",
        help="Data de corte para teste (tudo a partir dessa data vai para o conjunto de teste).",
    )
    parser.add_argument("--output", type=str, default="results/classifier_finance", help="Diretório de saída.")
    parser.add_argument("--features", nargs="+", default=DEFAULT_FEATURES, help="Lista de colunas de features.")
    parser.add_argument("--trees", type=int, default=400, help="Número de árvores no RandomForest.")
    parser.add_argument("--max-depth", type=int, default=None, help="Profundidade máxima do RandomForest.")
    parser.add_argument(
        "--model", type=str, default="rf", choices=("rf", "gb", "logistic"), help="Modelo supervisionado a utilizar."
    )
    parser.add_argument(
        "--calibrate",
        action="store_true",
        help="Ajusta probabilidades com Platt scaling (LogisticRegression) usando os dados de teste.",
    )
    parser.add_argument(
        "--mismatch-weight",
        type=float,
        default=1.5,
        help="Peso adicional para amostras onde direction_match=0 (erros).",
    )
    parser.add_argument("--difusiva-weight", type=float, default=1.2, help="Peso extra para regime difusivo.")
    parser.add_argument("--transicao-weight", type=float, default=1.0, help="Peso extra para regime de transição.")
    parser.add_argument("--coerente-weight", type=float, default=1.0, help="Peso extra para regime coerente.")
    parser.add_argument(
        "--rolling-freq",
        type=str,
        default="M",
        help="Frequência para métricas agregadas (ex: 'M' mensal, 'W' semanal).",
    )
    args = parser.parse_args()

    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)
    test_start = pd.Timestamp(args.test_start)

    paths = [Path(p) for p in args.metrics]
    df = load_financial_metrics(paths, start=start, end=end)
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    ensure_sorted_dates(df["date"])
    df = augment_with_derived_features(df)
    dataset = prepare_features(df, args.features)
    X_train, X_test, y_train, y_test, train_idx, test_idx = split_train_test(
        dataset, df["date"], test_start=test_start
    )
    train_mask = np.zeros(len(df), dtype=bool)
    test_mask = np.zeros(len(df), dtype=bool)
    train_mask[train_idx] = True
    test_mask[test_idx] = True
    validate_time_split(df["date"], train_mask, test_mask, test_start=test_start)

    train_meta = dataset.meta.iloc[train_idx].copy()
    sample_weight = np.ones_like(y_train, dtype=float)
    if args.mismatch_weight != 1.0:
        sample_weight[y_train == 0] *= args.mismatch_weight
    if "phase" in train_meta.columns:
        phase_weights = {
            "difusiva": args.difusiva_weight,
            "transicao": args.transicao_weight,
            "coerente": args.coerente_weight,
        }
        phases = train_meta["phase"].fillna("indefinido")
        for phase, weight in phase_weights.items():
            if weight != 1.0:
                sample_weight[phases == phase] *= weight

    clf, scaler = train_direction_classifier(
        X_train,
        y_train,
        model_type=args.model,
        n_estimators=args.trees,
        max_depth=args.max_depth,
        sample_weight=sample_weight,
    )
    metrics = evaluate_direction_classifier(clf, scaler, X_test, y_test, args.features)
    output_dir = Path(args.output)
    save_metrics(metrics, output_dir)

    proba = np.asarray(metrics["probabilities"], dtype=float)
    y_pred = np.asarray(metrics["predictions"], dtype=int)
    test_results = dataset.meta.iloc[test_idx].copy()
    test_results["y_true"] = y_test
    test_results["y_pred"] = y_pred
    test_results["proba"] = proba
    test_results.sort_values("date", inplace=True)
    test_results.to_csv(output_dir / "test_predictions.csv", index=False)

    _plot_confusion_matrix(np.array(metrics["confusion_matrix"]), output_dir / "confusion_matrix.png")
    _plot_feature_importance(metrics["feature_importances"], output_dir / "feature_importance.png")
    _plot_probability_distributions(proba, y_test, output_dir / "probabilities.png")

    rolling_df = _compute_rolling_metrics(test_results, freq=args.rolling_freq)
    rolling_df.to_csv(output_dir / "rolling_metrics.csv", index=False)

    if "phase" in test_results.columns:
        phase_rows = []
        for phase, group in test_results.groupby("phase"):
            if group.empty:
                continue
            accuracy = accuracy_score(group["y_true"], group["y_pred"])
            precision, recall, f1, _ = precision_recall_fscore_support(
                group["y_true"], group["y_pred"], average="binary"
            )
            phase_rows.append(
                {
                    "phase": phase,
                    "records": group.shape[0],
                    "accuracy": accuracy,
                    "precision": precision,
                    "recall": recall,
                    "f1": f1,
                    "coverage_p60": (group["proba"] >= 0.6).mean(),
                }
            )
        pd.DataFrame(phase_rows).to_csv(output_dir / "phase_metrics.csv", index=False)

    summary_path = output_dir / "metrics_summary.txt"
    with summary_path.open("w", encoding="utf-8") as fh:
        fh.write("Direction classifier metrics (test set)\n")
        fh.write(f"split_hash: {split_hash(np.array(train_idx), np.array(test_idx))}\n")
        fh.write(json.dumps(metrics, indent=2))

    print(f"Model metrics saved under {output_dir}")


if __name__ == "__main__":
    main()
