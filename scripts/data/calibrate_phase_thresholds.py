from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import json

ROOT = Path("results/today_forecast_eval")
OUT = ROOT / "calibration"
OUT.mkdir(parents=True, exist_ok=True)


def load_metrics():
    dfs = []
    for p in ROOT.glob("*/daily_forecast_metrics.csv"):
        try:
            df = pd.read_csv(p, parse_dates=["date"] , low_memory=False)
        except Exception:
            continue
        if df.empty:
            continue
        df["symbol_dir"] = p.parent.name
        dfs.append(df)
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)


def evaluate_thresholds(df, p_lows=(0.1,0.25,0.35,0.5), p_highs=(0.5,0.65,0.8,0.95)):
    results = {}
    for sym, g in df.groupby("symbol"):
        alphas = g["alpha"].dropna().values
        if alphas.size < 20:
            continue
        best = None
        stats = []
        for pl in p_lows:
            low = np.quantile(alphas, pl)
            for ph in p_highs:
                if ph <= pl:
                    continue
                high = np.quantile(alphas, ph)
                # classify
                coh = g[g["alpha"] >= high]
                dif = g[g["alpha"] <= low]
                if coh.empty:
                    continue
                mae_coh = float(coh["error_pct"].abs().mean()) if "error_pct" in coh.columns else np.nan
                dir_coh = float(coh["direction_match"].mean()) if "direction_match" in coh.columns else np.nan
                mae_dif = float(dif["error_pct"].abs().mean()) if not dif.empty and "error_pct" in dif.columns else np.nan
                dir_dif = float(dif["direction_match"].mean()) if not dif.empty and "direction_match" in dif.columns else np.nan
                stats.append({"pl":pl,"ph":ph,"low":float(low),"high":float(high),"mae_coh":mae_coh,"dir_coh":dir_coh,"mae_dif":mae_dif,"dir_dif":dir_dif,"n_coh":int(coh.shape[0]),"n_dif":int(dif.shape[0])})
                # choose best by dir_coh then mae_coh
                if best is None or (dir_coh > best["dir_coh"] if not np.isnan(dir_coh) else False):
                    best = stats[-1]
        results[sym] = {"best":best, "all":stats}
    return results


def save_results(results: dict):
    (OUT / "calibration_results.json").write_text(json.dumps(results, default=lambda x: None, indent=2))


def plot_summary(results):
    rows = []
    for sym, v in results.items():
        b = v.get("best")
        if not b:
            continue
        rows.append({"symbol":sym, "dir_coh":b["dir_coh"], "mae_coh":b["mae_coh"], "n_coh":b["n_coh"], "low":b["low"], "high":b["high"]})
    df = pd.DataFrame(rows).sort_values("dir_coh", ascending=False)
    if df.empty:
        return
    plt.figure(figsize=(10,6))
    plt.scatter(df["mae_coh"], df["dir_coh"], s=df["n_coh"].clip(10,100), alpha=0.8)
    for i,r in df.iterrows():
        plt.text(r["mae_coh"], r["dir_coh"], r["symbol"], fontsize=8)
    plt.xlabel('MAE% (coherent windows)')
    plt.ylabel('Direction accuracy (coherent windows)')
    plt.title('Calibration: coherent-window performance per symbol')
    plt.grid(True)
    plt.savefig(OUT / "coherent_perf_scatter.png", dpi=200)
    plt.close()


def generate_diagnostic_plots(df, results):
    # per-symbol scatter alpha vs abs(error)
    for sym, g in df.groupby("symbol"):
        if sym not in results or not results[sym].get("best"):
            continue
        best = results[sym]["best"]
        low = best["low"]
        high = best["high"]
        plt.figure(figsize=(8,4))
        plt.scatter(g["alpha"], g["error_pct"].abs(), s=6, alpha=0.6)
        plt.axvline(low, color='red', linestyle='--', label=f'low={low:.3g}')
        plt.axvline(high, color='green', linestyle='--', label=f'high={high:.3g}')
        plt.yscale('log')
        plt.xlabel('alpha')
        plt.ylabel('|error_pct|')
        plt.title(f'{sym} alpha vs abs(error)')
        plt.legend()
        plt.grid(True, which='both', ls=':', alpha=0.5)
        plt.tight_layout()
        plt.savefig(OUT / f'{sym}_alpha_error.png', dpi=200)
        plt.close()


def main():
    df = load_metrics()
    if df.empty:
        print('No metrics found')
        return
    results = evaluate_thresholds(df)
    save_results(results)
    plot_summary(results)
    generate_diagnostic_plots(df, results)
    print('Calibration finished; outputs in', OUT)


if __name__ == '__main__':
    main()
