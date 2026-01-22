import argparse
import json
import os
import re
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def infer_sep(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        sample = f.read(4096)
    try:
        import csv

        return csv.Sniffer().sniff(sample).delimiter
    except Exception:
        return ","


def normalize_numeric(series):
    s = series.astype(str)
    s = s.str.replace(".", "", regex=False)
    s = s.str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def normalize_series(x, med=None, mad=None, q_low=None, q_high=None):
    x = np.asarray(x, dtype=float)
    if med is None:
        med = np.nanmedian(x)
    if mad is None:
        mad = np.nanmedian(np.abs(x - med))
    if mad == 0 or not np.isfinite(mad):
        mad = np.nanstd(x) if np.nanstd(x) else 1.0
    z = (x - med) / (mad + 1e-9)
    if q_low is None or q_high is None:
        q_low = np.nanpercentile(z, 1)
        q_high = np.nanpercentile(z, 99)
    z = np.clip(z, q_low, q_high)
    return z, med, mad, q_low, q_high


def denormalize_series(z, med, mad):
    return z * (mad + 1e-9) + med


def ami_curve(series, max_tau=60, bins=32):
    series = np.asarray(series, dtype=float)
    max_tau = min(max_tau, max(2, len(series) // 5))
    mi = []
    for tau in range(1, max_tau + 1):
        x = series[:-tau]
        y = series[tau:]
        hist, _, _ = np.histogram2d(x, y, bins=bins)
        pxy = hist / np.sum(hist)
        px = np.sum(pxy, axis=1)
        py = np.sum(pxy, axis=0)
        denom = px[:, None] * py[None, :]
        nz = (pxy > 0) & (denom > 0)
        mi_val = np.sum(pxy[nz] * np.log(pxy[nz] / denom[nz]))
        mi.append(mi_val)
    return np.array(mi)


def first_local_min(values):
    if len(values) < 3:
        return int(np.argmin(values)) + 1
    for i in range(1, len(values) - 1):
        if values[i] < values[i - 1] and values[i] < values[i + 1]:
            return i + 1
    return int(np.argmin(values)) + 1


def fnn_curve(series, tau, max_m=12, rtol=10.0, atol=2.0):
    series = np.asarray(series, dtype=float)
    max_m = min(max_m, 12)
    fnn = []
    for m in range(1, max_m + 1):
        start = (m - 1) * tau
        end = len(series) - tau
        if end - start <= 2:
            fnn.append(1.0)
            continue
        X = []
        Xp1 = []
        for i in range(start, end):
            X.append([series[i - j * tau] for j in range(m)])
            Xp1.append([series[i - j * tau] for j in range(m + 1)])
        X = np.array(X)
        Xp1 = np.array(Xp1)
        dists = np.linalg.norm(X[:, None, :] - X[None, :, :], axis=2)
        np.fill_diagonal(dists, np.inf)
        nn = np.argmin(dists, axis=1)
        dist_m = dists[np.arange(len(nn)), nn]
        dist_m[dist_m == 0] = 1e-9
        dist_mp1 = np.linalg.norm(Xp1 - Xp1[nn], axis=1)
        std_m = np.std(X, axis=0).mean()
        fnn_mask = (np.abs(dist_mp1 - dist_m) / dist_m > rtol) | (dist_mp1 / std_m > atol if std_m else True)
        fnn.append(float(np.mean(fnn_mask)))
    return np.array(fnn)


def select_tau_m(series, max_tau=60, max_m=12, bins=32, fnn_threshold=0.02):
    try:
        ami = ami_curve(series, max_tau=max_tau, bins=bins)
        tau = first_local_min(ami)
    except Exception:
        tau = 2
    try:
        fnn = fnn_curve(series, tau=tau, max_m=max_m)
        m_sel = None
        for i, v in enumerate(fnn):
            if v < fnn_threshold:
                m_sel = i + 1
                break
        if m_sel is None:
            m_sel = int(np.argmin(fnn)) + 1
        m = m_sel
    except Exception:
        m = 6
    if tau <= 0:
        tau = 2
    if m <= 1:
        m = 6
    return tau, m


def build_embedding(series, tau, m, max_h):
    series = np.asarray(series, dtype=float)
    start = (m - 1) * tau
    end = len(series) - max_h
    X = []
    idx_t = []
    for i in range(start, end):
        X.append([series[i - j * tau] for j in range(m)])
        idx_t.append(i)
    if not X:
        return None, None
    return np.array(X), np.array(idx_t)


def knn_predict_direct(
    series,
    dates,
    tau,
    m,
    k,
    train_end_date,
    test_year,
    horizons,
    max_test_points=400,
    max_train_points=None,
    n_jobs=1,
):
    try:
        from sklearn.neighbors import NearestNeighbors
    except Exception:
        NearestNeighbors = None

    max_h = max(horizons)
    X, idx_t = build_embedding(series, tau, m, max_h)
    if X is None:
        return {}, {}

    dates = np.array(dates, dtype="datetime64[D]")
    train_end_dt = np.datetime64(train_end_date.date())
    year_start = np.datetime64(f"{test_year}-01-01")
    year_end = np.datetime64(f"{test_year}-12-31")

    preds = {h: {} for h in horizons}
    reals = {}

    for h in horizons:
        y = series[idx_t + h]
        train_mask = dates[idx_t + h] <= train_end_dt
        test_mask = (dates[idx_t] >= year_start) & (dates[idx_t + h] <= year_end)

        X_train = X[train_mask]
        y_train = y[train_mask]
        X_test = X[test_mask]
        idx_test = idx_t[test_mask]

        if max_train_points and len(X_train) > max_train_points:
            pick = np.linspace(0, len(X_train) - 1, max_train_points, dtype=int)
            X_train = X_train[pick]
            y_train = y_train[pick]

        if len(idx_test) > max_test_points:
            pick = np.linspace(0, len(idx_test) - 1, max_test_points, dtype=int)
            idx_test = idx_test[pick]
            X_test = X[np.isin(idx_t, idx_test)]

        if len(X_train) < k or len(X_test) == 0:
            continue

        X_train = X_train.astype(np.float32, copy=False)
        X_test = X_test.astype(np.float32, copy=False)
        mean = X_train.mean(axis=0)
        std = X_train.std(axis=0)
        std[std == 0] = 1.0
        X_train = (X_train - mean) / std
        X_test = (X_test - mean) / std

        if NearestNeighbors is not None:
            nbrs = NearestNeighbors(n_neighbors=k, algorithm="auto", n_jobs=n_jobs)
            nbrs.fit(X_train)
            dists, inds = nbrs.kneighbors(X_test)
            weights = 1.0 / (dists + 1e-9)
            weights_sum = np.sum(weights, axis=1)
            pred_vals = np.sum(y_train[inds] * weights, axis=1) / weights_sum
        else:
            pred_vals = []
            for xq in X_test:
                d = np.linalg.norm(X_train - xq, axis=1)
                sel = np.argpartition(d, k - 1)[:k]
                w = 1.0 / (d[sel] + 1e-9)
                pred_vals.append(float(np.sum(y_train[sel] * w) / np.sum(w)))
            pred_vals = np.array(pred_vals)

        for pred, t_idx in zip(pred_vals, idx_test):
            target_date = dates[t_idx + h]
            preds[h][target_date] = float(pred)
            reals[target_date] = float(series[t_idx + h])

    return preds, reals


def baseline_preds(series, dates, test_year, horizons):
    preds = {h: {} for h in horizons}
    reals = {}
    for h in horizons:
        for i in range(h, len(series)):
            date_t = dates[i]
            if date_t.year != test_year:
                continue
            real = series[i]
            base = series[i - h]
            preds[h][date_t] = base
            reals[date_t] = real
    return preds, reals


def baseline_ma20(series, dates, test_year, horizons, window=20):
    preds = {h: {} for h in horizons}
    reals = {}
    for h in horizons:
        for i in range(h, len(series)):
            date_t = dates[i]
            if date_t.year != test_year:
                continue
            start = max(0, i - h - window + 1)
            base = np.mean(series[start : i - h + 1])
            preds[h][date_t] = float(base)
            reals[date_t] = series[i]
    return preds, reals


def metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    err = y_pred - y_true
    mae = float(np.nanmean(np.abs(err))) if len(err) else np.nan
    rmse = float(np.sqrt(np.nanmean(err ** 2))) if len(err) else np.nan
    bias = float(np.nanmean(err)) if len(err) else np.nan
    mape = np.nan
    smape = np.nan
    nonzero = y_true != 0
    if np.any(nonzero):
        mape = float(np.nanmean(np.abs(err[nonzero] / y_true[nonzero])) * 100.0)
    denom = np.abs(y_true) + np.abs(y_pred)
    nonzero = denom != 0
    if np.any(nonzero):
        smape = float(np.nanmean(2 * np.abs(err[nonzero]) / denom[nonzero]) * 100.0)
    return {"mae": mae, "rmse": rmse, "mape": mape, "bias": bias, "smape": smape}


def plot_real_vs_pred(dates, real, pred, out_path, title):
    plt.figure(figsize=(10, 4))
    plt.plot(dates, real, label="Real", color="#1f77b4", linewidth=1.2)
    plt.plot(dates, pred, label="Previsto", color="#d62728", linewidth=1.2)
    plt.title(title)
    plt.xlabel("Data")
    plt.ylabel("Valor")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def plot_error_hist(errors, out_path, title):
    plt.figure(figsize=(7, 4))
    plt.hist(errors, bins=60, color="#555555", alpha=0.85)
    plt.title(title)
    plt.xlabel("Erro")
    plt.ylabel("Frequencia")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def plot_metric_over_years(metrics_by_year, out_path, title):
    years = sorted(metrics_by_year.keys())
    mae = [metrics_by_year[y]["mae"] for y in years]
    rmse = [metrics_by_year[y]["rmse"] for y in years]
    mape = [metrics_by_year[y]["mape"] for y in years]
    plt.figure(figsize=(8, 4))
    plt.plot(years, mae, label="MAE")
    plt.plot(years, rmse, label="RMSE")
    plt.plot(years, mape, label="MAPE")
    plt.title(title)
    plt.xlabel("Ano")
    plt.ylabel("Erro")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def plot_skill_over_years(skill_by_year, out_path, title):
    years = sorted(skill_by_year.keys())
    skill = [skill_by_year[y] for y in years]
    plt.figure(figsize=(8, 4))
    plt.plot(years, skill, marker="o", linewidth=1.2)
    plt.axhline(0, color="#333333", linewidth=0.8)
    plt.title(title)
    plt.xlabel("Ano")
    plt.ylabel("Skill")
    plt.tight_layout()
    plt.savefig(out_path, dpi=160)
    plt.close()


def load_energy_series():
    base = os.path.join("data", "raw", "ONS", "ons_carga_diaria", "ons_carga_diaria_2000_2026.csv")
    if not os.path.exists(base):
        raise FileNotFoundError("Arquivo de energia nao encontrado.")
    sep = infer_sep(base)
    df = pd.read_csv(base, sep=sep, dtype=str)
    df["din_instante"] = pd.to_datetime(df["din_instante"], errors="coerce")
    df["val_cargaenergiamwmed"] = normalize_numeric(df["val_cargaenergiamwmed"])
    df = df.dropna(subset=["din_instante", "val_cargaenergiamwmed", "nom_subsistema"])
    df = df.sort_values("din_instante")
    return df


def load_yfinance_series(ticker, cache_dir):
    from scripts.yf_fetch_or_load import find_local_data, load_price_series, fetch_yfinance, unify_to_daily, save_cache

    ensure_dir(cache_dir)
    cache_path = os.path.join(cache_dir, f"{ticker}.csv")
    if os.path.exists(cache_path):
        df = pd.read_csv(cache_path)
        if "date" in df.columns and "r" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            return df

    candidates = find_local_data(ticker, ".")
    df = None
    if candidates:
        df = load_price_series(candidates[0])
    if df is None:
        df = fetch_yfinance(ticker, start="2010-01-01", end=None)
    if df is None:
        return None
    df = unify_to_daily(df)
    df.to_csv(cache_path, index=False)
    save_cache(df, ".", ticker)
    return df


def resample_series(dates, values, freq, mode="mean"):
    s = pd.Series(values, index=pd.to_datetime(dates))
    if freq == "daily":
        return s.index.to_pydatetime(), s.values
    if freq == "weekly":
        rule = "W"
    else:
        rule = "M"
    if mode == "sum":
        s = s.resample(rule).sum()
    else:
        s = s.resample(rule).mean()
    s = s.dropna()
    return s.index.to_pydatetime(), s.values


def build_targets(source, targets):
    target_list = []
    if source == "energy":
        df = load_energy_series()
        subs_map = {
            "N": "Norte",
            "NE": "Nordeste",
            "S": "Sul",
            "SECO": "Sudeste/Centro-Oeste",
        }
        for key, name in subs_map.items():
            if "ALL" in targets or key in targets:
                df_sub = df[df["nom_subsistema"] == name].copy()
                dates = df_sub["din_instante"].to_numpy()
                values = df_sub["val_cargaenergiamwmed"].to_numpy()
                target_list.append({"name": f"energy_{key}_level", "dates": dates, "values": values, "kind": "level"})
                delta = np.diff(values)
                target_list.append({"name": f"energy_{key}_delta", "dates": dates[1:], "values": delta, "kind": "delta"})
    else:
        for ticker in targets:
            df = load_yfinance_series(ticker, "data/yfinance_cache")
            if df is None:
                continue
            dates = df["date"].to_numpy()
            values = df["r"].to_numpy()
            target_list.append({"name": f"yfinance_{ticker}", "dates": dates, "values": values, "kind": "returns"})
    return target_list


def parse_targets(targets_str, source):
    if source == "energy":
        if targets_str == "energy:ALL":
            return ["ALL"]
        parts = targets_str.replace("energy:", "")
        return [p.strip().upper() for p in parts.split(",") if p.strip()]
    parts = targets_str.replace("yfinance:", "")
    return [p.strip() for p in parts.split(",") if p.strip()]


def auto_name(source, freq, model, start_year, end_year):
    return f"{source}_{freq}_{model}_{start_year}_{end_year}"


def safe_name(name):
    text = re.sub(r"[^A-Za-z0-9_\\-]+", "_", str(name))
    return text.strip("_") or "target"


def write_report(report_path, config, target_summaries, ranking):
    lines = []
    lines.append('# Walk-forward Backtest Report\n')
    lines.append('## Configuracao\n')
    for k, v in config.items():
        lines.append(f'- {k}: {v}\n')
    lines.append('\n## Ranking (menor MAPE medio)\n')
    for item in ranking:
        lines.append(f'- {item["target"]}: {item["mape_mean"]:.4f}\n')
    for target in target_summaries:
        lines.append(f'\n## Target: {target["name"]}\n')
        lines.append(f'- output_dir: {target["out_dir"]}\n')
        lines.append(f'- tau: {target["tau"]}, m: {target["m"]}\n')
        if "sanity" in target:
            s = target["sanity"]
            lines.append('\n### Sanity checks\n')
            lines.append(f'- n_obs: {s.get("n_obs")}\n')
            lines.append(f'- n_nan: {s.get("n_nan")}\n')
            lines.append(f'- min: {s.get("min")}\n')
            lines.append(f'- max: {s.get("max")}\n')
            lines.append(f'- median: {s.get("median")}\n')
            lines.append(f'- mad: {s.get("mad")}\n')
            lines.append(f'- outliers_5mad: {s.get("outliers_5mad")}\n')
        lines.append('\n### Metricas por ano\n\n')
        lines.append('| Ano | h | MAE | RMSE | MAPE | Bias | sMAPE | Skill |\n')
        lines.append('|---|---|---|---|---|---|---|---|\n')
        for year, mh in target.get("metrics_by_h", {}).items():
            for h, m in mh.items():
                skill = target["skill_by_year"].get(year, float('nan')) if h == target.get("h1", 1) else float('nan')
                lines.append(
                    f'| {year} | {h} | {m["mae"]:.4f} | {m["rmse"]:.4f} | {m["mape"]:.4f} | {m["bias"]:.4f} | {m["smape"]:.4f} | {skill:.4f} |\n'
                )
        lines.append('\n### Plots\n')
        lines.append(f'- metric_over_years.png: {os.path.join(target["out_dir"], "metric_over_years.png")}\n')
        lines.append(f'- skill_over_years.png: {os.path.join(target["out_dir"], "skill_over_years.png")}\n')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

def load_safe_mode(path="config/safe_mode.json"):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_years_range(text):
    if not text or ":" not in text:
        return None, None
    parts = text.split(":")
    if len(parts) != 2:
        return None, None
    start = int(parts[0])
    end = int(parts[1])
    return start, end


def main():


    parser = argparse.ArgumentParser(description="Walk-forward backtest anual")
    parser.add_argument("--source", required=True, choices=["energy", "yfinance"])
    parser.add_argument("--targets", required=True)
    parser.add_argument("--freq", default="daily", choices=["daily", "weekly", "monthly"])
    parser.add_argument("--start_year", type=int, default=2010)
    parser.add_argument("--end_year", type=int, default=2025)
    parser.add_argument("--model", default="knn_phase")
    parser.add_argument("--tau", default="auto")
    parser.add_argument("--m", default="auto")
    parser.add_argument("--k", type=int, default=20)
    parser.add_argument("--horizons", default="1,5,20,60")
    parser.add_argument("--max-test-points", type=int, default=400)
    parser.add_argument("--max-train-points", type=int, default=4000)
    parser.add_argument("--safe", action="store_true")
    parser.add_argument("--years", default="")
    parser.add_argument("--per-year-plots", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    if args.years:
        y_start, y_end = parse_years_range(args.years)
        if y_start and y_end:
            args.start_year = y_start
            args.end_year = y_end

    if args.safe:
        safe_cfg = load_safe_mode()
        args.max_train_points = int(safe_cfg.get("max_points_train", args.max_train_points))
        args.max_test_points = int(safe_cfg.get("max_points_test", args.max_test_points))
        max_years = int(safe_cfg.get("max_years", 0))
        if max_years > 0:
            span = args.end_year - args.start_year + 1
            if span > max_years:
                args.start_year = args.end_year - max_years + 1
        max_plots = int(safe_cfg.get("max_plots_per_run", 0))
        disable_per_year_plots = bool(safe_cfg.get("disable_per_year_plots", True))
        n_jobs = int(safe_cfg.get("n_jobs", 1))
    else:
        max_plots = 0
        disable_per_year_plots = True
        n_jobs = 1
    if args.per_year_plots:
        disable_per_year_plots = False

    horizons = [int(h) for h in args.horizons.split(",") if h.strip()]
    targets = parse_targets(args.targets, args.source)
    out_dir = args.out.replace("<auto_name>", auto_name(args.source, args.freq, args.model, args.start_year, args.end_year))
    ensure_dir(out_dir)

    target_list = build_targets(args.source, targets)
    target_summaries = []
    ranking_rows = []
    plot_count = 0

    for target in target_list:
        name = target["name"]
        kind = target["kind"]
        dates, values = target["dates"], target["values"]
        resample_mode = "sum" if kind in ("returns", "delta") else "mean"
        dates, values = resample_series(dates, values, args.freq, mode=resample_mode)
        out_target = os.path.join(out_dir, safe_name(name))
        ensure_dir(out_target)

        sanity = {
            'n_obs': int(len(values)),
            'n_nan': int(np.isnan(values).sum()) if hasattr(values, '__len__') else 0,
            'min': float(np.nanmin(values)) if len(values) else np.nan,
            'max': float(np.nanmax(values)) if len(values) else np.nan,
            'median': float(np.nanmedian(values)) if len(values) else np.nan,
            'mad': float(np.nanmedian(np.abs(values - np.nanmedian(values)))) if len(values) else np.nan,
            'outliers_5mad': int(np.sum(np.abs(values - np.nanmedian(values)) > 5 * (np.nanmedian(np.abs(values - np.nanmedian(values))) + 1e-9))) if len(values) else 0,
        }

        metrics_by_year = {}
        metrics_by_h = {}
        skill_by_year = {}

        tau = args.tau
        m = args.m
        if tau == "auto" or m == "auto":
            mask_auto = np.array([d <= datetime(args.end_year - 1, 12, 31) for d in dates])
            z_auto = values[mask_auto]
            if len(z_auto) > 0:
                z_auto, _, _, _, _ = normalize_series(z_auto, None, None, None, None)
                tau_sel, m_sel = select_tau_m(z_auto, max_tau=60, max_m=12, bins=32, fnn_threshold=0.02)
            else:
                tau_sel, m_sel = 2, 6
        else:
            tau_sel = int(tau)
            m_sel = int(m)

        for year in range(args.start_year, args.end_year + 1):
            t0 = time.time()
            train_end = datetime(year - 1, 12, 31)
            test_year = year
            mask_train = np.array([d <= train_end for d in dates])
            if not mask_train.any():
                continue
            train_values = values[mask_train]

            z_train, med, mad, q_low, q_high = normalize_series(train_values, None, None, None, None)
            z_all, _, _, _, _ = normalize_series(values, med, mad, q_low, q_high)

            cache_dir = os.path.join(out_target, "cache")
            ensure_dir(cache_dir)
            cache_path = os.path.join(cache_dir, f"train_{year}.npz")
            if os.path.exists(cache_path):
                cached = np.load(cache_path, allow_pickle=False)
                z_all = cached["z_all"]
                dates_np = cached["dates"]
                tau_sel = int(cached["tau"])
                m_sel = int(cached["m"])
            else:
                dates_np = np.array(dates)
                np.savez(
                    cache_path,
                    z_all=z_all.astype(np.float32, copy=False),
                    dates=dates_np.astype("datetime64[D]"),
                    tau=np.array([tau_sel]),
                    m=np.array([m_sel]),
                )

            preds, reals = knn_predict_direct(
                z_all,
                dates_np,
                tau_sel,
                m_sel,
                args.k,
                train_end,
                test_year,
                horizons,
                max_test_points=args.max_test_points,
                max_train_points=args.max_train_points,
                n_jobs=n_jobs,
            )
            base_p, _ = baseline_preds(z_all, np.array(dates), test_year, horizons)
            ma_p, _ = baseline_ma20(z_all, np.array(dates), test_year, horizons)

            year_dir = os.path.join(out_target, str(year))
            ensure_dir(year_dir)
            all_dates = sorted(set(reals.keys()))
            if not all_dates:
                continue
            pred_rows = []
            for dt in all_dates:
                row = {"date": dt}
                row["y_true"] = denormalize_series(reals[dt], med, mad)
                for h in horizons:
                    if dt in preds.get(h, {}):
                        row[f"y_pred_h{h}"] = denormalize_series(preds[h][dt], med, mad)
                    else:
                        row[f"y_pred_h{h}"] = np.nan
                pred_rows.append(row)
            df_pred = pd.DataFrame(pred_rows)
            df_pred.to_csv(os.path.join(year_dir, f"predictions_{year}.csv"), index=False)

            metrics_by_h[year] = {}
            for h in horizons:
                y_true = np.array([reals[d] for d in all_dates if d in preds.get(h, {})])
                y_pred = np.array([preds[h][d] for d in all_dates if d in preds.get(h, {})])
                if len(y_true) == 0:
                    continue
                m_h = metrics(denormalize_series(y_true, med, mad), denormalize_series(y_pred, med, mad))
                base_vals = np.array([base_p[h].get(d, np.nan) for d in all_dates if d in preds.get(h, {})])
                base_vals = base_vals[~np.isnan(base_vals)]
                if len(base_vals) == len(y_true):
                    m_base = metrics(denormalize_series(y_true, med, mad), denormalize_series(base_vals, med, mad))
                    base_mae = m_base["mae"]
                else:
                    base_mae = np.nan
                if base_mae and base_mae == base_mae:
                    m_h["skill_vs_persistence"] = (base_mae - m_h["mae"]) / base_mae
                else:
                    m_h["skill_vs_persistence"] = np.nan
                metrics_by_h[year][h] = m_h

                if not disable_per_year_plots:
                    if h in (horizons[0], 20) or h == horizons[-1]:
                        if max_plots == 0 or plot_count < max_plots:
                            plot_real_vs_pred(
                                all_dates[: len(y_pred)],
                                denormalize_series(y_true, med, mad),
                                denormalize_series(y_pred, med, mad),
                                os.path.join(year_dir, f"real_vs_pred_{year}_h{h}.png"),
                                f"Real vs Pred (h={h}) - {year}",
                            )
                            plot_count += 1

            if horizons[0] in metrics_by_h[year]:
                h1 = horizons[0]
                y_true_h1 = np.array([reals[d] for d in all_dates if d in preds.get(h1, {})])
                y_pred_h1 = np.array([preds[h1][d] for d in all_dates if d in preds.get(h1, {})])
                metrics_by_year[year] = metrics_by_h[year][h1]
                date_list = [d for d in all_dates if d in preds.get(h1, {})]
                base = np.array([base_p[h1].get(d, np.nan) for d in date_list], dtype=float)
                ma_base = np.array([ma_p[h1].get(d, np.nan) for d in date_list], dtype=float)
                base_m = metrics(denormalize_series(y_true_h1, med, mad), denormalize_series(base, med, mad))
                ma_m = metrics(denormalize_series(y_true_h1, med, mad), denormalize_series(ma_base, med, mad))
                best_base_mae = min(base_m["mae"], ma_m["mae"]) if base_m["mae"] and ma_m["mae"] else base_m["mae"]
                skill = (best_base_mae - metrics_by_year[year]["mae"]) / best_base_mae if best_base_mae else np.nan
                skill_by_year[year] = skill

                if not disable_per_year_plots:
                    if max_plots == 0 or plot_count < max_plots:
                        plot_error_hist(
                            denormalize_series(y_pred_h1, med, mad) - denormalize_series(y_true_h1, med, mad),
                            os.path.join(year_dir, f"error_hist_{year}.png"),
                            f"Erro (h={h1}) - {year}",
                        )
                        plot_count += 1

            print(f"[{name}] ano {year} concluido em {time.time() - t0:.1f}s")
            del preds, reals

        if metrics_by_year:
            if max_plots == 0 or plot_count < max_plots:
                plot_metric_over_years(
                    metrics_by_year,
                    os.path.join(out_target, "metric_over_years.png"),
                    f"Metricas por ano - {name}",
                )
                plot_count += 1
            if max_plots == 0 or plot_count < max_plots:
                plot_skill_over_years(
                    skill_by_year,
                    os.path.join(out_target, "skill_over_years.png"),
                    f"Skill por ano - {name}",
                )
                plot_count += 1

        mape_mean = np.nanmean([m["mape"] for m in metrics_by_year.values()]) if metrics_by_year else np.nan
        ranking_rows.append({"target": name, "mape_mean": mape_mean})
        target_summaries.append(
            {
                "name": name,
                "out_dir": out_target,
                "tau": tau_sel,
                "m": m_sel,
                "metrics_by_year": metrics_by_year,
                "skill_by_year": skill_by_year,
                "metrics_by_h": metrics_by_h,
                "h1": horizons[0],
                "sanity": sanity,
            }
        )

    ranking_rows = sorted(ranking_rows, key=lambda x: x["mape_mean"] if x["mape_mean"] == x["mape_mean"] else 1e9)
    report_path = os.path.join(out_dir, "REPORT.md")
    config = {
        "source": args.source,
        "targets": args.targets,
        "freq": args.freq,
        "start_year": args.start_year,
        "end_year": args.end_year,
        "model": args.model,
        "tau": args.tau,
        "m": args.m,
        "k": args.k,
        "horizons": args.horizons,
    }
    write_report(report_path, config, target_summaries, ranking_rows)

    summary_path = os.path.join(out_dir, "summary.json")
    summary = {"config": config, "targets": [], "ranking": ranking_rows}
    for target in target_summaries:
        mape_vals = [m["mape"] for m in target.get("metrics_by_year", {}).values() if m["mape"] == m["mape"]]
        mae_vals = [m["mae"] for m in target.get("metrics_by_year", {}).values() if m["mae"] == m["mae"]]
        rmse_vals = [m["rmse"] for m in target.get("metrics_by_year", {}).values() if m["rmse"] == m["rmse"]]
        summary["targets"].append(
            {
                "name": target["name"],
                "out_dir": target["out_dir"],
                "mape_mean": float(np.mean(mape_vals)) if mape_vals else None,
                "mae_mean": float(np.mean(mae_vals)) if mae_vals else None,
                "rmse_mean": float(np.mean(rmse_vals)) if rmse_vals else None,
                "years": sorted(list(target.get("metrics_by_year", {}).keys())),
            }
        )
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    ranking_rows = []
    for target in target_summaries:
        metrics_by_h = target.get("metrics_by_h", {})
        for h in horizons:
            mape_vals = []
            bias_vals = []
            skill_vals = []
            for year, mh in metrics_by_h.items():
                if h not in mh:
                    continue
                mape_vals.append(mh[h].get("mape"))
                bias_vals.append(mh[h].get("bias"))
                skill_vals.append(mh[h].get("skill_vs_persistence"))
            mape_vals = [v for v in mape_vals if v == v]
            bias_vals = [v for v in bias_vals if v == v]
            skill_vals = [v for v in skill_vals if v == v]
            if not mape_vals:
                continue
            ranking_rows.append(
                {
                    "target": target["name"],
                    "horizon": h,
                    "mape_mean": float(np.mean(mape_vals)),
                    "bias_mean": float(np.mean(bias_vals)) if bias_vals else np.nan,
                    "skill_vs_persistence_mean": float(np.mean(skill_vals)) if skill_vals else np.nan,
                }
            )

    if ranking_rows:
        ranking_rows = sorted(ranking_rows, key=lambda x: x["mape_mean"])
        ranking_csv = os.path.join(out_dir, "ranking_table.csv")
        pd.DataFrame(ranking_rows).to_csv(ranking_csv, index=False)
        ranking_md = os.path.join(out_dir, "RANKING.md")
        with open(ranking_md, "w", encoding="utf-8") as f:
            f.write("# Ranking consolidado\n\n")
            f.write("| Target | Horizonte | MAPE medio | Skill vs persistencia | Bias medio |\n")
            f.write("|---|---|---|---|---|\n")
            for row in ranking_rows:
                f.write(
                    f'| {row["target"]} | {row["horizon"]} | {row["mape_mean"]:.4f} | {row["skill_vs_persistence_mean"]:.4f} | {row["bias_mean"]:.4f} |\n'
                )

    print(report_path)


if __name__ == "__main__":
    main()
