import argparse
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from spa.sanity import ensure_sorted_dates, safe_test_indices, split_hash, validate_time_split
import sys as _sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in _sys.path:
    _sys.path.insert(0, str(ROOT))

from spa.models.takens_knn import TakensKNN, embed
from spa.features.phase_features import compute_phase_features


def safe_name(name):
    return name.replace("/", "_").replace("^", "").replace(" ", "_")


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def plot_attractor(X, title, out_path):
    if X.shape[0] > 8000:
        idx = np.linspace(0, X.shape[0] - 1, 8000).astype(int)
        X = X[idx]
    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(X[:, 0], X[:, 1], X[:, 2], c=np.arange(len(X)), cmap="viridis", s=2, alpha=0.7)
    ax.set_title(title)
    ax.set_xlabel("x(t)")
    ax.set_ylabel("x(t-tau)")
    ax.set_zlabel("x(t-2tau)")
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
    pred_log = math.log(start_price) + np.cumsum(preds)
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


def plot_error_curve(mae, rmse, out_path):
    h = np.arange(1, len(mae) + 1)
    plt.figure(figsize=(8, 4))
    plt.plot(h, mae, color="#f97316", label="MAE")
    plt.plot(h, rmse, color="#0ea5e9", label="RMSE")
    if "bias" in out_path.name:
        pass
    plt.title("Erro vs horizonte")
    plt.xlabel("Horizonte (h)")
    plt.ylabel("Erro")
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_error_curve_with_bias(mae, rmse, bias, out_path):
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


def plot_summary_table(summary, out_path):
    rows = [[k, v] for k, v in summary.items()]
    fig, ax = plt.subplots(figsize=(6, 0.35 * max(6, len(rows))))
    ax.axis("off")
    table = ax.table(cellText=rows, colLabels=["campo", "valor"], cellLoc="center", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.2)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()


def compute_horizon_errors(model, series, dates, start_dates, H_long):
    mae = np.zeros(H_long)
    rmse = np.zeros(H_long)
    bias = np.zeros(H_long)
    counts = np.zeros(H_long)
    for start_idx in start_dates:
        preds = model.predict_multistep(series, start_idx, H_long)
        if len(preds) < H_long:
            continue
        real = series[start_idx + 1 : start_idx + 1 + H_long]
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


def compute_price_errors(model, returns, prices, dates, start_dates, H_long):
    mae = np.zeros(H_long)
    rmse = np.zeros(H_long)
    bias = np.zeros(H_long)
    counts = np.zeros(H_long)
    for start_idx in start_dates:
        preds = model.predict_multistep(returns, start_idx, H_long)
        if len(preds) < H_long:
            continue
        pred_log = np.log(prices[start_idx]) + np.cumsum(preds)
        pred_price = np.exp(pred_log)
        real_price = prices[start_idx + 1 : start_idx + 1 + H_long]
        diff = pred_price - real_price
        mae += np.abs(diff)
        rmse += diff ** 2
        bias += diff
        counts += 1
    counts[counts == 0] = 1
    mae = mae / counts
    rmse = np.sqrt(rmse / counts)
    bias = bias / counts
    return mae, rmse, bias


def compute_baseline_price_errors(prices, start_dates, H_long, ma_window=7):
    mae_p = np.zeros(H_long)
    mae_ma = np.zeros(H_long)
    counts = np.zeros(H_long)
    for start_idx in start_dates:
        if start_idx - ma_window < 0:
            continue
        persist = prices[start_idx]
        ma = float(np.mean(prices[start_idx - ma_window : start_idx]))
        real_price = prices[start_idx + 1 : start_idx + 1 + H_long]
        if len(real_price) < H_long:
            continue
        mae_p += np.abs(persist - real_price)
        mae_ma += np.abs(ma - real_price)
        counts += 1
    counts[counts == 0] = 1
    mae_p = mae_p / counts
    mae_ma = mae_ma / counts
    return mae_p, mae_ma


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


def load_energy_series():
    base_dir = ROOT
    ons_path = base_dir / "data" / "raw" / "ONS" / "ons_carga_diaria" / "ons_carga_diaria_2000_2026.csv"
    if not ons_path.exists():
        return None
    df = pd.read_csv(ons_path, sep=";", engine="python")
    df.columns = [c.strip() for c in df.columns]
    df["din_instante"] = pd.to_datetime(df["din_instante"], errors="coerce")
    df = df.dropna(subset=["din_instante", "val_cargaenergiamwmed", "id_subsistema", "nom_subsistema"])
    df["val_cargaenergiamwmed"] = df["val_cargaenergiamwmed"].astype(float)
    return df


def run_energy(subsystems, train_end, test_year):
    out_base = ROOT / "results" / "_figs" / "energy"
    summary_dir = out_base / "_summary"
    ensure_dir(summary_dir)
    df = load_energy_series()
    if df is None:
        print("Energy data not found.")
        return None

    manifest_path = ROOT / "website" / "assets" / "spa_energy" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    embed_meta = manifest.get("embedding_meta", {})

    name_map = {
        "N": "Norte",
        "NE": "Nordeste",
        "S": "Sul",
        "SECO": "Sudeste/Centro-Oeste",
    }

    summary_rows = []
    for code in subsystems:
        name = name_map.get(code, code)
        df_sub = df[(df["id_subsistema"].str.upper() == code) | (df["nom_subsistema"] == name)]
        if df_sub.empty:
            continue
        daily = df_sub.groupby("din_instante")["val_cargaenergiamwmed"].mean().reset_index()
        daily = daily.sort_values("din_instante")

        dates = pd.to_datetime(daily["din_instante"])
        ensure_sorted_dates(dates)
        dates = dates.to_numpy()
        prices = daily["val_cargaenergiamwmed"].to_numpy()
        log_price = np.log(prices)
        returns = np.diff(log_price)
        dates = dates[1:]
        prices = prices[1:]
        delta = np.diff(prices)
        delta_dates = dates[1:]
        delta_prices = prices[1:]

        train_end_dt = pd.Timestamp(train_end)
        test_start = pd.Timestamp(f"{test_year}-01-01")
        test_end = pd.Timestamp(f"{test_year}-12-31")

        meta_name = name.replace("/", " ")
        tau = embed_meta.get(meta_name, {}).get("daily", {}).get("tau", 2)
        m = embed_meta.get(meta_name, {}).get("daily", {}).get("m", 4)
        k = embed_meta.get(meta_name, {}).get("daily", {}).get("k", 10)

        X, y, idx = embed(returns, tau, m)
        if X is None:
            continue
        train_mask = dates[idx] <= train_end_dt
        test_mask = (dates[idx] >= test_start) & (dates[idx] <= test_end)
        validate_time_split(
            dates,
            dates <= train_end_dt,
            (dates >= test_start) & (dates <= test_end),
            train_end=train_end_dt,
            test_start=test_start,
            test_end=test_end,
        )
        test_start_pos = int(np.where(dates >= test_start)[0].min()) if np.any(dates >= test_start) else None
        if test_start_pos is None:
            continue
        min_valid = test_start_pos + (m - 1) * tau
        test_idx, dropped = safe_test_indices(test_mask.values if hasattr(test_mask, "values") else test_mask, min_valid)
        if train_mask.sum() < k or test_mask.sum() < 10:
            continue

        model = TakensKNN(tau=tau, m=m, k=k)
        train_idx = int(idx[train_mask].max())
        if not model.fit(returns, train_idx=train_idx):
            continue

        out_dir = out_base / safe_name(code)
        ensure_dir(out_dir)

        X_train = X[train_mask]
        if X_train.shape[1] >= 3:
            plot_attractor(
                X_train[:, :3],
                f"{code} | tau={tau}, m={m}, k={k} | n={len(X_train)}",
                out_dir / "attractor_3d.png",
            )

        if len(test_idx) < 5:
            continue
        mid_start = test_idx[len(test_idx) // 2]
        H_short = 5
        H_long = 60
        preds_short = model.predict_multistep(returns, mid_start, H_short)
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

        start_candidates = test_idx[: len(test_idx) - H_long]
        if len(start_candidates) == 0:
            continue
        picks = np.linspace(0, len(start_candidates) - 1, min(50, len(start_candidates))).astype(int)
        start_dates = start_candidates[picks]
        mae_curve, rmse_curve, bias_curve = compute_horizon_errors(model, returns, dates, start_dates, H_long)
        plot_error_curve_with_bias(mae_curve, rmse_curve, bias_curve, out_dir / "error_vs_horizon.png")

        horizon_est = horizon_estimate(mae_curve, returns[dates <= train_end_dt])
        horizon_mae2 = horizon_by_mae_ratio(mae_curve, ratio=2.0)
        summary = {
            "tau": tau,
            "m": m,
            "k": k,
            "MAE_h1": float(mae_curve[0]),
            "MAE_h2": float(mae_curve[1]),
            "MAE_h5": float(mae_curve[4]),
            "MAE_h10": float(mae_curve[9]),
            "MAE_h20": float(mae_curve[19]),
            "MAE_h60": float(mae_curve[59]),
            "RMSE_h1": float(rmse_curve[0]),
            "RMSE_h2": float(rmse_curve[1]),
            "RMSE_h5": float(rmse_curve[4]),
            "RMSE_h10": float(rmse_curve[9]),
            "RMSE_h20": float(rmse_curve[19]),
            "RMSE_h60": float(rmse_curve[59]),
            "bias_h1": float(bias_curve[0]),
            "bias_h2": float(bias_curve[1]),
            "bias_h5": float(bias_curve[4]),
            "bias_h10": float(bias_curve[9]),
            "bias_h20": float(bias_curve[19]),
            "bias_h60": float(bias_curve[59]),
            "horizon_est": int(horizon_est),
            "horizon_mae2": int(horizon_mae2),
            "train_n": int(train_mask.sum()),
            "test_n": int(len(test_idx)),
            "split_hash": split_hash(np.where(dates <= train_end_dt)[0], test_idx),
            "dropped_test_points_due_to_embedding": int(dropped),
        }
        # Variant on delta (difference)
        Xd, yd, idxd = embed(delta, tau, m)
        if Xd is not None:
            train_mask_d = delta_dates[idxd] <= train_end_dt
            test_mask_d = (delta_dates[idxd] >= test_start) & (delta_dates[idxd] <= test_end)
            model_d = TakensKNN(tau=tau, m=m, k=k)
            if train_mask_d.any():
                train_idx_d = int(idxd[train_mask_d].max())
                if model_d.fit(delta, train_idx=train_idx_d) and test_mask_d.sum() > 10:
                    test_start_pos_d = int(np.where(delta_dates >= test_start)[0].min()) if np.any(delta_dates >= test_start) else None
                    if test_start_pos_d is None:
                        continue
                    min_valid_d = test_start_pos_d + (m - 1) * tau
                    test_idx_d, _ = safe_test_indices(
                        (delta_dates >= test_start) & (delta_dates <= test_end),
                        min_valid_d,
                    )
                    if len(test_idx_d) > H_long + 1:
                        start_candidates_d = test_idx_d[: len(test_idx_d) - H_long]
                        picks_d = np.linspace(0, len(start_candidates_d) - 1, min(50, len(start_candidates_d))).astype(int)
                        start_dates_d = start_candidates_d[picks_d]
                        mae_d, rmse_d, bias_d = compute_horizon_errors(model_d, delta, delta_dates, start_dates_d, H_long)
                        summary.update(
                            {
                                "delta_MAE_h1": float(mae_d[0]),
                                "delta_MAE_h5": float(mae_d[4]),
                                "delta_MAE_h20": float(mae_d[19]),
                                "delta_MAE_h60": float(mae_d[59]),
                                "delta_bias_h20": float(bias_d[19]),
                            }
                        )

        plot_summary_table(summary, out_dir / "summary_table.png")

        metrics = {
            "asset": code,
            "tau": tau,
            "m": m,
            "k": k,
            "mae_curve": mae_curve.tolist(),
            "rmse_curve": rmse_curve.tolist(),
            "bias_curve": bias_curve.tolist(),
            "horizon_est": int(horizon_est),
            "horizon_mae2": int(horizon_mae2),
            "train_n": int(train_mask.sum()),
            "test_n": int(len(test_idx)),
            "split_hash": split_hash(np.where(dates <= train_end_dt)[0], test_idx),
            "dropped_test_points_due_to_embedding": int(dropped),
            "train_end": train_end,
            "test_year": test_year,
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
        train_pf = pd.DataFrame()
        if phase_df is not None and not phase_df.empty:
            phase_df.to_csv(out_dir / "phase_features.csv", index=False)

            train_mask_pf = phase_df["date"] <= pd.Timestamp(train_end)
            train_pf = phase_df[train_mask_pf]
            thresholds = {}
            for col in ["raio_rms", "drift_local"]:
                thresholds[col] = float(np.nanpercentile(train_pf[col], 95)) if not train_pf.empty else np.nan

            phase_df["regime_alert"] = (
                (phase_df["raio_rms"] > thresholds["raio_rms"])
                & (phase_df["drift_local"] > thresholds["drift_local"])
            )

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

            plt.figure(figsize=(10, 3))
            plt.plot(phase_df["date"], phase_df["regime_alert"].astype(int), color="#ef4444")
            plt.title("Regime flags (drift_local & raio_rms > limiar)")
            plt.xlabel("Data")
            plt.ylabel("alerta")
            plt.tight_layout()
            plt.savefig(out_dir / "regime_flags.png", dpi=150)
            plt.close()

            alerts_2025 = int(phase_df[phase_df["date"].dt.year == test_year]["regime_alert"].sum())
        else:
            alerts_2025 = 0

        if not train_pf.empty:
            print(
                f"{code} phase features (train percentiles): "
                f"raio_rms p50/p95={np.nanpercentile(train_pf['raio_rms'], 50):.4f}/"
                f"{np.nanpercentile(train_pf['raio_rms'], 95):.4f}, "
                f"drift_local p50/p95={np.nanpercentile(train_pf['drift_local'], 50):.4f}/"
                f"{np.nanpercentile(train_pf['drift_local'], 95):.4f} | "
                f"alerts_{test_year}={alerts_2025}"
            )

        summary_rows.append(
            {
                "asset": code,
                "tau": tau,
                "m": m,
                "k": k,
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
                "delta_MAE1": summary.get("delta_MAE_h1"),
                "delta_MAE5": summary.get("delta_MAE_h5"),
                "delta_MAE20": summary.get("delta_MAE_h20"),
                "delta_MAE60": summary.get("delta_MAE_h60"),
                "delta_bias20": summary.get("delta_bias_h20"),
                "alerts_year": alerts_2025,
                "train_n": summary["train_n"],
                "test_n": summary["test_n"],
            }
        )

        print(
            f"{code}: MAE(h1,h5,h20,h60)=({summary['MAE_h1']:.4f},"
            f"{summary['MAE_h5']:.4f},{summary['MAE_h20']:.4f},{summary['MAE_h60']:.4f}) "
            f"| bias_mean={summary['bias_h20']:.4f} | alerts_{test_year}={alerts_2025} "
            f"| horizon_mae2={summary['horizon_mae2']}"
        )

    summary_df = pd.DataFrame(summary_rows)
    summary_path = summary_dir / "benchmark_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    return summary_path


def run_yfinance(tickers, train_end, test_year):
    out_base = ROOT / "results" / "_figs" / "yfinance"
    summary_dir = out_base / "_summary"
    ensure_dir(summary_dir)

    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "yf_chaos_benchmark.py"),
        "--tickers",
        ",".join(tickers),
        "--train-end",
        train_end,
        "--test-start",
        f"{test_year}-01-01",
        "--test-end",
        f"{test_year}-12-31",
        "--outdir",
        str(out_base),
    ]
    subprocess.run(cmd, check=True)

    summary_path = out_base / "benchmark_summary.csv"
    if summary_path.exists() and summary_path.stat().st_size > 0:
        dest = summary_dir / "benchmark_summary.csv"
        shutil.copy2(summary_path, dest)
        try:
            summary_df = pd.read_csv(summary_path)
        except Exception:
            summary_df = pd.DataFrame()
        for _, row in summary_df.iterrows():
            print(
                f"{row['ticker']}: MAE(h1,h5,h20,h60)=({row['MAE1']:.4f},{row['MAE5']:.4f},"
                f"{row['MAE20']:.4f},{row['MAE60']:.4f}) | bias_mean={row['bias20']:.4f}"
                f" | alerts_2025={int(row.get('alerts_2025', 0))} | horizon_mae2={int(row.get('horizon_mae2', 0))}"
            )
    return summary_path


def main():
    parser = argparse.ArgumentParser(description="Lab runner for energy and yfinance.")
    parser.add_argument("--domain", required=True, choices=["yfinance", "energy"])
    parser.add_argument("--tickers", default="", help="Comma-separated tickers.")
    parser.add_argument("--subsystems", default="", help="Comma-separated subsystems (SECO,S,NE,N).")
    parser.add_argument("--train-end", default="2024-12-31")
    parser.add_argument("--test-year", type=int, default=2025)
    args = parser.parse_args()

    if args.domain == "yfinance":
        tickers = [t.strip() for t in args.tickers.split(",") if t.strip()]
        if not tickers:
            tickers = ["SPY", "BTC-USD", "^VIX"]
        run_yfinance(tickers, args.train_end, args.test_year)
        return

    subsystems = [s.strip().upper() for s in args.subsystems.split(",") if s.strip()]
    if not subsystems:
        subsystems = ["SECO", "S", "NE", "N"]
    run_energy(subsystems, args.train_end, args.test_year)


if __name__ == "__main__":
    main()
