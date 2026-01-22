import argparse
import json
import math
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sys as _sys_mod
_sys_mod.modules.setdefault("pyarrow", None)
import pandas as pd

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.yf_fetch_or_load import find_local_data, load_price_series, fetch_yfinance, unify_to_daily, save_cache
from spa.features.phase_features import compute_phase_features
from spa.models.baselines import persistence_next, zero_mean_next, ar1_fit, ar1_predict


def safe_name(name):
    return name.replace("/", "_").replace("^", "").replace(" ", "_")


def embed(series, tau, m):
    series = np.asarray(series, dtype=float)
    start = (m - 1) * tau
    X = []
    y = []
    idx = []
    for i in range(start, len(series) - 1):
        X.append([series[i - j * tau] for j in range(m)])
        y.append(series[i + 1])
        idx.append(i + 1)
    if not X:
        return None, None, None
    return np.array(X), np.array(y), np.array(idx)


def zscore_fit(X):
    mean = X.mean(axis=0)
    std = X.std(axis=0)
    std[std == 0] = 1.0
    return mean, std


def zscore_apply(X, mean, std):
    return (X - mean) / std


def knn_predict_batch(X_train, y_train, X_query, k):
    preds = []
    for row in X_query:
        dists = np.linalg.norm(X_train - row, axis=1)
        idx = np.argpartition(dists, k - 1)[:k]
        weights = 1.0 / (dists[idx] + 1e-6)
        preds.append(float(np.sum(y_train[idx] * weights) / np.sum(weights)))
    return np.array(preds)


def choose_params(dates, returns, tau_grid, m_grid, k_grid, max_train=5000, max_val=2000):
    val_start = pd.Timestamp("2023-01-01")
    val_end = pd.Timestamp("2023-12-31")
    train_end = pd.Timestamp("2022-12-31")

    X_all = {}
    y_all = {}
    idx_all = {}

    best = None
    best_mae = None

    for tau in tau_grid:
        for m in m_grid:
            X, y, idx = embed(returns, tau, m)
            if X is None:
                continue
            X_all[(tau, m)] = X
            y_all[(tau, m)] = y
            idx_all[(tau, m)] = idx

            date_idx = dates[idx]
            train_mask = date_idx <= train_end
            val_mask = (date_idx >= val_start) & (date_idx <= val_end)
            if train_mask.sum() < 50 or val_mask.sum() < 50:
                continue

            X_train = X[train_mask]
            y_train = y[train_mask]
            X_val = X[val_mask]
            y_val = y[val_mask]

            if len(X_train) > max_train:
                sel = np.linspace(0, len(X_train) - 1, max_train).astype(int)
                X_train = X_train[sel]
                y_train = y_train[sel]
            if len(X_val) > max_val:
                sel = np.linspace(0, len(X_val) - 1, max_val).astype(int)
                X_val = X_val[sel]
                y_val = y_val[sel]

            mean, std = zscore_fit(X_train)
            X_train_z = zscore_apply(X_train, mean, std)
            X_val_z = zscore_apply(X_val, mean, std)

            for k in k_grid:
                if len(X_train_z) < k:
                    continue
                preds = knn_predict_batch(X_train_z, y_train, X_val_z, k)
                mae = float(np.mean(np.abs(preds - y_val)))
                if best_mae is None or mae < best_mae:
                    best_mae = mae
                    best = (tau, m, k, mean, std)

    if best is None:
        return 2, 4, 10, None, None
    return best


def predict_recursive(returns, start_index, tau, m, k, mean, std, X_train, y_train, H):
    state = np.array([returns[start_index - j * tau] for j in range(m)], dtype=float)
    preds = []
    for _ in range(H):
        state_z = (state - mean) / std
        dists = np.linalg.norm(X_train - state_z, axis=1)
        idx = np.argpartition(dists, k - 1)[:k]
        weights = 1.0 / (dists[idx] + 1e-6)
        next_val = float(np.sum(y_train[idx] * weights) / np.sum(weights))
        preds.append(next_val)
        state = np.concatenate([[next_val], state[:-1]])
    return np.array(preds)


def compute_horizon_errors(returns, dates, tau, m, k, mean, std, X_train, y_train, H_long, n_windows=50):
    test_start = pd.Timestamp("2025-01-01")
    test_end = pd.Timestamp("2025-12-31")
    idx = np.arange(len(returns))
    valid = idx[(dates >= test_start) & (dates <= test_end)]
    if len(valid) < H_long + 10:
        return None

    start_candidates = valid[: len(valid) - H_long]
    if len(start_candidates) == 0:
        return None

    picks = np.linspace(0, len(start_candidates) - 1, min(n_windows, len(start_candidates))).astype(int)
    starts = start_candidates[picks]

    mae = np.zeros(H_long)
    rmse = np.zeros(H_long)
    bias = np.zeros(H_long)
    counts = np.zeros(H_long)

    for start in starts:
        if start - (m - 1) * tau < 0:
            continue
        preds = predict_recursive(returns, start, tau, m, k, mean, std, X_train, y_train, H_long)
        real = returns[start + 1 : start + 1 + H_long]
        if len(real) < H_long:
            continue
        diff = preds - real
        mae += np.abs(diff)
        rmse += diff ** 2
        bias += diff
        counts += 1

    counts[counts == 0] = 1
    mae = mae / counts
    rmse = np.sqrt(rmse / counts)
    bias = bias / counts
    return mae, rmse, bias


def compute_baseline_errors(returns, dates, H_long):
    test_start = pd.Timestamp("2025-01-01")
    test_end = pd.Timestamp("2025-12-31")
    idx = np.arange(len(returns))
    valid = idx[(dates >= test_start) & (dates <= test_end)]
    if len(valid) < H_long + 10:
        return None

    start_candidates = valid[: len(valid) - H_long]
    picks = np.linspace(0, len(start_candidates) - 1, min(50, len(start_candidates))).astype(int)
    starts = start_candidates[picks]

    # Baselines are for 1-step only; use persistence/zero/ar1 for h=1 and hold for comparison at h1.
    mae_p, mae_z, mae_a = [], [], []
    a = ar1_fit(returns[dates <= pd.Timestamp("2024-12-31")])
    for start in starts:
        r0 = returns[start]
        r1 = returns[start + 1]
        mae_p.append(abs(r0 - r1))
        mae_z.append(abs(0 - r1))
        mae_a.append(abs(a * r0 - r1))
    return {
        "mae_persist": float(np.mean(mae_p)),
        "mae_zero": float(np.mean(mae_z)),
        "mae_ar1": float(np.mean(mae_a)),
        "ar1_a": float(a),
    }


def plot_attractor(X, title, out_path):
    if X.shape[0] > 8000:
        idx = np.linspace(0, X.shape[0] - 1, 8000).astype(int)
        X = X[idx]
    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(X[:, 0], X[:, 1], X[:, 2], c=np.arange(len(X)), cmap="viridis", s=2, alpha=0.7)
    ax.set_title(title)
    ax.set_xlabel("r(t)")
    ax.set_ylabel("r(t-tau)")
    ax.set_zlabel("r(t-2tau)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_short_window(dates, returns, prices, preds, start_idx, H, out_r, out_p):
    real_slice = returns[start_idx + 1 : start_idx + 1 + H]
    date_slice = dates[start_idx + 1 : start_idx + 1 + H]

    plt.figure(figsize=(8, 4))
    plt.plot(date_slice, real_slice, color="black", label="real")
    plt.plot(date_slice, preds, color="red", label="previsto")
    plt.title("Retornos: real vs previsto (curto prazo)")
    plt.xlabel("Data")
    plt.ylabel("r(t)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_r, dpi=150)
    plt.close()

    start_price = prices[start_idx]
    log_price = math.log(start_price)
    pred_log = log_price + np.cumsum(preds)
    pred_price = np.exp(pred_log)
    real_price = prices[start_idx + 1 : start_idx + 1 + H]

    plt.figure(figsize=(8, 4))
    plt.plot(date_slice, real_price, color="black", label="real")
    plt.plot(date_slice, pred_price, color="red", label="previsto")
    plt.title("Preco: real vs previsto (curto prazo)")
    plt.xlabel("Data")
    plt.ylabel("Preco")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_p, dpi=150)
    plt.close()


def plot_error_curve(mae, rmse, bias, out_path):
    h = np.arange(1, len(mae) + 1)
    plt.figure(figsize=(8, 4))
    plt.plot(h, mae, color="#f97316", label="MAE")
    plt.plot(h, rmse, color="#0ea5e9", label="RMSE")
    plt.plot(h, bias, color="#22c55e", label="Bias")
    plt.title("Erro vs horizonte")
    plt.xlabel("Horizonte (h)")
    plt.ylabel("Erro")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_compare_baselines(h, mae_curve, baselines, out_path):
    plt.figure(figsize=(8, 4))
    plt.plot(h, mae_curve, label="motor", color="#f97316")
    if baselines:
        plt.axhline(baselines["mae_persist"], color="#1d4ed8", linestyle="--", label="persistencia")
        plt.axhline(baselines["mae_zero"], color="#0f766e", linestyle="--", label="zero")
        plt.axhline(baselines["mae_ar1"], color="#6d28d9", linestyle="--", label="AR(1)")
    plt.title("Motor vs baselines (MAE)")
    plt.xlabel("Horizonte (h)")
    plt.ylabel("MAE")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_summary_table(summary, out_path):
    rows = [[k, v] for k, v in summary.items()]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.axis("off")
    table = ax.table(cellText=rows, colLabels=["campo", "valor"], cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.0)
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()


def horizon_estimate(mae_curve, train_returns):
    threshold = np.percentile(np.abs(train_returns), 95) * 0.5
    for idx, val in enumerate(mae_curve, start=1):
        if val > threshold:
            return idx
    return len(mae_curve)


def horizon_by_mae_ratio(mae_curve, ratio=2.0):
    base = mae_curve[0]
    if base <= 0:
        return len(mae_curve)
    for idx, val in enumerate(mae_curve, start=1):
        if val > ratio * base:
            return idx
    return len(mae_curve)


def run_for_ticker(ticker, base_dir, out_dir, cache_dir, train_end, test_start, test_end, H_short, H_long):
    local_candidates = find_local_data(ticker, base_dir)
    if (not local_candidates) and ticker.startswith("^"):
        local_candidates = find_local_data(ticker.replace("^", ""), base_dir)
    df = None
    for candidate in local_candidates or []:
        df = load_price_series(candidate)
        if df is not None:
            break
    if df is None:
        df = fetch_yfinance(ticker)
    if df is None:
        return None

    df = unify_to_daily(df)
    if df.empty:
        return None

    save_cache(df, base_dir, safe_name(ticker))

    dates = df["date"].to_numpy()
    returns = df["r"].to_numpy()
    prices = df["price"].to_numpy()

    tau_grid = [1, 2, 3, 5, 8, 13]
    m_grid = [2, 3, 4, 5, 6]
    k_grid = [5, 10, 20]

    tau, m, k, mean, std = choose_params(dates, returns, tau_grid, m_grid, k_grid)
    if mean is None or std is None:
        X, y, idx = embed(returns, tau, m)
        train_mask = dates[idx] <= pd.Timestamp(train_end)
        X_train = X[train_mask]
        y_train = y[train_mask]
        mean, std = zscore_fit(X_train)
    else:
        X, y, idx = embed(returns, tau, m)
        train_mask = dates[idx] <= pd.Timestamp(train_end)
        X_train = X[train_mask]
        y_train = y[train_mask]

    X_train_z = zscore_apply(X_train, mean, std)

    # Attractor 3D
    if X_train_z.shape[1] >= 3:
        plot_attractor(
            X_train_z[:, :3],
            f"{ticker} | tau={tau}, m={m}, k={k} | n={len(X_train_z)}",
            out_dir / "attractor_3d.png",
        )

    # Example short window in 2025
    test_mask = (dates >= pd.Timestamp(test_start)) & (dates <= pd.Timestamp(test_end))
    test_idx = np.where(test_mask)[0]
    if len(test_idx) == 0:
        return None
    mid_start = test_idx[len(test_idx) // 2]
    if mid_start - (m - 1) * tau < 0:
        mid_start = test_idx[0]

    preds_short = predict_recursive(returns, mid_start, tau, m, k, mean, std, X_train_z, y_train, H_short)
    plot_short_window(
        dates,
        returns,
        prices,
        preds_short,
        mid_start,
        H_short,
        out_dir / "returns_real_vs_pred_short.png",
        out_dir / "price_real_vs_pred_short.png",
    )

    # Bias histogram for 1-step and 5-step
    if len(test_idx) > H_long + 1:
        starts = test_idx[: len(test_idx) - 5]
        picks = np.linspace(0, len(starts) - 1, min(60, len(starts))).astype(int)
        starts = starts[picks]
        errs1 = []
        errs5 = []
        for start in starts:
            preds = predict_recursive(returns, start, tau, m, k, mean, std, X_train_z, y_train, 5)
            if len(preds) < 5:
                continue
            real = returns[start + 1 : start + 6]
            errs1.append(preds[0] - real[0])
            errs5.append(preds[4] - real[4])
        if errs1 and errs5:
            plt.figure(figsize=(8, 4))
            plt.hist(errs1, bins=20, alpha=0.6, label="erro 1-step")
            plt.hist(errs5, bins=20, alpha=0.6, label="erro 5-step")
            plt.title("Bias histogram (1-step vs 5-step)")
            plt.xlabel("erro")
            plt.ylabel("freq")
            plt.legend()
            plt.tight_layout()
            plt.savefig(out_dir / "bias_hist.png", dpi=150)
            plt.close()

    mae_curve, rmse_curve, bias_curve = compute_horizon_errors(
        returns,
        dates,
        tau,
        m,
        k,
        mean,
        std,
        X_train_z,
        y_train,
        H_long,
    )
    if mae_curve is None:
        return None

    plot_error_curve(mae_curve, rmse_curve, bias_curve, out_dir / "error_vs_horizon.png")

    baseline = compute_baseline_errors(returns, dates, H_long)
    if baseline:
        baseline_best = min(baseline["mae_persist"], baseline["mae_zero"], baseline["mae_ar1"])
    else:
        baseline_best = float("nan")

    plot_compare_baselines(np.arange(1, len(mae_curve) + 1), mae_curve, baseline, out_dir / "compare_baselines.png")

    horizon_est = horizon_estimate(mae_curve, returns[dates <= pd.Timestamp(train_end)])
    horizon_mae2 = horizon_by_mae_ratio(mae_curve, ratio=2.0)
    summary = {
        "tau": tau,
        "m": m,
        "k": k,
        "MAE_h1": float(mae_curve[0]),
        "MAE_h2": float(mae_curve[1]) if len(mae_curve) >= 2 else float("nan"),
        "MAE_h5": float(mae_curve[4]) if len(mae_curve) >= 5 else float("nan"),
        "MAE_h10": float(mae_curve[9]) if len(mae_curve) >= 10 else float("nan"),
        "MAE_h20": float(mae_curve[19]) if len(mae_curve) >= 20 else float("nan"),
        "MAE_h60": float(mae_curve[59]) if len(mae_curve) >= 60 else float("nan"),
        "RMSE_h1": float(rmse_curve[0]),
        "RMSE_h2": float(rmse_curve[1]) if len(rmse_curve) >= 2 else float("nan"),
        "RMSE_h5": float(rmse_curve[4]) if len(rmse_curve) >= 5 else float("nan"),
        "RMSE_h10": float(rmse_curve[9]) if len(rmse_curve) >= 10 else float("nan"),
        "RMSE_h20": float(rmse_curve[19]) if len(rmse_curve) >= 20 else float("nan"),
        "RMSE_h60": float(rmse_curve[59]) if len(rmse_curve) >= 60 else float("nan"),
        "horizon_est": int(horizon_est),
        "horizon_mae2": int(horizon_mae2),
        "bias_h1": float(bias_curve[0]),
        "bias_h2": float(bias_curve[1]) if len(bias_curve) >= 2 else float("nan"),
        "bias_h5": float(bias_curve[4]) if len(bias_curve) >= 5 else float("nan"),
        "bias_h10": float(bias_curve[9]) if len(bias_curve) >= 10 else float("nan"),
        "bias_h20": float(bias_curve[19]) if len(bias_curve) >= 20 else float("nan"),
        "bias_h60": float(bias_curve[59]) if len(bias_curve) >= 60 else float("nan"),
        "train_n": int(train_mask.sum()),
        "test_n": int(test_mask.sum()),
        "baseline_persist": baseline["mae_persist"] if baseline else float("nan"),
        "baseline_zero": baseline["mae_zero"] if baseline else float("nan"),
        "baseline_ar1": baseline["mae_ar1"] if baseline else float("nan"),
        "baseline_best": baseline_best,
        "gain_pct": float(100 * (baseline_best - mae_curve[0]) / baseline_best) if baseline_best and baseline_best > 0 else float("nan"),
        "passed_baseline": bool(mae_curve[0] < baseline_best) if baseline_best == baseline_best else False,
    }

    plot_summary_table(summary, out_dir / "summary_table.png")

    metrics = {
        "ticker": ticker,
        "tau": tau,
        "m": m,
        "k": k,
        "mae_curve": mae_curve.tolist(),
        "rmse_curve": rmse_curve.tolist(),
        "bias_curve": bias_curve.tolist(),
        "horizon_est": int(horizon_est),
        "horizon_mae2": int(horizon_mae2),
        "baseline": baseline,
        "train_n": int(train_mask.sum()),
        "test_n": int(test_mask.sum()),
        "train_end": train_end,
        "test_start": test_start,
        "test_end": test_end,
    }
    with (out_dir / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    forecast_df = pd.DataFrame(
        {
            "date": dates[mid_start + 1 : mid_start + 1 + H_short],
            "r_real": returns[mid_start + 1 : mid_start + 1 + H_short],
            "r_pred": preds_short,
            "price_real": prices[mid_start + 1 : mid_start + 1 + H_short],
        }
    )
    start_price = prices[mid_start]
    forecast_df["price_pred"] = np.exp(np.log(start_price) + np.cumsum(preds_short))
    forecast_df.to_csv(out_dir / "forecast_examples.csv", index=False)

    # Phase features
    phase_df = compute_phase_features(returns, dates, tau=tau, m=m, window=252, delta=1)
    if phase_df is not None and not phase_df.empty:
        phase_df.to_csv(out_dir / "phase_features.csv", index=False)

        train_mask_pf = phase_df["date"] <= pd.Timestamp(train_end)
        train_pf = phase_df[train_mask_pf]
        test_pf = phase_df[~train_mask_pf]

        thresholds = {}
        for col in ["raio_rms", "drift_local"]:
            thresholds[col] = float(np.nanpercentile(train_pf[col], 95)) if not train_pf.empty else np.nan

        phase_df["regime_alert"] = (
            (phase_df["raio_rms"] > thresholds["raio_rms"])
            & (phase_df["drift_local"] > thresholds["drift_local"])
        )

        # phase_timeseries.png
        fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
        axes[0].plot(phase_df["date"], phase_df["raio_rms"], label="raio_rms")
        axes[0].plot(phase_df["date"], phase_df["drift_local"], label="drift_local")
        axes[0].legend()
        axes[0].set_title("Raio RMS e drift local")

        axes[1].plot(phase_df["date"], phase_df["anisotropia"], label="anisotropia")
        axes[1].plot(phase_df["date"], phase_df["divergence_rate"], label="divergence_rate")
        axes[1].legend()
        axes[1].set_title("Anisotropia e divergence_rate")

        axes[2].plot(phase_df["date"], phase_df["autocorr"], label="autocorr")
        axes[2].legend()
        axes[2].set_title("Autocorr(r_t, r_{t-1})")
        plt.tight_layout()
        plt.savefig(out_dir / "phase_timeseries.png", dpi=150)
        plt.close()

        # regime_flags.png
        plt.figure(figsize=(10, 3))
        plt.plot(phase_df["date"], phase_df["regime_alert"].astype(int), color="#ef4444")
        plt.title("Regime flags (drift_local & raio_rms > limiar)")
        plt.xlabel("Data")
        plt.ylabel("alerta")
        plt.tight_layout()
        plt.savefig(out_dir / "regime_flags.png", dpi=150)
        plt.close()

        alerts_2025 = int(phase_df[phase_df["date"].dt.year == 2025]["regime_alert"].sum())

        print(
            f"{ticker} phase features (train percentiles): "
            f"raio_rms p50/p95={np.nanpercentile(train_pf['raio_rms'], 50):.4f}/"
            f"{np.nanpercentile(train_pf['raio_rms'], 95):.4f}, "
            f"drift_local p50/p95={np.nanpercentile(train_pf['drift_local'], 50):.4f}/"
            f"{np.nanpercentile(train_pf['drift_local'], 95):.4f} | "
            f"alerts_2025={alerts_2025}"
        )
        summary["alerts_2025"] = alerts_2025
    else:
        alerts_2025 = 0

    return summary


def main():
    parser = argparse.ArgumentParser(description="YFinance chaos benchmark (daily).")
    parser.add_argument("--tickers", default="", help="Comma-separated tickers.")
    parser.add_argument("--train-end", default="2024-12-31")
    parser.add_argument("--test-start", default="2025-01-01")
    parser.add_argument("--test-end", default="2025-12-31")
    parser.add_argument("--H-short", type=int, default=5)
    parser.add_argument("--H-long", type=int, default=60)
    parser.add_argument("--outdir", default=None, help="Base output dir for figures.")
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    out_base = Path(args.outdir) if args.outdir else (base_dir / "results" / "_figs" / "yfinance_daily")
    out_base.mkdir(parents=True, exist_ok=True)
    cache_dir = base_dir / "results" / "_tmp" / "yfinance_daily"
    cache_dir.mkdir(parents=True, exist_ok=True)

    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
    if not tickers:
        tickers = ["SPY", "QQQ", "IWM", "TLT", "GLD", "USO", "XLE", "AAPL", "MSFT", "NVDA", "^VIX", "BTC-USD"]

    summary_rows = []
    start_time = time.time()
    for ticker in tickers:
        out_dir = out_base / safe_name(ticker)
        out_dir.mkdir(parents=True, exist_ok=True)
        summary = run_for_ticker(
            ticker,
            base_dir,
            out_dir,
            cache_dir,
            args.train_end,
            args.test_start,
            args.test_end,
            args.H_short,
            args.H_long,
        )
        if summary is None:
            continue
        summary_rows.append(
            {
                "ticker": ticker,
                "tau": summary["tau"],
                "m": summary["m"],
                "k": summary["k"],
                "MAE1": summary["MAE_h1"],
                "MAE2": summary["MAE_h2"],
                "MAE5": summary["MAE_h5"],
                "MAE10": summary["MAE_h10"],
                "MAE20": summary["MAE_h20"],
                "MAE60": summary["MAE_h60"],
                "RMSE1": summary["RMSE_h1"],
                "RMSE2": summary["RMSE_h2"],
                "RMSE5": summary["RMSE_h5"],
                "RMSE10": summary["RMSE_h10"],
                "RMSE20": summary["RMSE_h20"],
                "RMSE60": summary["RMSE_h60"],
                "bias1": summary["bias_h1"],
                "bias2": summary["bias_h2"],
                "bias5": summary["bias_h5"],
                "bias10": summary["bias_h10"],
                "bias20": summary["bias_h20"],
                "bias60": summary["bias_h60"],
                "horizon_est": summary["horizon_est"],
                "horizon_mae2": summary["horizon_mae2"],
                "alerts_2025": summary.get("alerts_2025", 0),
                "train_n": summary["train_n"],
                "test_n": summary["test_n"],
                "baseline_persist": summary["baseline_persist"],
                "baseline_zero": summary["baseline_zero"],
                "baseline_ar1": summary["baseline_ar1"],
                "baseline_best": summary["baseline_best"],
                "gain_pct": summary["gain_pct"],
                "passed_baseline": summary["passed_baseline"],
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    summary_path = out_base / "benchmark_summary.csv"
    summary_df.to_csv(summary_path, index=False)

    if not summary_df.empty:
        ranked = summary_df.sort_values("MAE20")
        print("Top 5 mais previsiveis (menor MAE20)")
        print(ranked.head(5).to_string(index=False))
        print("Top 5 menos previsiveis (maior MAE20)")
        print(ranked.tail(5).to_string(index=False))

    elapsed = time.time() - start_time
    print(f"Tempo total: {elapsed:.2f}s")


if __name__ == "__main__":
    main()
