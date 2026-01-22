#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import pandas as pd
import argparse


def aggregate_events(events_df: pd.DataFrame, freq: str) -> pd.DataFrame:
    # events_df: date,type,scale,price
    events_df = events_df.copy()
    events_df['date'] = pd.to_datetime(events_df['date'])
    events_df = events_df.set_index('date')

    def agg_group(g):
        return {
            'n_peaks_daily': int(((g['type']=='peak') & (g['scale']=='daily')).sum()),
            'n_valleys_daily': int(((g['type']=='valley') & (g['scale']=='daily')).sum()),
            'n_peaks_weekly': int(((g['type']=='peak') & (g['scale']=='weekly')).sum()),
            'n_valleys_weekly': int(((g['type']=='valley') & (g['scale']=='weekly')).sum()),
            'max_peak_price': float(g.loc[(g['type']=='peak'),'price'].max() if not g.loc[(g['type']=='peak'),'price'].empty else float('nan')),
            'min_valley_price': float(g.loc[(g['type']=='valley'),'price'].min() if not g.loc[(g['type']=='valley'),'price'].empty else float('nan')),
        }

    grouped = events_df.groupby(pd.Grouper(freq=freq)).apply(lambda g: pd.Series(agg_group(g)))
    grouped = grouped.reset_index().rename(columns={'date': 'period_start'})
    return grouped


def process_all(in_dir: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    weekly_dir = out_dir / 'weekly'
    monthly_dir = out_dir / 'monthly'
    weekly_dir.mkdir(parents=True, exist_ok=True)
    monthly_dir.mkdir(parents=True, exist_ok=True)

    all_events = []
    for f in sorted(in_dir.glob('*_events.csv')):
        if f.name == 'summary.csv':
            continue
        df = pd.read_csv(f)
        series_name = f.stem.replace('_events','')
        if df.empty:
            continue
        # ensure columns
        if 'date' not in df.columns:
            continue
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        # weekly: period starting Monday (W-MON)
        weekly = aggregate_events(df, 'W-MON')
        weekly.insert(0, 'series', series_name)
        weekly.to_csv(weekly_dir / f'{series_name}_weekly.csv', index=False)
        # monthly: month start
        monthly = aggregate_events(df, 'MS')
        monthly.insert(0, 'series', series_name)
        monthly.to_csv(monthly_dir / f'{series_name}_monthly.csv', index=False)
        all_events.append(df.assign(series=series_name))

    if all_events:
        combined = pd.concat(all_events, ignore_index=True)
        combined['date'] = pd.to_datetime(combined['date'])
        combined = combined.set_index('date')
        combined_weekly = combined.groupby([pd.Grouper(freq='W-MON'), 'series']).agg(
            n_peaks_daily = ('type', lambda s: int(((s=='peak') & (combined.loc[s.index,'scale']=='daily')).sum())),
            n_valleys_daily = ('type', lambda s: int(((s=='valley') & (combined.loc[s.index,'scale']=='daily')).sum())),
        ).reset_index().rename(columns={'date':'period_start'})
        # pivot to have series as columns with counts
        pivot_peaks = combined_weekly.pivot(index='period_start', columns='series', values='n_peaks_daily').fillna(0).astype(int)
        pivot_valleys = combined_weekly.pivot(index='period_start', columns='series', values='n_valleys_daily').fillna(0).astype(int)
        pivot_peaks.to_csv(out_dir / 'consolidated_weekly_peaks.csv')
        pivot_valleys.to_csv(out_dir / 'consolidated_weekly_valleys.csv')

    print('Agregação concluída.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--in-dir', type=str, default='results/market_data_events')
    parser.add_argument('--out-dir', type=str, default='results/market_data_aggregates')
    args = parser.parse_args()
    process_all(Path(args.in_dir), Path(args.out_dir))
