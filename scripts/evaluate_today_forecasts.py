from __future__ import annotations

import json
import subprocess
from datetime import date
from pathlib import Path
import sys
import time
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "modelos" / "core" / "src"
for candidate in (PROJECT_ROOT, SRC_ROOT):
    path_str = str(candidate)
    if path_str not in sys.path:
        sys.path.append(path_str)

from financial_walk_model import PHASE_LOW, PHASE_HIGH


ASSETS_FILE = PROJECT_ROOT / "dados" / "brutos" / "yf_assets.json"
OUT_ROOT = PROJECT_ROOT / "results" / "today_forecast_eval"
OUT_ROOT.mkdir(parents=True, exist_ok=True)


def predictability_score(alpha: float, low: float = PHASE_LOW, high: float = PHASE_HIGH) -> float:
    if not pd.notna(alpha) or not float(pd.notna(alpha)):
        return float("nan")
    try:
        a = float(alpha)
    except Exception:
        return float("nan")
    if not (a == a):
        return float("nan")
    if high <= low:
        return 0.0
    # normalized where alpha <= low => 0 (chaotic), alpha >= high => 1 (predictable)
    score = (a - low) / (high - low)
    return float(max(0.0, min(1.0, score)))


def run_forecast_for_symbol(symbol: str, out_base: Path) -> Path:
    # call existing script; skip quantum for speed
    out_arg = str(out_base)
    cmd = [sys.executable, "scripts/run_daily_forecast.py", "--symbol", symbol, "--output", out_arg, "--skip-quantum"]
    # ensure we have an end date (today)
    today = date.today().isoformat()
    cmd.extend(["--end", today])
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=False)
    return out_base / symbol


def collect_latest_rows(symbol_dir: Path) -> pd.DataFrame:
    csv_path = symbol_dir / "daily_forecast_metrics.csv"
    if not csv_path.exists():
        return pd.DataFrame()
    df = pd.read_csv(csv_path, parse_dates=["date"])
    if df.empty:
        return df
    # pick most recent forecast date per mode
    df = df.sort_values(["mode", "date"]).groupby("mode").tail(1)
    df["symbol"] = df["symbol"].astype(str)
    return df


def main() -> None:
    with open(ASSETS_FILE, "r", encoding="utf-8") as f:
        assets = json.load(f)
    symbols = list(assets.values())
    aggregated = []
    for sym in symbols:
        sym_label = sym
        dest = run_forecast_for_symbol(sym_label, OUT_ROOT)
        # small pause to allow files to flush
        time.sleep(0.5)
        df = collect_latest_rows(dest)
        if df.empty:
            print(f"No results for {sym_label}")
            continue
        for _, row in df.iterrows():
            price_today = float(row.get("price_today", float("nan")))
            price_pred = float(row.get("price_pred", float("nan")))
            price_real = float(row.get("price_real", float("nan")))
            error_pct = float(row.get("error_pct", float("nan")))
            alpha = float(row.get("alpha", float("nan")))
            phase = row.get("phase", "") if "phase" in row.index else None
            pred_vs_today = float(100.0 * (price_pred - price_today) / price_today) if price_today not in (0.0, float("nan")) else float("nan")
            predict_score = predictability_score(alpha)
            aggregated.append(
                {
                    "symbol": sym_label,
                    "mode": row.get("mode"),
                    "date": row.get("date"),
                    "price_today": price_today,
                    "price_pred": price_pred,
                    "price_real": price_real,
                    "error_pct": error_pct,
                    "pred_vs_today_pct": pred_vs_today,
                    "alpha": alpha,
                    "phase": phase,
                    "predictability_score": predict_score,
                }
            )

    out_df = pd.DataFrame(aggregated)
    out_path = OUT_ROOT / "today_forecast_summary.csv"
    out_df.to_csv(out_path, index=False)
    print(f"Wrote summary to {out_path}")


if __name__ == "__main__":
    main()
