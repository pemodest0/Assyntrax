from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import date
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "results" / "today_forecast_eval"
OUT_ROOT.mkdir(parents=True, exist_ok=True)

ASSETS_FILE = ROOT / "dados" / "configs" / "top5_assets.json"


def run_forecast(symbol: str) -> Path:
    cmd = [sys.executable, "scripts/run_daily_forecast.py", "--symbol", symbol, "--output", str(OUT_ROOT), "--skip-quantum"]
    cmd.extend(["--end", date.today().isoformat()])
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=False)
    return OUT_ROOT / symbol


def collect_latest(symbol_dir: Path) -> pd.DataFrame:
    csv = symbol_dir / "daily_forecast_metrics.csv"
    if not csv.exists():
        return pd.DataFrame()
    df = pd.read_csv(csv, parse_dates=["date"]) if csv.exists() else pd.DataFrame()
    if df.empty:
        return df
    df = df.sort_values(["mode", "date"]).groupby("mode").tail(1)
    df["symbol"] = df["symbol"].astype(str)
    return df


def main():
    with ASSETS_FILE.open("r", encoding="utf8") as f:
        assets = json.load(f)
    symbols = list(assets.values())
    agg = []
    for s in symbols:
        outdir = run_forecast(s)
        time.sleep(0.5)
        df = collect_latest(outdir)
        if df.empty:
            print("No results for", s)
            continue
        for _, r in df.iterrows():
            agg.append({
                "symbol": s,
                "mode": r.get("mode"),
                "date": r.get("date"),
                "price_today": r.get("price_today"),
                "price_pred": r.get("price_pred"),
                "price_real": r.get("price_real"),
                "error_pct": r.get("error_pct"),
                "alpha": r.get("alpha"),
            })
    out = pd.DataFrame(agg)
    out.to_csv(OUT_ROOT / "investor_top5_summary.csv", index=False)
    print("Wrote summary to", OUT_ROOT / "investor_top5_summary.csv")


if __name__ == '__main__':
    main()
