#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from graph_engine.core import local_divergence  # noqa: E402
from graph_engine.embedding import estimate_embedding_params, takens_embed  # noqa: E402
from graph_engine.graph_builder import knn_edges, normalize_counts, transition_counts  # noqa: E402
from graph_engine.labels import (
    compute_confidence,
    compute_graph_quality,
    compute_thresholds,
    label_state,
)  # noqa: E402
from graph_engine.metastable import metastable_regimes  # noqa: E402


def load_series(path: Path, timeframe: str) -> Tuple[pd.Series, pd.DatetimeIndex]:
    df = pd.read_csv(path)
    date_col = "date" if "date" in df.columns else df.columns[0]
    col = "close" if "close" in df.columns else df.columns[-1]
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, col]).sort_values(date_col)
    if timeframe == "weekly":
        series = df.set_index(date_col)[col].astype(float).resample("W").last().dropna()
    else:
        series = df.set_index(date_col)[col].astype(float)
    return series, series.index


def _metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prev: np.ndarray, scale: float) -> Dict[str, float]:
    err = y_true - y_pred
    mae = float(np.mean(np.abs(err))) if err.size else float("nan")
    rmse = float(np.sqrt(np.mean(err * err))) if err.size else float("nan")
    mase = float(mae / max(scale, 1e-8)) if err.size else float("nan")
    dir_true = np.sign(y_true - y_prev)
    dir_pred = np.sign(y_pred - y_prev)
    dir_acc = float(np.mean(dir_true == dir_pred)) if err.size else float("nan")
    return {"mae": mae, "rmse": rmse, "mase": mase, "dir_acc": dir_acc}


def _year_slices(index: pd.DatetimeIndex) -> List[int]:
    years = sorted(set(index.year))
    return years


def backtest_series(
    series: pd.Series,
    timeframe: str,
    n_micro: int,
    n_regimes: int,
    k_nn: int,
    theiler: int,
    alpha: float,
    method: str,
    m: int,
    tau: int,
) -> Dict[str, any]:
    years = _year_slices(series.index)
    results = {}

    # scale for MASE uses full train sample per year
    for i in range(1, len(years)):
        year = years[i]
        train_end = pd.Timestamp(year=year - 1, month=12, day=31)
        train = series[series.index <= train_end]
        test = series[(series.index.year == year)]
        if len(train) < (m - 1) * tau + 5 or len(test) < 5:
            continue

        train_values = train.values.astype(float)
        test_values = test.values.astype(float)

        emb_train = takens_embed(train_values, m=m, tau=tau)
        km = KMeans(n_clusters=min(n_micro, max(20, len(emb_train) // 5)), random_state=7, n_init=10)
        train_labels = km.fit_predict(emb_train)
        centroids = km.cluster_centers_

        counts = transition_counts(train_labels)
        p_matrix = normalize_counts(counts, alpha=alpha)
        micro_regime = metastable_regimes(p_matrix, n_regimes=n_regimes, seed=7, method=method)

        # build embedding for full data up to test end
        full_series = pd.concat([train, test])
        full_values = full_series.values.astype(float)
        emb_full = takens_embed(full_values, m=m, tau=tau)
        aligned_index = full_series.index[(m - 1) * tau :]

        # assign microstates by nearest centroid
        nn = NearestNeighbors(n_neighbors=1).fit(centroids)
        micro_full = nn.kneighbors(emb_full, return_distance=False).ravel()

        conf_full = compute_confidence(p_matrix, micro_regime, micro_full)
        stretch, frac_pos = local_divergence(emb_full, theiler=theiler)
        if stretch.size > 0:
            lo = float(np.quantile(stretch, 0.05))
            hi = float(np.quantile(stretch, 0.95))
            stretch = np.clip(stretch, lo, hi)
        stretch_mu = np.pad(stretch, (0, 1), mode="edge")
        stretch_frac = np.pad(frac_pos, (0, 1), mode="edge")

        # thresholds from train only
        train_mask = aligned_index <= train_end
        escape_train = 1.0 - conf_full[train_mask]
        thresholds = compute_thresholds(escape_train, stretch_mu[train_mask], stretch_frac[train_mask])

        edges = knn_edges(centroids, k=k_nn)
        quality = compute_graph_quality(len(centroids), edges, np.bincount(train_labels, minlength=len(centroids)), p_matrix, {})

        # test mask within aligned index
        test_mask = (aligned_index.year == year)
        idx = np.where(test_mask)[0]
        if idx.size < 2:
            continue

        labels = []
        for j in idx:
            if quality["score"] < 0.3:
                labels.append("NOISY")
            else:
                labels.append(
                    label_state(
                        float(conf_full[j]),
                        float(stretch_mu[j]),
                        float(1.0 - conf_full[j]),
                        float(stretch_frac[j]),
                        thresholds,
                    )
                )

        # forecast: naive 1-step
        y = full_series.values.astype(float)
        y_prev = y[(m - 1) * tau :][test_mask]
        y_pred = y_prev.copy()
        y_true = np.roll(y_prev, -1)
        y_true = y_true[:-1]
        y_pred = y_pred[:-1]
        y_prev = y_prev[:-1]
        label_arr = np.array(labels[:-1])

        scale = float(np.mean(np.abs(np.diff(train_values)))) if len(train_values) > 1 else 1.0
        overall = _metrics(y_true, y_pred, y_prev, scale)

        by_regime = {}
        for reg in np.unique(label_arr):
            mask = label_arr == reg
            by_regime[str(reg)] = _metrics(y_true[mask], y_pred[mask], y_prev[mask], scale)

        results[str(year)] = {
            "overall": overall,
            "by_regime": by_regime,
        }

    # latest snapshot for UI
    last_window = series.tail(30)
    latest_pred = float(series.iloc[-1])
    latest = {
        "dates": [d.strftime("%Y-%m-%d") for d in last_window.index],
        "values": [float(v) for v in last_window.values],
        "forecast_next": latest_pred,
    }

    return {"by_year": results, "latest": latest}


def main() -> None:
    parser = argparse.ArgumentParser(description="Formal backtest by regime and asset.")
    parser.add_argument("--tickers", required=True, help="Comma-separated tickers")
    parser.add_argument("--timeframes", default="daily,weekly")
    parser.add_argument("--data-dir", default="data/raw/finance/yfinance_daily")
    parser.add_argument("--outdir", default="results/latest_graph/backtest")
    parser.add_argument("--n-micro", type=int, default=200)
    parser.add_argument("--n-regimes", type=int, default=4)
    parser.add_argument("--k-nn", type=int, default=10)
    parser.add_argument("--theiler", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=2.0)
    parser.add_argument("--method", default="spectral", choices=["spectral", "pcca"])
    parser.add_argument("--m", type=int, default=3)
    parser.add_argument("--tau", type=int, default=1)
    parser.add_argument("--auto-embed", action="store_true")
    parser.add_argument("--tau-method", default="ami", choices=["ami", "acf"])
    parser.add_argument("--m-method", default="cao", choices=["cao", "fnn"])
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    data_dir = Path(args.data_dir)

    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    tfs = [t.strip() for t in args.timeframes.split(",") if t.strip()]

    for ticker in tickers:
        csv_path = data_dir / f"{ticker}.csv"
        if not csv_path.exists():
            continue
        for tf in tfs:
            series, _ = load_series(csv_path, tf)
            if args.auto_embed:
                m_use, tau_use = estimate_embedding_params(series.values, tau_method=args.tau_method, m_method=args.m_method)
            else:
                m_use, tau_use = args.m, args.tau

            result = backtest_series(
                series,
                timeframe=tf,
                n_micro=args.n_micro,
                n_regimes=args.n_regimes,
                k_nn=args.k_nn,
                theiler=args.theiler,
                alpha=args.alpha,
                method=args.method,
                m=m_use,
                tau=tau_use,
            )

            asset_dir = outdir / ticker
            asset_dir.mkdir(parents=True, exist_ok=True)
            summary_path = asset_dir / f"{ticker}_{tf}_summary.json"
            summary_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("[ok] backtest complete")


if __name__ == "__main__":
    main()
