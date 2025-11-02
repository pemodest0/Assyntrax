from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _parse_int_list(text: str) -> List[int]:
    return [int(item.strip()) for item in text.split(",") if item.strip()]


def _parse_float_list(text: str) -> List[float]:
    return [float(item.strip()) for item in text.split(",") if item.strip()]


def _run_forecast(args: argparse.Namespace, bins: int, window: int, noise: float, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    runner = Path(__file__).resolve().parent / "run_daily_forecast.py"
    cmd = [
        sys.executable,
        str(runner),
        "--forecast-days",
        str(args.forecast_days),
        "--window",
        str(window),
        "--bins",
        str(bins),
        "--noise",
        str(noise),
        "--walk-steps",
        str(args.walk_steps),
        "--output",
        str(out_dir),
    ]
    if args.symbol:
        cmd.extend(["--symbol", args.symbol])
    if args.csv:
        cmd.extend(["--csv", args.csv, "--date-col", args.date_col, "--value-col", args.value_col])
        if args.month_zscore:
            cmd.append("--month-zscore")
    if args.start:
        cmd.extend(["--start", args.start])
    if args.end:
        cmd.extend(["--end", args.end])
    if args.return_method:
        cmd.extend(["--return-method", args.return_method])
    subprocess.run(cmd, check=True)


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Robustness grid runner for daily forecasts.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--symbol", type=str, help="Ticker symbol.")
    group.add_argument("--csv", type=str, help="CSV file for generic series.")
    parser.add_argument("--date-col", type=str, default="date")
    parser.add_argument("--value-col", type=str, default="price")
    parser.add_argument("--month-zscore", action="store_true")
    parser.add_argument("--start", type=str, default=None)
    parser.add_argument("--end", type=str, default=None)
    parser.add_argument("--return-method", type=str, choices=("log", "simple", "diff"), default="log")
    parser.add_argument("--forecast-days", type=int, default=5)
    parser.add_argument("--walk-steps", type=int, default=30)
    parser.add_argument("--bins-list", type=str, required=True)
    parser.add_argument("--window-list", type=str, required=True)
    parser.add_argument("--noise-list", type=str, required=True)
    parser.add_argument("--outdir", type=str, required=True)
    args = parser.parse_args(argv)

    bins_values = _parse_int_list(args.bins_list)
    window_values = _parse_int_list(args.window_list)
    noise_values = _parse_float_list(args.noise_list)

    root_out = Path(args.outdir)
    root_out.mkdir(parents=True, exist_ok=True)

    records: List[dict] = []

    for bins, window, noise in itertools.product(bins_values, window_values, noise_values):
        tag = f"bins{bins}_win{window}_noise{noise:.3f}".replace(".", "p")
        subdir = root_out / tag
        print(f"[INFO] Running forecast for {tag}")
        _run_forecast(args, bins, window, noise, subdir)
        summary_path = subdir / "daily_forecast_summary.csv"
        if not summary_path.exists():
            print(f"[WARN] Summary missing for {tag}")
            continue
        summary = pd.read_csv(summary_path)
        for _, row in summary.iterrows():
            records.append(
                {
                    "combination": tag,
                    "bins": bins,
                    "window": window,
                    "noise": noise,
                    "mode": row["mode"],
                    "mode_label": row.get("mode_label", row["mode"]),
                    "mae_pct": row["mae_pct"],
                    "direction_accuracy": row["direction_accuracy"],
                }
            )

    if not records:
        print("[WARN] No records produced.")
        return

    df = pd.DataFrame(records)
    df.to_csv(root_out / "robustness_grid.csv", index=False)

    # Generate summary text
    summary_lines: List[str] = []
    for mode, group in df.groupby("mode"):
        wins = (group["direction_accuracy"] > df[df["mode"] == "classical"]["direction_accuracy"].mean()).sum()
        summary_lines.append(f"{mode}: {wins} wins (direction accuracy above classical mean)")
    (root_out / "robustness_summary.txt").write_text("\n".join(summary_lines), encoding="utf-8")

    # Heatmap for Hadamard direction accuracy per noise
    had_df = df[df["mode"].str.contains("hadamard")]
    if not had_df.empty:
        unique_noise = sorted(had_df["noise"].unique())
        fig, axes = plt.subplots(1, len(unique_noise), figsize=(5 * len(unique_noise), 4), squeeze=False)
        for idx, noise in enumerate(unique_noise):
            pivot = had_df[had_df["noise"] == noise].pivot_table(
                index="bins", columns="window", values="direction_accuracy", aggfunc="mean"
            )
            ax = axes[0, idx]
            im = ax.imshow(pivot.values, origin="lower", cmap="viridis", aspect="auto")
            ax.set_xticks(range(len(pivot.columns)))
            ax.set_xticklabels(pivot.columns)
            ax.set_yticks(range(len(pivot.index)))
            ax.set_yticklabels(pivot.index)
            ax.set_title(f"Hadamard Dir. Acc.\nnoise={noise}")
            ax.set_xlabel("window")
            ax.set_ylabel("bins")
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        fig.tight_layout()
        fig.savefig(root_out / "phase_map.png", dpi=300)
        plt.close(fig)


if __name__ == "__main__":
    main()
