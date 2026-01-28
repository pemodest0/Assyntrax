#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import pandas as pd
import json
import argparse


def weekly_changes(clean_csv: Path):
    df = pd.read_csv(clean_csv, parse_dates=['date']).set_index('date').sort_index()
    weekly = df['price'].resample('W-FRI').last().dropna()
    returns = weekly.pct_change().dropna()
    rdf = returns.to_frame(name='weekly_return')
    rdf['price'] = weekly.loc[rdf.index]
    rdf = rdf.reset_index().rename(columns={'index':'date'})
    rdf['date_start'] = (rdf['date'] - pd.Timedelta(days=6)).dt.strftime('%Y-%m-%d')
    rdf['date_end'] = rdf['date'].dt.strftime('%Y-%m-%d')
    rdf['weekly_return_pct'] = (rdf['weekly_return'] * 100).round(4)
    return rdf


def make_asset_report(name: str, clean_csv: Path, plot_png: Path, top_n: int = 10):
    rdf = weekly_changes(clean_csv)
    top_up = rdf.sort_values('weekly_return', ascending=False).head(top_n)
    top_down = rdf.sort_values('weekly_return', ascending=True).head(top_n)
    stats = {
        'period_start': rdf['date_start'].min() if not rdf.empty else None,
        'period_end': rdf['date_end'].max() if not rdf.empty else None,
        'n_weeks': int(len(rdf)),
        'mean_weekly_return_pct': float(rdf['weekly_return_pct'].mean()) if not rdf.empty else None,
        'std_weekly_return_pct': float(rdf['weekly_return_pct'].std()) if not rdf.empty else None,
    }
    def row_to_dict(r):
        return {
            'date_start': r['date_start'],
            'date_end': r['date_end'],
            'weekly_return_pct': float(r['weekly_return_pct']),
            'price': float(r['price']),
            'date': r['date'].strftime('%Y-%m-%d')
        }
    return {
        'name': name,
        'plot_png': str(plot_png) if plot_png.exists() else None,
        'stats': stats,
        'top_up': [row_to_dict(r) for _, r in top_up.iterrows()],
        'top_down': [row_to_dict(r) for _, r in top_down.iterrows()],
    }


def consolidate_all(asset_reports: list[dict], top_n: int = 10):
    # build global top ups/downs across assets
    rows = []
    for rep in asset_reports:
        for item in rep['top_up']:
            rows.append({'asset': rep['name'], 'date_start': item['date_start'], 'date_end': item['date_end'], 'weekly_return_pct': item['weekly_return_pct'], 'price': item['price'], 'date': item['date']})
    up_df = pd.DataFrame(rows).sort_values('weekly_return_pct', ascending=False).head(top_n)
    rows = []
    for rep in asset_reports:
        for item in rep['top_down']:
            rows.append({'asset': rep['name'], 'date_start': item['date_start'], 'date_end': item['date_end'], 'weekly_return_pct': item['weekly_return_pct'], 'price': item['price'], 'date': item['date']})
    down_df = pd.DataFrame(rows).sort_values('weekly_return_pct', ascending=True).head(top_n)
    return up_df.to_dict(orient='records'), down_df.to_dict(orient='records')


def write_markdown(rep: dict, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{rep['name']}_report.md"
    with path.open('w', encoding='utf8') as f:
        f.write(f"# {rep['name']} — GPT-ready report\n\n")
        f.write(f"**Period:** {rep['stats']['period_start']} → {rep['stats']['period_end']}\n\n")
        f.write(f"**Weeks:** {rep['stats']['n_weeks']}  •  **Mean weekly return (%):** {rep['stats']['mean_weekly_return_pct']:.4f}  •  **Std (%):** {rep['stats']['std_weekly_return_pct']:.4f}\n\n")
        if rep['plot_png']:
            f.write(f"![plot]({rep['plot_png']})\n\n")
        f.write('## Top weekly rises\n')
        for it in rep['top_up']:
            f.write(f"- {it['date_start']} → {it['date_end']}: {it['weekly_return_pct']}% (price {it['price']:.2f})\n")
        f.write('\n## Top weekly drops\n')
        for it in rep['top_down']:
            f.write(f"- {it['date_start']} → {it['date_end']}: {it['weekly_return_pct']}% (price {it['price']:.2f})\n")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--clean-dir', type=str, default='dados/processed/market_data_cleaned')
    parser.add_argument('--plots-dir', type=str, default='results/market_data_aggregates/segments')
    parser.add_argument('--out-json', type=str, default='results/gpt_ready_report.json')
    parser.add_argument('--out-md-dir', type=str, default='results/gpt_reports')
    parser.add_argument('--top-n', type=int, default=10)
    args = parser.parse_args()

    clean_dir = Path(args.clean_dir)
    plots_dir = Path(args.plots_dir)
    out_json = Path(args.out_json)
    out_md_dir = Path(args.out_md_dir)

    csvs = sorted(clean_dir.glob('*_cleaned.csv'))
    asset_reports = []
    for csv in csvs:
        name = csv.stem.replace('_cleaned','')
        plot = plots_dir / f'{name}_segments_plot.png'
        rep = make_asset_report(name, csv, plot, top_n=args.top_n)
        asset_reports.append(rep)
        write_markdown(rep, out_md_dir)

    up_all, down_all = consolidate_all(asset_reports, top_n=args.top_n)
    final = {
        'generated_at': pd.Timestamp.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'assets': asset_reports,
        'consolidated_top_up': up_all,
        'consolidated_top_down': down_all,
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(final, indent=2), encoding='utf8')
    print('GPT-ready JSON written to', out_json)
    print('Markdown reports in', out_md_dir)

if __name__ == '__main__':
    main()
