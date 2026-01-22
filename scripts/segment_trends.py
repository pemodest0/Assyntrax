#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse


def load_clean(path: Path) -> pd.Series:
    df = pd.read_csv(path, parse_dates=['date'])
    df = df.set_index('date').sort_index()
    if 'price' not in df.columns:
        raise ValueError('CSV sem coluna price: ' + str(path))
    return df['price']


def segments_from_sign(signs: pd.Series) -> list[dict]:
    segs = []
    if signs.empty:
        return segs
    current_sign = None
    start = None
    for idx, val in signs.items():
        if pd.isna(val) or val == 0:
            # treat as break
            if current_sign is not None:
                segs.append({'sign': current_sign, 'start': start, 'end': prev_idx})
                current_sign = None
                start = None
            prev_idx = idx
            continue
        if current_sign is None:
            current_sign = val
            start = idx
        elif val != current_sign:
            segs.append({'sign': current_sign, 'start': start, 'end': prev_idx})
            current_sign = val
            start = idx
        prev_idx = idx
    if current_sign is not None:
        segs.append({'sign': current_sign, 'start': start, 'end': prev_idx})
    return segs


def analyze_segments(price: pd.Series, segs: list[dict]) -> pd.DataFrame:
    rows = []
    for s in segs:
        start = s['start']
        end = s['end']
        sign = s['sign']
        p0 = price.loc[start]
        p1 = price.loc[end]
        # length in periods
        length = (end - start).days
        # cumulative return
        cumret = (p1 / p0 - 1.0) if p0 and not pd.isna(p0) else np.nan
        rows.append({
            'start': start.strftime('%Y-%m-%d'),
            'end': end.strftime('%Y-%m-%d'),
            'length_days': int(length),
            'sign': int(sign),
            'start_price': float(p0),
            'end_price': float(p1),
            'cum_return': float(cumret),
        })
    return pd.DataFrame(rows)


def process_asset(name: str, series: pd.Series, out_dir: Path, start_date: pd.Timestamp, end_date: pd.Timestamp):
    # trim
    s = series[start_date:end_date].dropna()
    if s.empty:
        print('Vazio para', name)
        return
    # daily returns
    dret = s.pct_change()
    dsign = dret.apply(lambda x: 1 if x>0 else (-1 if x<0 else 0)).fillna(0)
    dsegs = segments_from_sign(dsign)
    ddf = analyze_segments(s, dsegs)
    out_dir.mkdir(parents=True, exist_ok=True)
    ddf.to_csv(out_dir / f'{name}_daily_segments.csv', index=False)

    # weekly
    weekly_price = s.resample('W-FRI').last().dropna()
    wret = weekly_price.pct_change()
    wsign = wret.apply(lambda x: 1 if x>0 else (-1 if x<0 else 0)).fillna(0)
    wsegs = segments_from_sign(wsign)
    wdf = analyze_segments(weekly_price, wsegs)
    wdf.to_csv(out_dir / f'{name}_weekly_segments.csv', index=False)

    # plots: weekly annotated
    fig, ax = plt.subplots(2,1, figsize=(14,8), sharex=True)
    ax[0].plot(s.index, s.values, color='black')
    ax[0].set_title(f'{name} price (daily)')
    # color weekly background
    for seg in wsegs:
        color = '#c8ffd1' if seg['sign']>0 else '#ffd1d1'
        ax[0].axvspan(seg['start'], seg['end'], facecolor=color, alpha=0.3)
    ax[1].plot(weekly_price.index, weekly_price.values, marker='o')
    ax[1].set_title(f'{name} price (weekly) with segments')
    for seg in wsegs:
        color = '#2ca02c' if seg['sign']>0 else '#d62728'
        ax[1].axvspan(seg['start'], seg['end'], facecolor=color, alpha=0.2)
    plt.tight_layout()
    plt.savefig(out_dir / f'{name}_segments_plot.png')
    plt.close()

    # compact summary: keep only segments longer than 1 period for weekly
    wdf_long = wdf[wdf['length_days']>=1].copy()
    wdf_long.to_csv(out_dir / f'{name}_weekly_segments_summary.csv', index=False)

    print('Processed', name, 'daily segments:', len(ddf), 'weekly segments:', len(wdf))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--clean-dir', type=str, default='dados/processed/market_data_cleaned')
    parser.add_argument('--out-dir', type=str, default='results/market_data_aggregates/segments')
    parser.add_argument('--years', type=int, default=20)
    args = parser.parse_args()
    clean = Path(args.clean_dir)
    out = Path(args.out_dir)
    end = pd.Timestamp.today().normalize()
    start = end - pd.DateOffset(years=args.years)
    csvs = sorted(clean.glob('*_cleaned.csv'))
    if not csvs:
        print('No cleaned CSVs found in', clean)
        return
    for f in csvs:
        name = f.stem.replace('_cleaned','')
        series = load_clean(f)
        process_asset(name, series, out, start, end)

if __name__ == '__main__':
    main()
