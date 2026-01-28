#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import argparse
from PIL import Image
import io


def top_changes_weekly(clean_csv: Path, top_n: int = 10):
    df = pd.read_csv(clean_csv, parse_dates=['date']).set_index('date').sort_index()
    weekly = df['price'].resample('W-FRI').last().dropna()
    returns = weekly.pct_change().dropna()
    # build DataFrame
    rdf = returns.to_frame(name='weekly_return')
    rdf['price'] = weekly.loc[rdf.index]
    rdf = rdf.reset_index().rename(columns={'index': 'date'})
    rdf['date_start'] = (rdf['date'] - pd.Timedelta(days=6)).dt.strftime('%Y-%m-%d')
    rdf['date_end'] = rdf['date'].dt.strftime('%Y-%m-%d')
    rdf['weekly_return_pct'] = (rdf['weekly_return'] * 100).round(2)
    top_up = rdf.sort_values('weekly_return', ascending=False).head(top_n)
    top_down = rdf.sort_values('weekly_return', ascending=True).head(top_n)
    return top_up, top_down


def embed_image(ax, image_path: Path):
    img = Image.open(image_path)
    ax.imshow(img)
    ax.axis('off')


def make_asset_pages(pdf: PdfPages, name: str, clean_csv: Path, plot_png: Path, top_up: pd.DataFrame, top_down: pd.DataFrame):
    # Page 1: plot image full page
    fig1 = plt.figure(figsize=(8.27, 11.69))
    ax = fig1.add_subplot(111)
    embed_image(ax, plot_png)
    fig1.suptitle(f'{name} — Segments plot', fontsize=10)
    pdf.savefig(fig1)
    plt.close(fig1)

    # Page 2: top 10 ups and downs as text tables
    fig2, ax2 = plt.subplots(figsize=(8.27, 11.69))
    ax2.axis('off')
    title = f'{name} — Top {len(top_up)} Weekly Rises and Drops'
    ax2.text(0.5, 0.95, title, ha='center', va='top', fontsize=12, weight='bold')

    def df_to_text(df):
        lines = []
        for i, r in df.iterrows():
            lines.append(f"{r['date_start']} → {r['date_end']}: {r['weekly_return_pct']}% (price {r['price']:.2f})")
        return '\n'.join(lines)

    up_text = df_to_text(top_up)
    down_text = df_to_text(top_down)

    ax2.text(0.05, 0.85, 'Top Rises (weekly):', fontsize=10, weight='bold')
    ax2.text(0.05, 0.8, up_text, fontsize=9, family='monospace')
    ax2.text(0.55, 0.85, 'Top Drops (weekly):', fontsize=10, weight='bold')
    ax2.text(0.55, 0.8, down_text, fontsize=9, family='monospace')

    pdf.savefig(fig2)
    plt.close(fig2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--clean-dir', type=str, default='dados/processed/market_data_cleaned')
    parser.add_argument('--plots-dir', type=str, default='results/market_data_aggregates/segments')
    parser.add_argument('--out-pdf', type=str, default='results/market_data_report.pdf')
    parser.add_argument('--top-n', type=int, default=10)
    args = parser.parse_args()

    clean_dir = Path(args.clean_dir)
    plots_dir = Path(args.plots_dir)
    out_pdf = Path(args.out_pdf)
    csvs = sorted(clean_dir.glob('*_cleaned.csv'))
    if not csvs:
        print('No cleaned CSVs found in', clean_dir)
        return

    with PdfPages(out_pdf) as pdf:
        for csv in csvs:
            name = csv.stem.replace('_cleaned','')
            plot_png = plots_dir / f'{name}_segments_plot.png'
            if not plot_png.exists():
                print('Missing plot for', name, 'skipping')
                continue
            top_up, top_down = top_changes_weekly(csv, args.top_n)
            make_asset_pages(pdf, name, csv, plot_png, top_up, top_down)
    print('PDF gerado:', out_pdf)

if __name__ == '__main__':
    main()
