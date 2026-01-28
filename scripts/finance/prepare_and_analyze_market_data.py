#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


def detect_local_extrema(series: pd.Series) -> tuple[pd.DatetimeIndex, pd.DatetimeIndex]:
    # simples detect: ponto é pico se maior que anterior e posterior
    s = series.dropna()
    peaks = s[(s > s.shift(1)) & (s > s.shift(-1))].index
    valleys = s[(s < s.shift(1)) & (s < s.shift(-1))].index
    return peaks, valleys


def load_series(path: Path) -> pd.Series:
    df = pd.read_csv(path)
    # detectar coluna de data
    date_cols = [c for c in df.columns if c.lower() in ('date', 'observation_date')]
    if not date_cols:
        # tentar primeira coluna
        date_col = df.columns[0]
    else:
        date_col = date_cols[0]
    # detectar coluna de valor
    value_cols = [c for c in df.columns if c.lower() in ('price', 'adj close', 'close') or c not in (date_col,)]
    if not value_cols:
        raise ValueError(f"Nenhuma coluna de valor encontrada em {path}")
    value_col = value_cols[0]
    df[date_col] = pd.to_datetime(df[date_col])
    df = df[[date_col, value_col]].rename(columns={date_col: 'date', value_col: 'price'})
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df = df.set_index('date').sort_index()
    return df['price']


def process_series(name: str, csv: Path, out_clean: Path, out_plot: Path, out_events: Path):
    s = load_series(csv)
    original_len = len(s)
    # Reindex to daily frequency (calendar days) from min to max
    full_idx = pd.date_range(start=s.index.min(), end=s.index.max(), freq='D')
    s_full = s.reindex(full_idx)
    missing_before = s_full.isna().sum()
    # fill missing: linear interpolation then forward/backfill
    s_filled = s_full.interpolate(method='time')
    s_filled = s_filled.fillna(method='ffill').fillna(method='bfill')
    missing_after = s_filled.isna().sum()

    # save cleaned CSV
    out_clean.parent.mkdir(parents=True, exist_ok=True)
    s_filled.to_frame(name='price').reset_index().rename(columns={'index':'date'}).to_csv(out_clean, index=False)

    # detect daily extrema
    peaks, valleys = detect_local_extrema(s_filled)

    # detect weekly extrema (resample to weekly close)
    weekly = s_filled.resample('W-FRI').last()
    w_peaks, w_valleys = detect_local_extrema(weekly)

    # save events
    out_events.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for dt in peaks:
        rows.append({'date': dt.strftime('%Y-%m-%d'), 'type': 'peak', 'scale': 'daily', 'price': float(s_filled.loc[dt])})
    for dt in valleys:
        rows.append({'date': dt.strftime('%Y-%m-%d'), 'type': 'valley', 'scale': 'daily', 'price': float(s_filled.loc[dt])})
    for dt in w_peaks:
        rows.append({'date': dt.strftime('%Y-%m-%d'), 'type': 'peak', 'scale': 'weekly', 'price': float(weekly.loc[dt])})
    for dt in w_valleys:
        rows.append({'date': dt.strftime('%Y-%m-%d'), 'type': 'valley', 'scale': 'weekly', 'price': float(weekly.loc[dt])})
    events_df = pd.DataFrame(rows).sort_values('date')
    events_df.to_csv(out_events, index=False)

    # plot annotated
    out_plot.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(14,5))
    plt.plot(s_filled.index, s_filled.values, label=name)
    if len(peaks):
        plt.scatter(peaks, s_filled.loc[peaks].values, color='red', marker='^', label='daily peaks')
    if len(valleys):
        plt.scatter(valleys, s_filled.loc[valleys].values, color='green', marker='v', label='daily valleys')
    if len(w_peaks):
        plt.scatter(w_peaks, weekly.loc[w_peaks].values, color='orange', marker='s', label='weekly peaks')
    if len(w_valleys):
        plt.scatter(w_valleys, weekly.loc[w_valleys].values, color='blue', marker='o', label='weekly valleys')
    plt.title(f'{name} — cleaned and extrema')
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_plot)
    plt.close()

    summary = {
        'name': name,
        'original_points': original_len,
        'daily_points_full': len(s_full),
        'missing_before': int(missing_before),
        'missing_after': int(missing_after),
        'daily_peaks': int(len(peaks)),
        'daily_valleys': int(len(valleys)),
        'weekly_peaks': int(len(w_peaks)),
        'weekly_valleys': int(len(w_valleys)),
        'cleaned_csv': str(out_clean),
        'events_csv': str(out_events),
        'plot_png': str(out_plot),
    }
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in-dir', type=str, default='dados/brutos/market_data')
    parser.add_argument('--out-clean-dir', type=str, default='dados/processed/market_data_cleaned')
    parser.add_argument('--out-events-dir', type=str, default='results/market_data_events')
    parser.add_argument('--out-plots-dir', type=str, default='results/market_data_plots_annotated')
    args = parser.parse_args()

    in_dir = Path(args.in_dir)
    csvs = sorted(in_dir.glob('*.csv'))
    if not csvs:
        print('Nenhum CSV encontrado em', in_dir)
        return
    summaries = []
    for csv in csvs:
        name = csv.stem
        clean_out = Path(args.out_clean_dir) / f'{name}_cleaned.csv'
        plot_out = Path(args.out_plots_dir) / f'{name}_annotated.png'
        events_out = Path(args.out_events_dir) / f'{name}_events.csv'
        try:
            summary = process_series(name, csv, clean_out, plot_out, events_out)
            summaries.append(summary)
            print(f"Processado {name}: {summary['daily_points_full']} dias, {summary['daily_peaks']} picos diários, {summary['daily_valleys']} vales diários")
        except Exception as e:
            print(f'Erro processando {csv}: {e}')

    # salvar resumo consolidado
    summ_df = pd.DataFrame(summaries)
    out_summary = Path('results/market_data_events/summary.csv')
    out_summary.parent.mkdir(parents=True, exist_ok=True)
    summ_df.to_csv(out_summary, index=False)
    print('Resumo salvo em', out_summary)


if __name__ == '__main__':
    main()
