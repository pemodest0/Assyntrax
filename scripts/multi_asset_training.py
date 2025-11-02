#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans


def load_metrics(paths):
    frames = {}
    for label, path in paths.items():
        df = pd.read_csv(path, parse_dates=["date"])
        df = df[df["mode"] == "classical"].copy()
        if df.empty:
            continue
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        frames[label] = df
    return frames


def compute_feature_matrix(frames, feature_cols):
    series = []
    labels = []
    for label, df in frames.items():
        available = [col for col in feature_cols if col in df.columns]
        features = df[available].replace([np.inf, -np.inf], np.nan).fillna(method="ffill").fillna(method="bfill").fillna(0.0)
        aggregated = features.mean()
        vector = aggregated.reindex(feature_cols, fill_value=0.0).to_numpy()
        series.append(vector)
        labels.append(label)
    return np.vstack(series), labels


def main() -> None:
    parser = argparse.ArgumentParser(description="Clusterização de ativos para treino compartilhado.")
    parser.add_argument("--assets", nargs="+", help="Lista label:path")
    parser.add_argument("--clusters", type=int, default=3, help="Número de clusters")
    parser.add_argument("--output", type=str, default="results/multi_asset_clusters.json")
    args = parser.parse_args()

    paths = {}
    for item in args.assets:
        label, path = item.split(":", 1)
        paths[label.upper()] = path

    frames = load_metrics(paths)
    if not frames:
        raise SystemExit("Nenhum dataset carregado")

    feature_cols = [
        "expected_return",
        "alpha",
        "entropy",
        "vol_realized_short",
        "vol_realized_long",
        "vol_ratio",
        "rsi_14",
        "bollinger_bandwidth",
    ]

    matrix, labels = compute_feature_matrix(frames, feature_cols)
    clusters = min(args.clusters, len(labels))
    kmeans = KMeans(n_clusters=clusters, random_state=42)
    groups = kmeans.fit_predict(matrix)

    result = {}
    for group, label in zip(groups, labels):
        result.setdefault(int(group), []).append(label)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
