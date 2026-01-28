from __future__ import annotations

import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "raw"
LEGACY_DATA_DIR = ROOT / "dados" / "brutos"
OUT = ROOT / 'results' / 'benchmarks'
OUT.mkdir(parents=True, exist_ok=True)

def find_price_file(symbol: str) -> Path | None:
    # try common variations
    candidates = [f'{symbol}.csv', f'{symbol.lower()}.csv', f'{symbol}_stooq.csv', f'{symbol}_reconstructed.csv']
    for c in candidates:
        p = DATA_DIR / c
        if p.exists():
            return p
        legacy = LEGACY_DATA_DIR / c
        if legacy.exists():
            return legacy
    # try fuzzy search
    for folder in (DATA_DIR, LEGACY_DATA_DIR):
        if not folder.exists():
            continue
        for p in folder.glob("*.csv"):
            if symbol.lower() in p.name.lower():
                return p
    return None


def prepare_series(path: Path) -> pd.Series:
    df = pd.read_csv(path, parse_dates=[0], infer_datetime_format=True)
    df.rename(columns={df.columns[0]: 'date'}, inplace=True)
    # try common price columns
    price = None
    for col in ['close', 'Close', 'adj_close', 'Adj Close', 'price', 'Price', 'PRECO', 'Preço']:
        if col in df.columns:
            price = df[col]
            break
    if price is None:
        # fallback to last numeric column
        numcols = df.select_dtypes(include=[np.number]).columns
        if len(numcols) == 0:
            raise RuntimeError('No numeric column found in ' + str(path))
        price = df[numcols[-1]]
    s = pd.Series(data=price.values, index=pd.to_datetime(df['date']))
    s = s.sort_index()
    return s


def run_baselines(symbol: str, series: pd.Series, out_root: Path) -> None:
    # walk-forward one-step forecast using simple baselines
    window = 252
    ma_k = 5
    records = { 'naive': [], 'ma5': [] }
    for i in range(window, len(series)-1):
        today = series.index[i]
        price_today = float(series.iloc[i])
        price_next = float(series.iloc[i+1])
        # naive: predict same price
        pred_naive = price_today
        # ma5 on prices
        ma = series.iloc[i-ma_k+1:i+1].mean() if i-ma_k+1 >= 0 else series.iloc[:i+1].mean()
        pred_ma5 = float(ma)
        for name, pred in [('naive', pred_naive), ('ma5', pred_ma5)]:
            error_pct = 100.0 * (pred - price_next) / price_next if price_next != 0 else np.nan
            records[name].append({
                'date': today.isoformat(),
                'symbol': symbol,
                'price_today': price_today,
                'price_pred': float(pred),
                'price_real': price_next,
                'error_pct': float(error_pct),
                'direction_pred': int(pred > price_today),
                'direction_real': int(price_next > price_today),
            })

    # save per-baseline CSVs
    for name, recs in records.items():
        outdir = out_root / symbol / name
        outdir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(recs).to_csv(outdir / 'daily_metrics.csv', index=False)
        # summary
        df = pd.DataFrame(recs)
        if df.empty:
            continue
        summary = {
            'symbol': symbol,
            'baseline': name,
            'mae_pct': float(df['error_pct'].abs().mean()),
            'direction_acc': float((df['direction_pred'] == df['direction_real']).mean()),
            'n': int(len(df)),
        }
        (outdir / 'summary.json').write_text(json.dumps(summary, indent=2))


def main(symbols: list[str]):
    for s in symbols:
        print('Benchmarking', s)
        p = find_price_file(s)
        if p is None:
            print('No price file for', s)
            continue
        try:
            series = prepare_series(p)
        except Exception as e:
            print('Failed to load', p, e)
            continue
        run_baselines(s, series, OUT)
    print('Benchmarks completed; outputs in', OUT)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        syms = sys.argv[1:]
    else:
        # default: read top5 config
        cfg = Path("data/configs/top5_assets.json")
        if cfg.exists():
            syms = list(json.loads(cfg.read_text()).values())
        else:
            legacy_cfg = Path("dados/configs/top5_assets.json")
            if legacy_cfg.exists():
                syms = list(json.loads(legacy_cfg.read_text()).values())
            else:
                syms = ["SPY", "AAPL", "MSFT", "GOOG", "AMZN"]
    main(syms)
