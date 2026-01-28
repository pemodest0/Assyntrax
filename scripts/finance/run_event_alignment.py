from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd


def _load_events(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "date" not in df.columns:
        raise KeyError("events CSV must contain a 'date' column.")
    if "label" not in df.columns:
        df["label"] = df["date"].astype(str)
    df["date"] = pd.to_datetime(df["date"])
    return df[["date", "label"]]


def _find_peak(series: pd.Series, target_date: pd.Timestamp, window_days: int) -> tuple[Optional[pd.Timestamp], Optional[float]]:
    mask = series.index.to_series()
    window = series.loc[
        (mask >= target_date - pd.Timedelta(days=window_days))
        & (mask <= target_date + pd.Timedelta(days=window_days))
    ]
    if window.empty:
        return None, None
    idx = window.abs().idxmax()
    return idx, float(series.loc[idx])


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Align entropy/alpha peaks with event dates.")
    parser.add_argument("--input", required=True, help="Path to daily_forecast_metrics.csv.")
    parser.add_argument("--events", required=True, help="CSV with date,label of events.")
    parser.add_argument("--window-days", type=int, default=10, help="Search window around each event.")
    parser.add_argument("--mode", type=str, default="quantum_hadamard", help="Mode to analyse (default quantum_hadamard).")
    parser.add_argument("--out", required=True, help="Output CSV with alignment results.")
    args = parser.parse_args(argv)

    metrics = pd.read_csv(args.input)
    metrics["date"] = pd.to_datetime(metrics["date"])
    mode_df = metrics[metrics["mode"] == args.mode].copy()
    if mode_df.empty:
        raise RuntimeError(f"No rows for mode '{args.mode}' in {args.input}")
    mode_df.sort_values("date", inplace=True)
    mode_df.set_index("date", inplace=True)

    if "dalpha" not in mode_df.columns:
        mode_df["dalpha"] = mode_df["alpha"].diff()
    if "dentropy" not in mode_df.columns:
        mode_df["dentropy"] = mode_df["entropy"].diff()

    events = _load_events(Path(args.events))
    rows = []
    for _, row in events.iterrows():
        date_event = row["date"]
        label = row["label"]
        peak_alpha_date, peak_alpha_value = _find_peak(mode_df["dalpha"], date_event, args.window_days)
        peak_entropy_date, peak_entropy_value = _find_peak(mode_df["dentropy"], date_event, args.window_days)
        lead_alpha = (
            (peak_alpha_date - date_event).days if peak_alpha_date is not None else np.nan
        )
        lead_entropy = (
            (peak_entropy_date - date_event).days if peak_entropy_date is not None else np.nan
        )
        rows.append(
            {
                "event_date": date_event.date(),
                "event_label": label,
                "peak_alpha_date": peak_alpha_date.date() if peak_alpha_date is not None else None,
                "peak_alpha_value": peak_alpha_value,
                "lead_lag_alpha_days": lead_alpha,
                "peak_entropy_date": peak_entropy_date.date() if peak_entropy_date is not None else None,
                "peak_entropy_value": peak_entropy_value,
                "lead_lag_entropy_days": lead_entropy,
            }
        )

    pd.DataFrame(rows).to_csv(args.out, index=False)


if __name__ == "__main__":
    main()

