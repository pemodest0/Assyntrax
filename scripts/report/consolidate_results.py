from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Optional

import pandas as pd


def _collect_summaries(root: Path, filename: str, extra_cols: Optional[dict] = None) -> pd.DataFrame:
    rows: List[pd.DataFrame] = []
    for path in root.rglob(filename):
        try:
            df = pd.read_csv(path)
        except Exception:
            continue
        df.insert(0, "dataset", path.parent.name)
        if extra_cols:
            for key, value in extra_cols.items():
                df[key] = value
        rows.append(df)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def _write_if_not_empty(df: pd.DataFrame, destination: Path, name: str) -> None:
    if df.empty:
        print(f"[WARN] No data for {name}")
    else:
        df.to_csv(destination / name, index=False)


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="Consolidate finance/physical forecast results.")
    parser.add_argument("--finance-dir", type=str, required=True)
    parser.add_argument("--physical-dir", type=str, required=True)
    parser.add_argument("--dm-dir", type=str, required=False, default=None)
    parser.add_argument("--outdir", type=str, required=True)
    args = parser.parse_args(argv)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    finance_df = _collect_summaries(Path(args.finance_dir), "daily_forecast_summary.csv")
    _write_if_not_empty(finance_df, outdir, "summary_finance.csv")

    physical_df = _collect_summaries(Path(args.physical_dir), "daily_forecast_summary.csv")
    _write_if_not_empty(physical_df, outdir, "summary_physical.csv")

    robustness_df = _collect_summaries(Path(args.physical_dir), "robustness_grid.csv")
    _write_if_not_empty(robustness_df, outdir, "robustness_grid.csv")

    events_df = _collect_summaries(Path(args.finance_dir), "alignment_*.csv")
    _write_if_not_empty(events_df, outdir, "phase_events.csv")

    if args.dm_dir:
        dm_path = Path(args.dm_dir) / "dm_summary.csv"
        if dm_path.exists():
            dm_df = pd.read_csv(dm_path)
            _write_if_not_empty(dm_df, outdir, "dm_summary.csv")
        else:
            print(f"[WARN] DM summary not found in {args.dm_dir}")


if __name__ == "__main__":
    main()

