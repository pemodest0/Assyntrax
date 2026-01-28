from __future__ import annotations

import pandas as pd
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / 'results' / 'benchmarks'
OUT = ROOT / 'results' / 'backtests'
OUT.mkdir(parents=True, exist_ok=True)


def run_backtest(symbol: str, baseline: str, cost=0.0005):
    csv = BENCH / symbol / baseline / 'daily_metrics.csv'
    if not csv.exists():
        print('missing', csv)
        return
    df = pd.read_csv(csv, parse_dates=['date']).sort_values('date')
    if df.empty:
        return
    # compute next-day return from price_today -> price_real
    df['ret'] = df['price_real'] / df['price_today'] - 1.0
    # signal: long if predicted price > today
    df['signal'] = (df['price_pred'] > df['price_today']).astype(int)
    # position change costs
    df['trade'] = df['signal'].diff().abs().fillna(0)
    # P&L per step: signal * ret - trade*cost
    df['pl'] = df['signal'] * df['ret'] - df['trade'] * cost
    df['cumret'] = (1 + df['pl']).cumprod() - 1
    outdir = OUT / symbol
    outdir.mkdir(parents=True, exist_ok=True)
    df.to_csv(outdir / f'backtest_{baseline}.csv', index=False)
    summary = {
        'symbol': symbol,
        'baseline': baseline,
        'final_cumret': float(df['cumret'].iat[-1]) if not df['cumret'].empty else 0.0,
        'sharpe': float(df['pl'].mean() / (df['pl'].std() + 1e-9) * np.sqrt(252)),
        'max_drawdown': float(((1+df['pl']).cumprod().cummax() - (1+df['pl']).cumprod()).max())
    }
    (outdir / f'backtest_{baseline}_summary.json').write_text(pd.Series(summary).to_json())
    print('Backtest done', symbol, baseline)


def main(symbols: list[str]):
    for s in symbols:
        for b in (BENCH / s).iterdir() if (BENCH / s).exists() else []:
            if b.is_dir():
                run_backtest(s, b.name)


if __name__ == '__main__':
    # default top5
    syms = ['SPY','AAPL','MSFT','GOOG','AMZN']
    main(syms)
