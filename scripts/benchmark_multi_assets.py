#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import json
import matplotlib.pyplot as plt
import pandas as pd


def load_metrics(metrics_path: Path) -> pd.DataFrame:
    df = pd.read_csv(metrics_path, parse_dates=["date"])
    df = df[df["mode"] == "classical"].copy()
    if df.empty:
        raise ValueError(f"No classical data in {metrics_path}")
    if df["date"].dt.tz is not None:
        df["date"] = df["date"].dt.tz_convert("UTC").dt.tz_localize(None)
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df


def compute_yearly_summary(
    df: pd.DataFrame,
    years: List[int],
) -> Dict[int, Dict[str, float]]:
    out: Dict[int, Dict[str, float]] = {}
    df["error_points"] = df["price_pred"] - df["price_real"]
    df["abs_error_points"] = df["error_points"].abs()
    df["abs_error_pct"] = (
        df["abs_error_points"] / df["price_real"].abs().clip(lower=1e-6) * 100.0
    )
    df["direction_match"] = df["direction_match"].astype(bool)
    for year, group in df.groupby(df["date"].dt.year):
        if year not in years:
            continue
        if group.empty:
            continue
        out[year] = {
            "records": int(group.shape[0]),
            "mae_points": float(group["abs_error_points"].mean()),
            "mae_pct": float(group["abs_error_pct"].mean()),
            "median_abs_pct": float(group["abs_error_pct"].median()),
            "direction_accuracy": float(group["direction_match"].mean()),
            "max_over_points": float(group["error_points"].max()),
            "max_under_points": float(group["error_points"].min()),
            "max_abs_pct": float(group["abs_error_pct"].max()),
        }
    return out


def plot_mae(
    summary: Dict[str, Dict[int, Dict[str, float]]],
    years: List[int],
    output: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(8, 4))
    width = 0.35
    x = range(len(summary))
    for idx, year in enumerate(years):
        values = [summary[label].get(year, {}).get("mae_pct", float("nan")) for label in summary]
        ax.bar(
            [i + (idx - 0.5) * width for i in x],
            values,
            width=width,
            label=str(year),
        )
    ax.set_title("MAE percentual por ativo/ano")
    ax.set_ylabel("MAE %")
    ax.set_xticks(list(x))
    ax.set_xticklabels(summary.keys(), rotation=15)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara desempenho de previsão em múltiplos ativos.")
    parser.add_argument(
        "--assets",
        nargs="+",
        default=[
            "IBOV:results/benchmark_2023/ibov_reconstructed/daily_forecast_metrics.csv",
            "SPY:results/benchmark_2023/spy_stooq/daily_forecast_metrics.csv",
        ],
        help="Lista label:path_to_metrics.csv",
    )
    parser.add_argument("--years", nargs="+", type=int, default=[2024, 2025], help="Anos a analisar.")
    parser.add_argument("--output", type=str, default="results/multi_asset_benchmark", help="Diretório de saída.")
    args = parser.parse_args()

    assets: Dict[str, Path] = {}
    for item in args.assets:
        try:
            label, path = item.split(":", 1)
        except ValueError:
            raise SystemExit(f"Invalid asset specification: {item}. Use label:path.")
        assets[label.upper()] = Path(path)

    summaries: Dict[str, Dict[int, Dict[str, float]]] = {}
    rows: List[Dict[str, object]] = []

    for label, path in assets.items():
        try:
            df = load_metrics(path)
        except Exception as exc:
            print(f"[WARN] {label}: {exc}")
            continue
        yearly = compute_yearly_summary(df, args.years)
        if not yearly:
            print(f"[WARN] {label}: No data for requested years.")
            continue
        summaries[label] = yearly
        for year, stats in yearly.items():
            row = {"asset": label, "year": year}
            row.update(stats)
            rows.append(row)

    if not summaries:
        raise SystemExit("No summaries computed.")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    df_summary = pd.DataFrame(rows)
    df_summary.sort_values(["asset", "year"], inplace=True)
    df_summary.to_csv(output_dir / "summary.csv", index=False)

    plot_mae(summaries, args.years, output_dir / "mae_comparison.png")

    with (output_dir / "summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summaries, fh, indent=2, default=float)

    print(df_summary)


if __name__ == "__main__":
    main()

