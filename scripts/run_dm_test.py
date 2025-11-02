from __future__ import annotations

import argparse
import itertools
import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd


def _parse_csv_list(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _dm_statistic(errors_a: pd.Series, errors_b: pd.Series, horizon: int) -> Tuple[float, float]:
    """Compute Diebold-Mariano statistic using squared-error loss."""
    df = pd.concat([errors_a, errors_b], axis=1, join="inner").dropna()
    if df.empty:
        return float("nan"), float("nan")
    diff = df.iloc[:, 0] ** 2 - df.iloc[:, 1] ** 2
    d_mean = diff.mean()
    n = diff.shape[0]
    if n < 5:
        return float("nan"), float("nan")
    lag = max(1, min(int(math.floor(horizon / 2)), n - 1))
    demeaned = diff - d_mean
    gamma0 = float(np.dot(demeaned, demeaned) / (n - 1))
    nw = gamma0
    for k in range(1, lag + 1):
        weight = 1.0 - k / (lag + 1.0)
        cov = float(np.dot(demeaned[k:], demeaned[:-k]) / (n - 1))
        nw += 2.0 * weight * cov
    if nw <= 0:
        return float("nan"), float("nan")
    stat = d_mean / math.sqrt(nw / n)
    # For large samples DM statistic ~ N(0,1)
    p_value = math.erfc(abs(stat) / math.sqrt(2.0))
    return float(stat), float(p_value)


def _baseline_predictions(series: pd.DataFrame) -> Dict[str, pd.Series]:
    results: Dict[str, pd.Series] = {}
    df = series.copy().sort_values("date").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"])

    # Naive random walk (persistence)
    naive_pred = df["price_today"]
    results["baseline:naive"] = naive_pred - df["price_real"]

    # EMA-10 baseline
    ema = df["price_today"].ewm(span=10, adjust=False).mean()
    results["baseline:ema10"] = ema - df["price_real"]

    # AR(1) baseline using OLS on price_today -> price_real
    X = np.column_stack((np.ones(df.shape[0]), df["price_today"].to_numpy()))
    y = df["price_real"].to_numpy()
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    ar_pred = X @ beta
    results["baseline:ar1"] = pd.Series(ar_pred - y, index=df.index)

    # attach index of dates
    for key in results:
        results[key] = pd.Series(results[key].values, index=df["date"])
    return results


def _load_errors(metrics_path: Path, modes: Iterable[str]) -> Tuple[Dict[str, pd.Series], pd.DataFrame]:
    metrics = pd.read_csv(metrics_path)
    metrics["date"] = pd.to_datetime(metrics["date"])
    errors: Dict[str, pd.Series] = {}
    score_rows: List[Dict[str, object]] = []
    for mode in modes:
        mode_df = (
            metrics[metrics["mode"] == mode]
            .copy()
            .sort_values("date")
            .reset_index(drop=True)
        )
        if mode_df.empty:
            continue
        err = mode_df["price_pred"] - mode_df["price_real"]
        errors[f"mode:{mode}"] = pd.Series(err.values, index=mode_df["date"])
        mae = float(mode_df["error_pct"].abs().mean())
        direction = float(mode_df["direction_match"].mean())
        score_rows.append(
            {
                "mode": mode,
                "mode_label": mode_df["mode_label"].iloc[0],
                "mae_pct": mae,
                "direction_accuracy": direction,
            }
        )
    if not score_rows:
        raise RuntimeError(f"No modes found in {metrics_path}")
    base_df = (
        metrics[metrics["mode"] == modes[0]]
        .copy()
        .sort_values("date")
        .reset_index(drop=True)
    )
    base_df = base_df[["date", "price_today", "price_real"]]
    return errors, pd.DataFrame(score_rows), base_df


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Diebold-Mariano comparison across result folders.")
    parser.add_argument("--input-dir", type=str, required=True, help="Directory containing daily forecast subfolders.")
    parser.add_argument("--modes", type=str, default="classical,quantum_hadamard,quantum_grover")
    parser.add_argument("--baseline", type=str, default="ema10,ar1")
    parser.add_argument("--forecast-days", type=int, default=5)
    parser.add_argument("--outdir", type=str, default="results_finance/dm_results")
    args = parser.parse_args(argv)

    modes = _parse_csv_list(args.modes)
    baselines = _parse_csv_list(args.baseline)
    input_dir = Path(args.input_dir)
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: List[Dict[str, object]] = []
    model_rows: List[Dict[str, object]] = []

    for subdir in sorted(input_dir.iterdir()):
        if not subdir.is_dir():
            continue
        metrics_path = subdir / "daily_forecast_metrics.csv"
        if not metrics_path.exists():
            continue
        dataset_name = subdir.name
        try:
            error_dict, score_df, ref_prices = _load_errors(metrics_path, modes)
        except Exception as exc:  # pragma: no cover - diagnostic
            print(f"[WARN] skipping {dataset_name}: {exc}")
            continue

        baseline_errors = _baseline_predictions(ref_prices)
        for key, value in baseline_errors.items():
            error_dict[key] = value
            if key not in score_df["mode"].values:
                if key == "baseline:naive":
                    label = "Naive"
                elif key == "baseline:ema10":
                    label = "EMA(10)"
                elif key == "baseline:ar1":
                    label = "AR(1)"
                else:
                    label = key
                e_pct = float((value / ref_prices["price_real"].values).abs().mean() * 100.0)
                direction = float((np.sign(ref_prices["price_real"].values - ref_prices["price_today"].values) == 0).mean())
                score_df = pd.concat(
                    [
                        score_df,
                        pd.DataFrame(
                            [
                                {
                                    "mode": key,
                                    "mode_label": label,
                                    "mae_pct": e_pct,
                                    "direction_accuracy": direction,
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )

        base_name = modes[0]
        compare_pairs: List[Tuple[str, str]] = []
        for mode in modes[1:]:
            if f"mode:{mode}" in error_dict:
                compare_pairs.append((f"mode:{mode}", f"mode:{base_name}"))
        for baseline in baselines:
            base_key = f"baseline:{baseline}"
            if base_key not in error_dict:
                continue
            compare_pairs.append((base_key, f"mode:{base_name}"))
            for mode in modes[1:]:
                mode_key = f"mode:{mode}"
                if mode_key in error_dict:
                    compare_pairs.append((mode_key, base_key))

        for key, series in error_dict.items():
            model_rows.append(
                {
                    "dataset": dataset_name,
                    "model": key,
                    "mae": float(np.nanmean(np.abs(series))),
                }
            )

        for first, second in compare_pairs:
            if first not in error_dict or second not in error_dict:
                continue
            stat, p_val = _dm_statistic(error_dict[first], error_dict[second], args.forecast_days)
            summary_rows.append(
                {
                    "dataset": dataset_name,
                    "model_a": first,
                    "model_b": second,
                    "dm_stat": stat,
                    "p_value": p_val,
                }
            )

        score_df.insert(0, "dataset", dataset_name)
        score_df.to_csv(out_dir / f"{dataset_name}_scores.csv", index=False)

    if summary_rows:
        pd.DataFrame(summary_rows).to_csv(out_dir / "dm_summary.csv", index=False)
    if model_rows:
        pd.DataFrame(model_rows).to_csv(out_dir / "model_errors.csv", index=False)


if __name__ == "__main__":
    main()
