#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
import sys

import pandas as pd
import yfinance as yf

TRY_PANDAS_DATAREADER = True
try:
    from pandas_datareader import data as pdr
except Exception:
    TRY_PANDAS_DATAREADER = False

import matplotlib.pyplot as plt


def _ensure_series(candidate: pd.Series | pd.DataFrame) -> pd.Series:
    if isinstance(candidate, pd.Series):
        return candidate
    if isinstance(candidate, pd.DataFrame):
        if candidate.shape[1] == 1:
            return candidate.iloc[:, 0]
        return candidate.iloc[:, 0]
    raise TypeError(f"Objeto inesperado retornado ao extrair preços: {type(candidate)}")


def _extract_price_series(df: pd.DataFrame, ticker: str) -> pd.Series:
    if 'Adj Close' in df.columns:
        return _ensure_series(df['Adj Close'])
    if isinstance(df.columns, pd.MultiIndex):
        price_candidate = None
        for col in df.columns:
            parts = col if isinstance(col, tuple) else (col,)
            if 'Adj Close' in parts:
                series = _ensure_series(df[col])
                if ticker in parts:
                    return series
                price_candidate = series
        if price_candidate is not None:
            return price_candidate
        close_candidate = None
        for col in df.columns:
            parts = col if isinstance(col, tuple) else (col,)
            if 'Close' in parts:
                series = _ensure_series(df[col])
                if ticker in parts:
                    return series
                close_candidate = series
        if close_candidate is not None:
            return close_candidate
    if 'Close' in df.columns:
        return _ensure_series(df['Close'])
    available = ', '.join(map(str, df.columns))
    raise KeyError(f"Coluna de preço não encontrada para {ticker} (colunas: {available})")


def download_yf(ticker: str, start: str, end: str, output: Path) -> None:
    df = yf.download(ticker, start=start, end=end, progress=False)
    if df.empty:
        raise ValueError(f"Nenhum dado retornado para {ticker}")
    price_series = _extract_price_series(df, ticker)
    frame = price_series.to_frame(name='price')
    frame.index.name = 'date'
    frame = frame.reset_index()
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(f"Salvo {output} ({frame.shape[0]} linhas)")


def download_fred(symbol: str, start: str, end: str, output: Path) -> bool:
    if not TRY_PANDAS_DATAREADER:
        print("pandas_datareader não está disponível; pulando FRED")
        return False
    try:
        df = pdr.DataReader(symbol, 'fred', start, end)
    except Exception as e:
        print(f"Erro ao baixar {symbol} via FRED: {e}")
        return False
    if df.empty:
        print(f"FRED retornou vazio para {symbol}")
        return False
    series = df.iloc[:, 0]
    frame = series.to_frame(name='price')
    frame.index.name = 'date'
    frame = frame.reset_index()
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False)
    print(f"Salvo FRED {symbol} -> {output} ({frame.shape[0]} linhas)")
    return True


def plot_series(csv_path: Path, out_png: Path, title: str | None = None) -> None:
    df = pd.read_csv(csv_path, parse_dates=['date']).set_index('date')
    plt.figure(figsize=(12, 4))
    plt.plot(df.index, df['price'])
    plt.title(title or csv_path.stem)
    plt.xlabel('date')
    plt.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_png)
    plt.close()
    print(f"Plot salvo: {out_png}")


def main():
    parser = argparse.ArgumentParser(description='Baixa séries de mercado e gera CSVs + gráficos.')
    parser.add_argument('--start', type=str, help='Data inicial YYYY-MM-DD (default = 25 anos atrás)')
    parser.add_argument('--end', type=str, help='Data final YYYY-MM-DD (default = hoje)')
    parser.add_argument('--tickers', nargs='+', help='Tickers yfinance para baixar (além dos defaults)')
    parser.add_argument('--no-fred', action='store_true', help='Pula tentativas de download via FRED (DGS10/DGS2)')
    parser.add_argument('--out-dir', type=str, default='dados/brutos/market_data', help='Diretório para CSVs')
    parser.add_argument('--plots-dir', type=str, default='results/market_data_plots', help='Diretório para plots')
    args = parser.parse_args()

    end_date = datetime.strptime(args.end, '%Y-%m-%d') if args.end else datetime.utcnow()
    if args.start:
        start_date = datetime.strptime(args.start, '%Y-%m-%d')
    else:
        start_date = end_date - timedelta(days=int(25 * 365.25))

    start = start_date.strftime('%Y-%m-%d')
    end = end_date.strftime('%Y-%m-%d')

    out_dir = Path(args.out_dir)
    plots_dir = Path(args.plots_dir)

    default_tickers = {
        '^GSPC': 'S&P500_index',
        'SPY': 'SPY',
        'DX-Y.NYB': 'DXY',
        '^VIX': 'VIX',
    }

    tickers = args.tickers if args.tickers else list(default_tickers.keys())

    for ticker in tickers:
        safe = ticker.replace('^', '').replace(' ', '_').replace('/', '_').upper()
        csv_path = out_dir / f"{safe}.csv"
        try:
            download_yf(ticker, start, end, csv_path)
        except Exception as e:
            print(f"Falha ao baixar {ticker} via yfinance: {e}")

    # Treasuries: tentar FRED DGS10 / DGS2, senão fallback para ^TNX (10y) via yfinance
    fred_period_start = start
    fred_period_end = end
    # 10Y
    dgs10_out = out_dir / 'DGS10.csv'
    ok10 = False
    if not args.no_fred and TRY_PANDAS_DATAREADER:
        ok10 = download_fred('DGS10', fred_period_start, fred_period_end, dgs10_out)
    if not ok10:
        print('Fallback: tentando ^TNX (yahoo) para 10Y')
        try:
            download_yf('^TNX', start, end, dgs10_out)
        except Exception as e:
            print(f'Falha fallback 10Y: {e}')

    # 2Y
    dgs2_out = out_dir / 'DGS2.csv'
    ok2 = False
    if not args.no_fred and TRY_PANDAS_DATAREADER:
        ok2 = download_fred('DGS2', fred_period_start, fred_period_end, dgs2_out)
    if not ok2:
        print('Fallback: procurando ticker yfinance para 2Y via ^IR2 (não garantido)')
        try:
            download_yf('^IR2', start, end, dgs2_out)
        except Exception as e:
            print(f'Falha fallback 2Y: {e}')

    # Gerar plots para todos CSVs em out_dir
    csvs = sorted(out_dir.glob('*.csv'))
    for csv in csvs:
        png = plots_dir / f"{csv.stem}.png"
        try:
            plot_series(csv, png)
        except Exception as e:
            print(f"Erro gerando plot para {csv}: {e}")

    print('\nConcluído. CSVs salvos em:', out_dir)
    print('Plots salvos em:', plots_dir)


if __name__ == '__main__':
    main()
