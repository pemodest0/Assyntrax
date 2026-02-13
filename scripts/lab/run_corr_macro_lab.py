#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT_BASE = ROOT / "results" / "lab_corr"
ASSET_GROUPS_PATH = ROOT / "data" / "asset_groups.json"
LOCAL_PRICES_DIR = ROOT / "data" / "raw" / "finance" / "yfinance_daily"


class RateLimitError(RuntimeError):
    pass


@dataclass
class FetchResult:
    ticker: str
    group: str
    api_symbol: str
    status: str
    message: str
    n_points: int
    start: str | None
    end: str | None


DEFAULT_UNIVERSE: list[tuple[str, str]] = [
    ("SPY", "indices"),
    ("QQQ", "indices"),
    ("DIA", "indices"),
    ("IWM", "indices"),
    ("VTI", "indices"),
    ("RSP", "indices"),
    ("VIX", "indices"),
    ("HYG", "credit"),
    ("LQD", "credit"),
    ("TLT", "credit"),
    ("IEF", "credit"),
    ("SHY", "credit"),
    ("TIP", "credit"),
    ("GLD", "commodities"),
    ("SLV", "commodities"),
    ("DBC", "commodities"),
    ("DBA", "commodities"),
    ("USO", "commodities"),
    ("XLE", "commodities"),
    ("XOP", "commodities"),
    ("UUP", "fx"),
    ("FXE", "fx"),
    ("FXY", "fx"),
    ("BTC-USD", "crypto"),
    ("ETH-USD", "crypto"),
    ("EWZ", "emerging"),
    ("EEM", "emerging"),
    ("EFA", "emerging"),
    ("EWJ", "emerging"),
    ("XLF", "equities_us_sectors"),
    ("XLK", "equities_us_sectors"),
    ("XLI", "equities_us_sectors"),
    ("XLB", "equities_us_sectors"),
    ("XLP", "equities_us_sectors"),
    ("XLV", "equities_us_sectors"),
    ("XLY", "equities_us_sectors"),
    ("XLRE", "equities_us_sectors"),
    ("XLU", "equities_us_sectors"),
]


def _utc_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _normalize_symbol_for_twelve(ticker: str) -> str:
    t = ticker.strip().upper()
    if t.startswith("^"):
        t = t[1:]
    if t.endswith("-USD"):
        base = t[: -len("-USD")]
        return f"{base}/USD"
    return t


def _load_universe(max_assets: int) -> list[dict[str, str]]:
    if ASSET_GROUPS_PATH.exists():
        payload = json.loads(ASSET_GROUPS_PATH.read_text(encoding="utf-8"))
        out: list[dict[str, str]] = []
        seen: set[str] = set()
        for group, tickers in payload.items():
            if not isinstance(tickers, list):
                continue
            for ticker in tickers:
                if not isinstance(ticker, str):
                    continue
                t = ticker.strip()
                if not t or t in seen:
                    continue
                seen.add(t)
                out.append({"ticker": t, "group": str(group)})
        if out:
            return out[:max_assets]

    return [{"ticker": t, "group": g} for t, g in DEFAULT_UNIVERSE[:max_assets]]


def _fetch_daily_close(api_symbol: str, api_key: str, timeout_sec: int = 30) -> pd.Series:
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": api_symbol,
        "interval": "1day",
        "outputsize": 5000,
        "apikey": api_key,
        "format": "JSON",
    }
    req_url = f"{url}?{urlencode(params)}"
    try:
        with urlopen(req_url, timeout=timeout_sec) as resp:
            body = resp.read()
            data = json.loads(body.decode("utf-8"))
    except HTTPError as exc:
        if exc.code == 429:
            raise RateLimitError("HTTP 429 from Twelve Data") from exc
        msg = exc.read().decode("utf-8", errors="ignore").strip()
        raise RuntimeError(f"HTTP {exc.code} {msg}".strip()) from exc
    except URLError as exc:
        raise RuntimeError(f"Network error: {exc}") from exc

    if str(data.get("status", "")).lower() == "error":
        code = str(data.get("code", ""))
        msg = str(data.get("message", "unknown Twelve Data error"))
        if code == "429" or "limit" in msg.lower():
            raise RateLimitError(msg)
        raise RuntimeError(f"{code} {msg}".strip())

    values = data.get("values", [])
    if not isinstance(values, list) or not values:
        raise RuntimeError("empty values from Twelve Data")

    df = pd.DataFrame(values)
    if "datetime" not in df.columns or "close" not in df.columns:
        raise RuntimeError("missing datetime/close in Twelve Data payload")

    dt = pd.to_datetime(df["datetime"], errors="coerce")
    close = pd.to_numeric(df["close"], errors="coerce")
    out = pd.Series(close.to_numpy(dtype=float), index=dt, name="close")
    out = out[~out.index.isna()].sort_index()
    out = out[~out.index.duplicated(keep="last")]
    out = out.dropna()
    if out.empty:
        raise RuntimeError("no valid close values")
    return out


def _fetch_universe(
    universe: list[dict[str, str]],
    api_key: str,
    min_points: int,
) -> tuple[dict[str, pd.Series], list[FetchResult], bool]:
    prices: dict[str, pd.Series] = {}
    logs: list[FetchResult] = []
    rate_limited = False

    for row in universe:
        ticker = row["ticker"]
        group = row["group"]
        api_symbol = _normalize_symbol_for_twelve(ticker)
        try:
            s = _fetch_daily_close(api_symbol=api_symbol, api_key=api_key)
            if s.shape[0] < min_points:
                logs.append(
                    FetchResult(
                        ticker=ticker,
                        group=group,
                        api_symbol=api_symbol,
                        status="skip_low_history",
                        message=f"points<{min_points}",
                        n_points=int(s.shape[0]),
                        start=str(s.index.min().date()),
                        end=str(s.index.max().date()),
                    )
                )
                continue
            prices[ticker] = s
            logs.append(
                FetchResult(
                    ticker=ticker,
                    group=group,
                    api_symbol=api_symbol,
                    status="ok",
                    message="",
                    n_points=int(s.shape[0]),
                    start=str(s.index.min().date()),
                    end=str(s.index.max().date()),
                )
            )
        except RateLimitError as exc:
            logs.append(
                FetchResult(
                    ticker=ticker,
                    group=group,
                    api_symbol=api_symbol,
                    status="rate_limited",
                    message=str(exc),
                    n_points=0,
                    start=None,
                    end=None,
                )
            )
            rate_limited = True
            break
        except Exception as exc:  # pragma: no cover - defensive
            logs.append(
                FetchResult(
                    ticker=ticker,
                    group=group,
                    api_symbol=api_symbol,
                    status="error",
                    message=str(exc),
                    n_points=0,
                    start=None,
                    end=None,
                )
            )

    return prices, logs, rate_limited


def _read_local_close(csv_path: Path) -> pd.Series:
    df = pd.read_csv(csv_path)
    date_col = None
    for c in ("date", "Date", "datetime", "Datetime", "timestamp"):
        if c in df.columns:
            date_col = c
            break
    if date_col is None:
        raise RuntimeError("missing date column")

    price_col = None
    for c in ("price", "close", "Close", "adj_close", "Adj Close", "adjclose"):
        if c in df.columns:
            price_col = c
            break
    if price_col is None:
        raise RuntimeError("missing price/close column")

    dt = pd.to_datetime(df[date_col], errors="coerce")
    close = pd.to_numeric(df[price_col], errors="coerce")
    out = pd.Series(close.to_numpy(dtype=float), index=dt, name="close")
    out = out[~out.index.isna()].sort_index()
    out = out[~out.index.duplicated(keep="last")]
    out = out.dropna()
    if out.empty:
        raise RuntimeError("no valid close values in local csv")
    return out


def _fetch_universe_local(
    universe: list[dict[str, str]],
    min_points: int,
) -> tuple[dict[str, pd.Series], list[FetchResult], bool]:
    prices: dict[str, pd.Series] = {}
    logs: list[FetchResult] = []

    for row in universe:
        ticker = row["ticker"]
        group = row["group"]
        candidates = [ticker]
        if ticker.startswith("^"):
            candidates.append(ticker[1:])
        else:
            candidates.append("^" + ticker)
        csv_path = None
        chosen = None
        for c in candidates:
            p = LOCAL_PRICES_DIR / f"{c}.csv"
            if p.exists():
                csv_path = p
                chosen = c
                break
        if csv_path is None:
            logs.append(
                FetchResult(
                    ticker=ticker,
                    group=group,
                    api_symbol=ticker,
                    status="missing_local_file",
                    message=f"not found in {LOCAL_PRICES_DIR}",
                    n_points=0,
                    start=None,
                    end=None,
                )
            )
            continue

        try:
            s = _read_local_close(csv_path)
            if s.shape[0] < min_points:
                logs.append(
                    FetchResult(
                        ticker=ticker,
                        group=group,
                        api_symbol=str(chosen),
                        status="skip_low_history",
                        message=f"points<{min_points}",
                        n_points=int(s.shape[0]),
                        start=str(s.index.min().date()),
                        end=str(s.index.max().date()),
                    )
                )
                continue
            prices[ticker] = s
            logs.append(
                FetchResult(
                    ticker=ticker,
                    group=group,
                    api_symbol=str(chosen),
                    status="ok",
                    message="local_csv",
                    n_points=int(s.shape[0]),
                    start=str(s.index.min().date()),
                    end=str(s.index.max().date()),
                )
            )
        except Exception as exc:
            logs.append(
                FetchResult(
                    ticker=ticker,
                    group=group,
                    api_symbol=str(chosen),
                    status="error",
                    message=str(exc),
                    n_points=0,
                    start=None,
                    end=None,
                )
            )

    return prices, logs, False


def _build_returns_panel(prices: dict[str, pd.Series]) -> pd.DataFrame:
    rets: dict[str, pd.Series] = {}
    for ticker, s in prices.items():
        r = np.log(s).diff()
        r = r.replace([np.inf, -np.inf], np.nan).dropna()
        if not r.empty:
            rets[ticker] = r
    if not rets:
        return pd.DataFrame()
    panel = pd.concat(rets, axis=1, sort=False)
    panel = panel.sort_index()
    # Keep business days only to avoid weekend-induced coverage artifacts
    # when mixing crypto (7d) with exchange-traded assets (5d).
    panel = panel[panel.index.dayofweek < 5]
    return panel


def _rolling_spectral_state(
    returns_panel: pd.DataFrame,
    window: int,
    coverage_min: float,
    min_assets: int,
) -> tuple[pd.DataFrame, pd.DataFrame | None, np.ndarray | None]:
    if returns_panel.empty:
        return pd.DataFrame(), None, None

    dates = pd.Index(sorted(pd.to_datetime(returns_panel.index).unique()))
    states: list[dict[str, Any]] = []
    latest_corr: pd.DataFrame | None = None
    latest_eig: np.ndarray | None = None

    min_obs = max(30, int(window * 0.60))
    for end_idx in range(window - 1, len(dates)):
        w_dates = dates[end_idx - window + 1 : end_idx + 1]
        block = returns_panel.reindex(w_dates)
        coverage = block.notna().mean(axis=0)
        keep = coverage[coverage >= coverage_min].index.tolist()
        if len(keep) < min_assets:
            continue

        aligned = block[keep].dropna(how="any")
        if aligned.shape[0] < min_obs or aligned.shape[1] < min_assets:
            continue

        corr = aligned.corr()
        c = corr.to_numpy(dtype=float)
        if not np.all(np.isfinite(c)):
            continue

        eig = np.sort(np.linalg.eigvalsh(c))[::-1]
        eig = np.real(eig)
        sum_l = float(np.sum(eig))
        sum_l2 = float(np.sum(np.square(eig)))
        if sum_l <= 0.0 or sum_l2 <= 0.0:
            continue

        lambda1 = float(eig[0])
        p1 = float(lambda1 / sum_l)
        deff = float((sum_l * sum_l) / sum_l2)
        states.append(
            {
                "date": pd.Timestamp(w_dates[-1]).date().isoformat(),
                "n_used": int(aligned.shape[1]),
                "lambda1": lambda1,
                "p1": p1,
                "deff": deff,
            }
        )
        latest_corr = corr
        latest_eig = eig

    return pd.DataFrame(states), latest_corr, latest_eig


def _hierarchical_clusters_latest(corr: pd.DataFrame) -> pd.DataFrame | None:
    try:
        from scipy.cluster.hierarchy import fcluster, leaves_list, linkage
        from scipy.spatial.distance import squareform
    except Exception:
        return None

    c = corr.to_numpy(dtype=float)
    c = np.clip(c, -1.0, 1.0)
    dist = np.sqrt(np.clip(2.0 * (1.0 - c), 0.0, None))
    np.fill_diagonal(dist, 0.0)
    condensed = squareform(dist, checks=False)
    z = linkage(condensed, method="average")
    cluster_id = fcluster(z, t=1.0, criterion="distance")
    order = leaves_list(z)
    leaf_rank = np.empty_like(order)
    leaf_rank[order] = np.arange(order.size)

    out = pd.DataFrame(
        {
            "asset": corr.index.astype(str),
            "cluster_id": cluster_id.astype(int),
            "leaf_rank": leaf_rank.astype(int),
        }
    )
    return out.sort_values(["cluster_id", "leaf_rank"]).reset_index(drop=True)


def _write_outputs(
    outdir: Path,
    universe: list[dict[str, str]],
    fetch_logs: list[FetchResult],
    states: pd.DataFrame,
    corr_latest: pd.DataFrame | None,
    eig_latest: np.ndarray | None,
    clusters_latest: pd.DataFrame | None,
    window: int,
    coverage_min: float,
    rate_limited: bool,
    data_source: str,
) -> None:
    outdir.mkdir(parents=True, exist_ok=True)

    payload = {
        "data_source": str(data_source),
        "window": int(window),
        "coverage_min": float(coverage_min),
        "rate_limited": bool(rate_limited),
        "requested_universe": universe,
        "fetch_log": [f.__dict__ for f in fetch_logs],
    }
    (outdir / "universe.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    states.to_csv(outdir / "daily_state.csv", index=False)

    if corr_latest is not None:
        corr_latest.to_csv(outdir / "corr_latest.csv", index=True)
    if eig_latest is not None:
        eig_df = pd.DataFrame(
            {
                "rank": np.arange(1, len(eig_latest) + 1, dtype=int),
                "lambda": eig_latest,
            }
        )
        eig_df.to_csv(outdir / "eig_latest.csv", index=False)
    if clusters_latest is not None:
        clusters_latest.to_csv(outdir / "clusters_latest.csv", index=False)

    report_lines: list[str] = []
    report_lines.append("Assyntrax macro correlation lab")
    report_lines.append(f"run_dir: {outdir}")
    report_lines.append(f"data_source: {data_source}")
    report_lines.append(f"rate_limited: {rate_limited}")
    report_lines.append(f"window: {window}")
    report_lines.append(f"requested_assets: {len(universe)}")
    ok_assets = sum(1 for f in fetch_logs if f.status == "ok")
    report_lines.append(f"fetched_assets_ok: {ok_assets}")
    if not states.empty:
        report_lines.append(f"state_rows: {len(states)}")
        report_lines.append(f"period: {states['date'].iloc[0]} -> {states['date'].iloc[-1]}")
        report_lines.append(f"n_used_mean: {float(states['n_used'].mean()):.2f}")
        report_lines.append(f"latest_p1: {float(states['p1'].iloc[-1]):.6f}")
        report_lines.append(f"latest_deff: {float(states['deff'].iloc[-1]):.6f}")
    else:
        report_lines.append("state_rows: 0")
    (outdir / "report.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Macro lab: rolling correlation spectral state from Twelve Data.")
    parser.add_argument("--outdir", type=str, default=str(OUT_BASE))
    parser.add_argument("--source", type=str, default="auto", choices=["auto", "api", "local"])
    parser.add_argument("--window", type=int, default=120)
    parser.add_argument("--coverage-min", type=float, default=0.80)
    parser.add_argument("--max-assets", type=int, default=60)
    parser.add_argument("--min-assets", type=int, default=8)
    parser.add_argument("--min-points", type=int, default=756)
    args = parser.parse_args()

    run_id = _utc_run_id()
    outdir = Path(args.outdir) / run_id
    universe = _load_universe(max_assets=int(args.max_assets))
    source = str(args.source).strip().lower()
    if source == "auto":
        source = "local" if LOCAL_PRICES_DIR.exists() else "api"

    if source == "local":
        prices, fetch_logs, rate_limited = _fetch_universe_local(
            universe=universe,
            min_points=int(args.min_points),
        )
    else:
        api_key = os.environ.get("TWELVE_DATA_API_KEY", "").strip()
        if not api_key:
            raise SystemExit("Missing TWELVE_DATA_API_KEY env var. Export it and rerun.")
        prices, fetch_logs, rate_limited = _fetch_universe(
            universe=universe,
            api_key=api_key,
            min_points=int(args.min_points),
        )

    if len(prices) < int(args.min_assets):
        msg = (
            f"Insufficient assets after fetch: got {len(prices)} usable assets, "
            f"need at least {int(args.min_assets)}."
        )
        _write_outputs(
            outdir=outdir,
            universe=universe,
            fetch_logs=fetch_logs,
            states=pd.DataFrame(),
            corr_latest=None,
            eig_latest=None,
            clusters_latest=None,
            window=int(args.window),
            coverage_min=float(args.coverage_min),
            rate_limited=rate_limited,
            data_source=source,
        )
        (outdir / "report.txt").write_text(msg + "\n", encoding="utf-8")
        raise SystemExit(msg)

    panel = _build_returns_panel(prices)
    states, corr_latest, eig_latest = _rolling_spectral_state(
        returns_panel=panel,
        window=int(args.window),
        coverage_min=float(args.coverage_min),
        min_assets=int(args.min_assets),
    )
    if states.empty or corr_latest is None or eig_latest is None:
        _write_outputs(
            outdir=outdir,
            universe=universe,
            fetch_logs=fetch_logs,
            states=pd.DataFrame(),
            corr_latest=None,
            eig_latest=None,
            clusters_latest=None,
            window=int(args.window),
            coverage_min=float(args.coverage_min),
            rate_limited=rate_limited,
            data_source=source,
        )
        (outdir / "report.txt").write_text("No valid rolling states produced.\n", encoding="utf-8")
        raise SystemExit("No valid rolling states produced.")

    clusters_latest = _hierarchical_clusters_latest(corr_latest)
    _write_outputs(
        outdir=outdir,
        universe=universe,
        fetch_logs=fetch_logs,
        states=states,
        corr_latest=corr_latest,
        eig_latest=eig_latest,
        clusters_latest=clusters_latest,
        window=int(args.window),
        coverage_min=float(args.coverage_min),
        rate_limited=rate_limited,
        data_source=source,
    )
    print(f"[lab_corr] status=ok run_dir={outdir}")


if __name__ == "__main__":
    main()
