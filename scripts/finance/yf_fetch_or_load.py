import os
from pathlib import Path

import numpy as np
import pandas as pd


def find_local_data(ticker, base_dir):
    ticker_upper = ticker.upper()
    candidates = []
    for root, _, files in os.walk(base_dir):
        if any(part in root for part in ["venv", "site-packages", "website", "results", ".git"]):
            continue
        for name in files:
            if not name.lower().endswith(".csv"):
                continue
            stem = Path(name).stem.upper()
            if stem == ticker_upper or stem.replace("_CLEANED", "") == ticker_upper:
                candidates.append(Path(root) / name)
    return candidates


def _detect_date_column(columns):
    candidates = ["date", "datetime", "timestamp", "time"]
    lower_map = {col.lower(): col for col in columns}
    for cand in candidates:
        for key, col in lower_map.items():
            if cand == key or key.endswith(cand):
                return col
    return None


def _detect_price_column(columns):
    candidates = [
        "adj close",
        "adj_close",
        "adjclose",
        "adjusted close",
        "adjusted_close",
        "close",
        "price",
    ]
    lower_map = {col.lower(): col for col in columns}
    for cand in candidates:
        if cand in lower_map:
            return lower_map[cand]
    return None


def load_price_series(path):
    df = pd.read_csv(path)
    date_col = _detect_date_column(df.columns)
    price_col = _detect_price_column(df.columns)
    if not date_col or not price_col:
        return None
    df = df[[date_col, price_col]].copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, price_col])
    df = df.sort_values(date_col)
    df.rename(columns={date_col: "date", price_col: "price"}, inplace=True)
    return df


def fetch_yfinance(ticker, start="2009-01-01", end=None):
    try:
        import yfinance as yf
    except ImportError as exc:
        raise RuntimeError("yfinance not installed; cannot fetch remote data.") from exc

    df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=False, group_by="column")
    if df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0].lower() for col in df.columns]
    df = df.reset_index()
    price_col = "adj close" if "adj close" in df.columns else "close"
    date_col = "Date" if "Date" in df.columns else "date"
    out = df[[date_col, price_col]].copy()
    out.rename(columns={date_col: "date", price_col: "price"}, inplace=True)
    return out


def unify_to_daily(df):
    df = df.copy()
    if "date" not in df.columns:
        date_col = _detect_date_column(df.columns)
        if date_col:
            df.rename(columns={date_col: "date"}, inplace=True)
    if "price" not in df.columns:
        price_col = _detect_price_column(df.columns)
        if price_col:
            df.rename(columns={price_col: "price"}, inplace=True)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.tz_localize(None)
    df = df.dropna(subset=["date", "price"])
    df = df.sort_values("date")
    df = df.drop_duplicates("date", keep="last")
    df["log_price"] = (df["price"]).astype(float).apply(lambda x: np.nan if x <= 0 else x)
    df = df.dropna(subset=["log_price"])
    df["log_price"] = np.log(df["log_price"].astype(float))
    df["r"] = df["log_price"].diff()
    df = df.dropna(subset=["r"])
    return df


def save_cache(df, base_dir, ticker):
    out_dir = Path(base_dir) / "data" / "raw" / "finance" / "yfinance_daily"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{ticker}.csv"
    df.to_csv(out_path, index=False)
    return out_path
