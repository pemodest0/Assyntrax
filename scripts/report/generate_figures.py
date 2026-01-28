import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def safe_name(name):
    return (
        name.replace("/", "_")
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("__", "_")
    )


def load_annual_backtest(path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def compute_metrics(real, pred):
    real = np.array(real, dtype=float)
    pred = np.array(pred, dtype=float)
    mask = ~np.isnan(real) & ~np.isnan(pred)
    if not mask.any():
        return None
    real = real[mask]
    pred = pred[mask]
    mae = float(np.mean(np.abs(pred - real)))
    rmse = float(np.sqrt(np.mean((pred - real) ** 2)))
    mape = float(np.mean(np.abs((pred - real) / real)) * 100) if np.all(real != 0) else None
    return {"mae": mae, "rmse": rmse, "mape": mape}


def plot_real_vs_pred(years, real, pred, mape, out_path, y_label="MWmed"):
    plt.figure(figsize=(8, 4.5))
    years = np.array(years)
    real_arr = np.array(real, dtype=float)
    pred_arr = np.array(pred, dtype=float)

    mask_real = ~np.isnan(real_arr)
    plt.plot(years[mask_real], real_arr[mask_real], color="black", label="real")
    plt.plot(years, pred_arr, color="red", label="previsto")

    if 2025 in years:
        plt.axvline(2025, color="gray", linestyle="--", linewidth=1)
        plt.text(2025 + 0.1, np.nanmax(pred_arr), "2025 so previsao", fontsize=9)

    title_mape = f"MAPE 2010-2024 = {mape:.2f}%" if mape is not None else "MAPE 2010-2024 = N/A"
    plt.title(f"Real vs Previsto (anual) | {title_mape}")
    plt.xlabel("Ano")
    plt.ylabel(y_label)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_pct_error(years, real, pred, out_path):
    years = np.array(years)
    real_arr = np.array(real, dtype=float)
    pred_arr = np.array(pred, dtype=float)
    mask = ~np.isnan(real_arr)
    err_pct = 100 * (pred_arr[mask] - real_arr[mask]) / real_arr[mask]
    colors = ["#ef4444" if abs(v) > 10 else "#38bdf8" for v in err_pct]

    plt.figure(figsize=(8, 4))
    plt.bar(years[mask], err_pct, color=colors)
    plt.axhline(0, color="black", linewidth=1)
    plt.title("Erro percentual por ano (previsto vs real)")
    plt.xlabel("Ano")
    plt.ylabel("Erro (%)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_table(years, real, pred, out_path):
    rows = []
    for year, r, p in zip(years, real, pred):
        if math.isnan(r) and math.isnan(p):
            continue
        err_abs = None if math.isnan(r) or math.isnan(p) else p - r
        err_pct = None if math.isnan(r) or math.isnan(p) else 100 * (p - r) / r
        rows.append([
            int(year),
            "-" if math.isnan(r) else f"{r:.2f}",
            "-" if math.isnan(p) else f"{p:.2f}",
            "-" if err_abs is None else f"{err_abs:.2f}",
            "-" if err_pct is None else f"{err_pct:.2f}%",
        ])

    fig, ax = plt.subplots(figsize=(8, 0.4 * max(6, len(rows))))
    ax.axis("off")
    table = ax.table(
        cellText=rows,
        colLabels=["ano", "real", "previsto", "erro_abs", "erro_pct"],
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.2)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_recent(real_df, forecast_df, subsystem, mape_2024, out_path):
    if subsystem not in real_df.columns or subsystem not in forecast_df.columns:
        return False

    real_df = real_df.copy()
    forecast_df = forecast_df.copy()
    real_df["date"] = pd.to_datetime(real_df["date"])
    forecast_df["date"] = pd.to_datetime(forecast_df["date"])

    real_recent = real_df.tail(180)
    forecast_recent = forecast_df.head(180)

    plt.figure(figsize=(9, 4))
    plt.plot(real_recent["date"], real_recent[subsystem], color="black", label="real (ultimos 180 dias)")
    plt.plot(forecast_recent["date"], forecast_recent[subsystem], color="red", label="previsto 2025")

    if mape_2024 is not None:
        band = mape_2024 / 100.0
        upper = forecast_recent[subsystem] * (1 + band)
        lower = forecast_recent[subsystem] * (1 - band)
        plt.fill_between(forecast_recent["date"], lower, upper, color="red", alpha=0.15)

    plt.title("Trecho final: real vs previsto (com banda simples)")
    plt.xlabel("Data")
    plt.ylabel("MWmed")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    return True


def plot_attractor_2d(points, title, out_path):
    plt.figure(figsize=(6, 6))
    plt.scatter(points[:, 0], points[:, 1], s=4, alpha=0.6)
    plt.title(title)
    plt.xlabel("x(t)")
    plt.ylabel("x(t-tau)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_attractor_3d(points, title, out_path):
    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(points[:, 0], points[:, 1], points[:, 2], s=2, alpha=0.6)
    ax.set_title(title)
    ax.set_xlabel("x(t)")
    ax.set_ylabel("x(t-tau)")
    ax.set_zlabel("x(t-2tau)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def knn_predict_one(X_train, y_train, x_query, k):
    if len(X_train) < k:
        return None
    dists = np.linalg.norm(X_train - x_query, axis=1)
    idx = np.argpartition(dists, k - 1)[:k]
    weights = 1.0 / (dists[idx] + 1e-6)
    return float(np.sum(y_train[idx] * weights) / np.sum(weights))


def annual_backtest_knn(years, values, tau=2, m=4, k=10):
    years = np.array(years, dtype=int)
    values = np.array(values, dtype=float)
    start = (m - 1) * tau
    X = []
    y = []
    target_years = []
    for i in range(start, len(values) - 1):
        row = [values[i - j * tau] for j in range(m)]
        X.append(row)
        y.append(values[i + 1])
        target_years.append(years[i + 1])
    if not X:
        return {}
    X = np.array(X)
    y = np.array(y)
    target_years = np.array(target_years)

    preds = {}
    for i, target_year in enumerate(target_years):
        train_mask = target_years < target_year
        if train_mask.sum() < k:
            continue
        pred = knn_predict_one(X[train_mask], y[train_mask], X[i], k)
        preds[target_year] = pred

    # 2025 forecast
    if years[-1] >= 2024:
        query_idx = len(values) - 1
        if query_idx - (m - 1) * tau >= 0 and len(X) >= k:
            query = np.array([values[query_idx - j * tau] for j in range(m)])
            pred_2025 = knn_predict_one(X, y, query, k)
            if pred_2025 is not None:
                preds[2025] = pred_2025
    return preds


def detect_date_column(columns):
    candidates = ["date", "datetime", "timestamp", "time"]
    lower_map = {col.lower(): col for col in columns}
    for cand in candidates:
        for key, col in lower_map.items():
            if cand == key or key.endswith(cand):
                return col
    return None


def detect_price_column(columns):
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


def find_yfinance_files(base_dir, custom_path=None):
    if custom_path:
        root = Path(custom_path)
        if root.is_file():
            return [root]
        if root.is_dir():
            return list(root.rglob("*.csv"))
        return []

    candidates = []
    for root, _, files in os.walk(base_dir):
        if any(part in root for part in ["venv", "site-packages", "website", "results", ".git"]):
            continue
        for name in files:
            if not name.lower().endswith(".csv"):
                continue
            if any(tag in root.lower() for tag in ["market_data", "yf", "yfinance", "yahoo"]):
                candidates.append(Path(root) / name)
    return candidates


def load_price_series(path, mode="log"):
    df = pd.read_csv(path)
    date_col = detect_date_column(df.columns)
    price_col = detect_price_column(df.columns)
    if not date_col or not price_col:
        return None, None, None
    df = df[[date_col, price_col]].copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col, price_col])
    df = df.sort_values(date_col)
    prices = df[price_col].astype(float).values
    if mode == "returns":
        values = np.diff(np.log(prices))
        dates = df[date_col].iloc[1:].values
    else:
        values = np.log(prices)
        dates = df[date_col].values
    return dates, values, {"date_col": date_col, "price_col": price_col}


def generate_energy(outdir, annual_path):
    base_dir = Path(__file__).resolve().parents[1]
    outdir.mkdir(parents=True, exist_ok=True)
    annual = load_annual_backtest(annual_path)
    if not annual:
        print("annual_backtest_2010_2025.json not found. Exiting.")
        return

    manifest_path = base_dir / "website" / "assets" / "spa_energy" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    embed_meta = manifest.get("embedding_meta", {})

    real_daily_path = base_dir / "website" / "assets" / "spa_energy" / "daily_2000_2024.csv"
    forecast_daily_path = base_dir / "website" / "assets" / "spa_energy" / "forecast_2025_daily.csv"
    real_daily = pd.read_csv(real_daily_path) if real_daily_path.exists() else None
    forecast_daily = pd.read_csv(forecast_daily_path) if forecast_daily_path.exists() else None

    summary_lines = []

    for subsystem, rows in annual.get("data", {}).items():
        years = []
        real = []
        pred = []
        for row in rows:
            years.append(row["year"])
            real.append(float("nan") if row["real_mean"] is None else float(row["real_mean"]))
            pred.append(float("nan") if row["pred_mean"] is None else float(row["pred_mean"]))

        metrics = compute_metrics(real, pred)
        mape = metrics["mape"] if metrics else None

        sub_dir = outdir / safe_name(subsystem)
        sub_dir.mkdir(parents=True, exist_ok=True)

        plot_real_vs_pred(years, real, pred, mape, sub_dir / "real_vs_pred_annual.png")
        plot_pct_error(years, real, pred, sub_dir / "pct_error_annual.png")
        plot_table(years, real, pred, sub_dir / "table_annual.png")

        if real_daily is not None and forecast_daily is not None:
            plot_recent(
                real_daily,
                forecast_daily,
                subsystem,
                mape,
                sub_dir / "real_vs_pred_recent.png",
            )

        safe_sub = subsystem.replace("/", "_").replace(" ", "_")
        attr_path = base_dir / "website" / "assets" / "spa_energy" / f"attractor_daily_{safe_sub}.json"
        if attr_path.exists():
            with attr_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            points = np.array([[p["x"], p["y"], p["z"]] for p in data])
            if points.shape[0] > 5000:
                points = points[:: int(points.shape[0] / 5000)]
            meta = embed_meta.get(subsystem, {}).get("daily", {})
            tau = meta.get("tau", "n/a")
            m = meta.get("m", "n/a")
            plot_attractor_2d(
                points[:, :2],
                f"Embedding 2D (tau={tau}, m={m})",
                sub_dir / "attractor_2d.png",
            )
            plot_attractor_3d(
                points[:, :3],
                f"Embedding 3D (tau={tau}, m={m})",
                sub_dir / "attractor_3d.png",
            )

        metrics_text = "MAE/RMSE/MAPE: N/A"
        if metrics and metrics["mape"] is not None:
            metrics_text = f"MAE={metrics['mae']:.2f}, RMSE={metrics['rmse']:.2f}, MAPE={metrics['mape']:.2f}%"

        worst_year = None
        worst_err = None
        for year, r, p in zip(years, real, pred):
            if math.isnan(r) or math.isnan(p) or r == 0:
                continue
            err_pct = abs(100 * (p - r) / r)
            if worst_err is None or err_pct > worst_err:
                worst_err = err_pct
                worst_year = year

        real_vals = [r for y, r in zip(years, real) if not math.isnan(r) and 2010 <= y <= 2024]
        mean_real = float(np.mean(real_vals)) if real_vals else None
        pred_2025 = None
        for y, p in zip(years, pred):
            if y == 2025:
                pred_2025 = p
                break

        delta_2025 = None
        if mean_real is not None and pred_2025 is not None:
            delta_2025 = 100 * (pred_2025 - mean_real) / mean_real

        summary_lines.append(
            f"{subsystem}: periodo 2010-2024 | {metrics_text} | pior ano={worst_year} ({worst_err:.2f}%) | "
            f"2025 previsto={pred_2025:.2f} | vs media={delta_2025:.2f}%"
        )

    print("Resumo por subsistema")
    for line in summary_lines:
        print(line)


def generate_yfinance(outdir, tickers, yfinance_path=None, mode="log", tau=2, m=4, k=10):
    base_dir = Path(__file__).resolve().parents[1]
    outdir.mkdir(parents=True, exist_ok=True)

    files = find_yfinance_files(base_dir, yfinance_path)
    if not files:
        print("No yfinance CSVs found.")
        return {}, []

    file_map = {}
    for path in files:
        ticker = path.stem.replace("_cleaned", "").upper()
        file_map.setdefault(ticker, []).append(path)

    if tickers:
        selected = [t for t in tickers if t in file_map]
    else:
        counts = []
        for ticker, paths in file_map.items():
            max_rows = 0
            for path in paths:
                try:
                    rows = sum(1 for _ in path.open("r", encoding="utf-8", errors="ignore")) - 1
                    max_rows = max(max_rows, rows)
                except OSError:
                    continue
            counts.append((max_rows, ticker))
        counts.sort(reverse=True)
        selected = [ticker for _, ticker in counts[:3]]

    summaries = []
    for ticker in selected:
        paths = file_map.get(ticker, [])
        if not paths:
            continue

        path = paths[0]
        dates, values, meta = load_price_series(path, mode=mode)
        if dates is None:
            print(f"{ticker}: missing date/price columns in {path}")
            continue

        years = pd.to_datetime(dates).year
        annual = pd.Series(values).groupby(years).mean()
        years_sorted = annual.index.values.astype(int)
        values_sorted = annual.values.astype(float)

        preds = annual_backtest_knn(years_sorted, values_sorted, tau=tau, m=m, k=k)
        if not preds:
            print(f"{ticker}: insufficient data for backtest")
            continue

        min_year = max(2010, years_sorted.min())
        max_year = min(2024, years_sorted.max())
        years_eval = [y for y in years_sorted if min_year <= y <= max_year]
        years_plot = years_eval + ([2025] if 2025 in preds else [])

        real = []
        pred = []
        for y in years_plot:
            real_val = float("nan")
            if y in years_sorted:
                real_val = float(values_sorted[list(years_sorted).index(y)])
            pred_val = preds.get(y, float("nan"))
            real.append(real_val)
            pred.append(pred_val)

        metrics = compute_metrics(real[:-1] if years_plot[-1] == 2025 else real, pred[:-1] if years_plot[-1] == 2025 else pred)
        mape = metrics["mape"] if metrics else None

        sub_dir = outdir / safe_name(ticker)
        sub_dir.mkdir(parents=True, exist_ok=True)

        y_label = "log(preco)" if mode == "log" else "log-retorno"
        plot_real_vs_pred(years_plot, real, pred, mape, sub_dir / "real_vs_pred_annual.png", y_label=y_label)
        plot_pct_error(years_plot, real, pred, sub_dir / "pct_error_annual.png")
        plot_table(years_plot, real, pred, sub_dir / "table_annual.png")

        worst_year = None
        worst_err = None
        errors = []
        for year, r, p in zip(years_plot, real, pred):
            if math.isnan(r) or math.isnan(p) or r == 0 or year == 2025:
                continue
            err_pct = 100 * (p - r) / r
            errors.append(err_pct)
            if worst_err is None or abs(err_pct) > abs(worst_err):
                worst_err = err_pct
                worst_year = year

        bias = float(np.mean(errors)) if errors else None
        n_years = len([y for y in years_plot if y != 2025])
        period = f"{min_year}-{max_year}"
        metrics_text = "MAE/RMSE/MAPE: N/A"
        if metrics and metrics["mape"] is not None:
            metrics_text = f"MAE={metrics['mae']:.4f}, RMSE={metrics['rmse']:.4f}, MAPE={metrics['mape']:.2f}%"
        bias_text = f"{bias:.2f}%" if bias is not None else "N/A"
        summaries.append(
            f"{ticker}: periodo {period} | N anos={n_years} | {metrics_text} | pior ano={worst_year} | bias medio={bias_text}"
        )

    print("Resumo por ticker")
    for line in summaries:
        print(line)
    return file_map, selected


def main():
    parser = argparse.ArgumentParser(description="Generate PNG figures for SPA.")
    parser.add_argument("--domain", default="energy", choices=["energy", "yfinance", "yfinance_daily"])
    parser.add_argument("--outdir", default=None, help="Output directory.")
    parser.add_argument("--annual-backtest", default="website/assets/spa_energy/annual_backtest_2010_2025.json")
    parser.add_argument("--ticker", default=None, help="Comma-separated list of tickers.")
    parser.add_argument("--all", action="store_true", help="Use all detected tickers.")
    parser.add_argument("--yfinance-path", default=None, help="Optional path to yfinance CSVs.")
    parser.add_argument("--mode", default="log", choices=["log", "returns"], help="yfinance observable mode.")
    parser.add_argument("--train-end", default="2024-12-31")
    parser.add_argument("--test-start", default="2025-01-01")
    parser.add_argument("--test-end", default="2025-12-31")
    parser.add_argument("--H-short", type=int, default=5)
    parser.add_argument("--H-long", type=int, default=60)
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    if args.domain == "energy":
        outdir = base_dir / (args.outdir or "results/_figs/energy")
        annual_path = base_dir / args.annual_backtest
        generate_energy(outdir, annual_path)
        return
    if args.domain == "yfinance_daily":
        cmd = [
            sys.executable,
            str(base_dir / "scripts" / "yf_chaos_benchmark.py"),
            "--train-end",
            args.train_end,
            "--test-start",
            args.test_start,
            "--test-end",
            args.test_end,
            "--H-short",
            str(args.H_short),
            "--H-long",
            str(args.H_long),
        ]
        if args.ticker:
            cmd.extend(["--tickers", args.ticker])
        subprocess.run(cmd, check=True)
        return

    tickers = []
    if args.ticker:
        tickers = [t.strip().upper() for t in args.ticker.split(",") if t.strip()]
    outdir = base_dir / (args.outdir or "results/_figs/yfinance")
    if args.all:
        tickers = []
    generate_yfinance(outdir, tickers, args.yfinance_path, mode=args.mode)


if __name__ == "__main__":
    main()
