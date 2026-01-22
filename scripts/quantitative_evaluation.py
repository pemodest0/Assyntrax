from __future__ import annotations

import glob
import pandas as pd
from pathlib import Path
import numpy as np

ROOT = Path("results/today_forecast_eval")


def predictability_score(alpha, low=0.6, high=0.85):
    try:
        a = float(alpha)
    except Exception:
        return np.nan
    if not np.isfinite(a):
        return np.nan
    if high <= low:
        return 0.0
    return float(max(0.0, min(1.0, (a - low) / (high - low))))


def load_all_metrics(root: Path):
    rows = []
    for csv in root.glob("*/daily_forecast_metrics.csv"):
        try:
            df = pd.read_csv(csv, parse_dates=["date"], low_memory=False)
        except Exception:
            continue
        if df.empty:
            continue
        df["source_symbol_dir"] = csv.parent.name
        rows.append(df)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def summarize(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for (sym, mode), g in df.groupby(["symbol", "mode"]):
        mae_pct = float(g["error_pct"].abs().mean()) if "error_pct" in g.columns else np.nan
        medae = float(g["error_pct"].abs().median()) if "error_pct" in g.columns else np.nan
        dir_acc = float(g["direction_match"].mean()) if "direction_match" in g.columns else np.nan
        mean_alpha = float(g["alpha"].mean()) if "alpha" in g.columns else np.nan
        mean_entropy = float(g["entropy"].mean()) if "entropy" in g.columns else np.nan
        frac_nan_pred = float(g["price_pred"].isna().mean()) if "price_pred" in g.columns else np.nan
        corr = float(g["dalpha"].corr(g["actual_return"])) if ("dalpha" in g.columns and "actual_return" in g.columns) else np.nan
        phase_counts = g["phase"].value_counts(dropna=False).to_dict() if "phase" in g.columns else {}
        pred_score = np.nanmean([predictability_score(a) for a in g.get("alpha", []).values])
        out.append(
            {
                "symbol": sym,
                "mode": mode,
                "records": int(g.shape[0]),
                "mae_pct": mae_pct,
                "median_ae_pct": medae,
                "direction_acc": dir_acc,
                "mean_alpha": mean_alpha,
                "mean_entropy": mean_entropy,
                "frac_nan_pred": frac_nan_pred,
                "corr_dalpha_return": corr,
                "predictability_score": float(pred_score) if not np.isnan(pred_score) else np.nan,
                "phase_counts": phase_counts,
            }
        )
    return pd.DataFrame(out)


def phase_fractions(df: pd.DataFrame) -> pd.DataFrame:
    records = []
    if "phase" not in df.columns:
        return pd.DataFrame()
    for sym, g in df.groupby("symbol"):
        counts = g["phase"].fillna("indefinido").value_counts()
        total = counts.sum()
        frac = {k: float(v / total) for k, v in counts.items()}
        records.append({"symbol": sym, **frac})
    return pd.DataFrame(records).fillna(0.0)


def top_bottom(df_sum: pd.DataFrame):
    # top by predictability_score
    top = df_sum.sort_values("predictability_score", ascending=False).head(10)
    worst = df_sum.sort_values("mae_pct", ascending=False).head(10)
    return top, worst


def main():
    df = load_all_metrics(ROOT)
    if df.empty:
        print("No metrics files found under", ROOT)
        return
    summary = summarize(df)
    summary.to_csv(ROOT / "quant_eval_summary_by_mode.csv", index=False)
    # aggregate per symbol (average across modes)
    agg = summary.groupby("symbol").agg(
        records=("records", "sum"),
        mae_pct=("mae_pct", "mean"),
        direction_acc=("direction_acc", "mean"),
        mean_alpha=("mean_alpha", "mean"),
        mean_entropy=("mean_entropy", "mean"),
        predictability_score=("predictability_score", "mean"),
    ).reset_index()
    agg.to_csv(ROOT / "quant_eval_summary_by_symbol.csv", index=False)

    top, worst = top_bottom(agg)

    print("Overall summary (by symbol):")
    print(agg.describe(include='all').transpose())
    print("\nTop symbols by predictability score:")
    print(top[["symbol","predictability_score","mae_pct","direction_acc"]].to_string(index=False))
    print("\nWorst symbols by MAE%:")
    print(worst[["symbol","mae_pct","predictability_score","direction_acc"]].to_string(index=False))


if __name__ == "__main__":
    main()
