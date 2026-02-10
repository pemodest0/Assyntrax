#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUTDIR_DEFAULT = ROOT / "results" / "validation" / "hybrid_risk"


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _discover_assets(max_assets: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    finance = sorted((ROOT / "data" / "raw" / "finance" / "yfinance_daily").glob("*.csv"))
    for p in finance:
        out.append(
            {
                "asset_id": p.stem,
                "domain": "finance",
                "path": p,
                "date_col": "date",
                "value_col": "close",
            }
        )

    energy = sorted((ROOT / "data" / "raw" / "ONS" / "ons_carga_diaria").glob("*.csv"))
    for p in energy:
        out.append(
            {
                "asset_id": p.stem,
                "domain": "energy",
                "path": p,
                "date_col": "din_instante",
                "value_col": "val_cargaenergiamwmed",
            }
        )

    realestate = sorted((ROOT / "data" / "realestate" / "normalized").glob("*.csv"))
    for p in realestate:
        out.append(
            {
                "asset_id": f"RE_{p.stem}",
                "domain": "real_estate",
                "path": p,
                "date_col": "date",
                "value_col": "value",
            }
        )
    return out[:max_assets]


def _resolve_col(df: pd.DataFrame, name: str) -> str | None:
    if name in df.columns:
        return name
    low = name.lower()
    for c in df.columns:
        if str(c).lower() == low:
            return str(c)
    return None


def _load_series(path: Path, date_col: str, value_col: str) -> tuple[pd.DataFrame, str]:
    df = pd.read_csv(path)
    if df.shape[1] == 1 and ";" in str(df.columns[0]):
        df = pd.read_csv(path, sep=";")
    dc = _resolve_col(df, date_col)
    vc = _resolve_col(df, value_col)
    if vc is None:
        for cand in ["price", "close", "adj_close", "value", "valor", "log_price", "r"]:
            vc = _resolve_col(df, cand)
            if vc is not None:
                break
    if dc is None:
        for cand in ["date", "data", "datetime", "timestamp", "time", "din_instante"]:
            dc = _resolve_col(df, cand)
            if dc is not None:
                break
    if dc is None or vc is None:
        raise ValueError(f"missing columns in {path.name}: date={date_col} value={value_col}")
    out = pd.DataFrame(
        {
            "date": pd.to_datetime(df[dc], errors="coerce"),
            "value": pd.to_numeric(df[vc], errors="coerce"),
        }
    ).dropna()
    out = out.sort_values("date").drop_duplicates("date")
    return out, str(vc).lower()


def _rolling_acf1(x: pd.Series, window: int) -> pd.Series:
    vals = x.to_numpy(dtype=float)
    out = np.full(vals.shape[0], np.nan, dtype=float)
    for i in range(window, len(vals)):
        w = vals[i - window : i]
        if np.std(w) < 1e-12:
            out[i] = 0.0
        else:
            out[i] = float(pd.Series(w).autocorr(lag=1))
    return pd.Series(out, index=x.index)


def _ewma_sigma(r: pd.Series, lam: float = 0.94) -> pd.Series:
    arr = r.fillna(0.0).to_numpy(dtype=float)
    v = np.zeros_like(arr)
    v[0] = float(np.var(arr[: min(30, len(arr))])) if len(arr) > 0 else 0.0
    for i in range(1, len(arr)):
        v[i] = lam * v[i - 1] + (1.0 - lam) * (arr[i - 1] ** 2)
    return pd.Series(np.sqrt(np.clip(v, 0.0, None)), index=r.index)


def _norm(s: pd.Series) -> pd.Series:
    q05 = s.quantile(0.05)
    q95 = s.quantile(0.95)
    den = float(max(q95 - q05, 1e-9))
    return ((s - q05) / den).clip(0.0, 1.0)


def _status(ews: float, var95: float, ewma_sig: float, q_ews: float, q_var: float, q_sig: float) -> str:
    # Higher EWS and sigma indicate turbulence; lower (more negative) VaR indicates larger potential loss.
    risk_hits = 0
    if ews >= q_ews:
        risk_hits += 1
    if var95 <= q_var:
        risk_hits += 1
    if ewma_sig >= q_sig:
        risk_hits += 1
    if risk_hits >= 2:
        return "watch"
    if risk_hits == 0:
        return "validated"
    return "inconclusive"


def _build_network_layer(finance_panel: pd.DataFrame, outdir: Path) -> dict[str, Any]:
    if finance_panel.empty or finance_panel.shape[1] < 3:
        return {"status": "insufficient_assets"}
    cov = finance_panel.cov().to_numpy(dtype=float)
    vals, vecs = np.linalg.eigh(cov)
    i = int(np.argmax(vals))
    top_eval = float(vals[i])
    v = np.abs(vecs[:, i])
    v = v / (np.sum(v) + 1e-12)
    network = {
        "status": "ok",
        "n_assets": int(finance_panel.shape[1]),
        "largest_eigenvalue": top_eval,
        "eigenvector_centrality_mean": float(np.mean(v)),
        "eigenvector_centrality_std": float(np.std(v)),
    }
    _json_dump(outdir / "network_metrics.json", network)
    return network


def main() -> None:
    parser = argparse.ArgumentParser(description="Hybrid EWS + VaR + EWMA GARCH-like + network risk layer.")
    parser.add_argument("--outdir", type=str, default=str(OUTDIR_DEFAULT))
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-assets", type=int, default=40)
    parser.add_argument("--min-points", type=int, default=300)
    parser.add_argument("--window", type=int, default=60)
    parser.add_argument("--lam", type=float, default=0.94)
    args = parser.parse_args()

    np.random.seed(args.seed)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    finance_ret_panel: dict[str, pd.Series] = {}

    for ds in _discover_assets(args.max_assets):
        aid = ds["asset_id"]
        try:
            df, used_col = _load_series(ds["path"], ds["date_col"], ds["value_col"])
            if df.shape[0] < args.min_points:
                rows.append(
                    {
                        "asset_id": aid,
                        "domain": ds["domain"],
                        "status": "fail",
                        "reason": f"insufficient_points<{args.min_points}",
                    }
                )
                continue
            if used_col == "r":
                ret = df["value"].replace([np.inf, -np.inf], np.nan).dropna()
            else:
                ret = np.log(df["value"]).diff().replace([np.inf, -np.inf], np.nan).dropna()
            if ret.shape[0] < args.window + 10:
                rows.append(
                    {
                        "asset_id": aid,
                        "domain": ds["domain"],
                        "status": "fail",
                        "reason": "insufficient_returns_window",
                    }
                )
                continue

            acf1 = _rolling_acf1(ret, args.window)
            rvar = ret.rolling(args.window, min_periods=args.window).var()
            rskew = ret.rolling(args.window, min_periods=args.window).skew().abs()
            ews_score = (_norm(acf1) + _norm(rvar) + _norm(rskew)) / 3.0

            ewma_sig = _ewma_sigma(ret, lam=args.lam)
            var95_hist = ret.rolling(args.window, min_periods=args.window).quantile(0.05)
            # Parametric normal VaR proxy.
            mu = ret.rolling(args.window, min_periods=args.window).mean()
            var95_norm = mu - 1.645 * ewma_sig

            q_ews = float(ews_score.quantile(0.8))
            q_var = float(var95_hist.quantile(0.2))
            q_sig = float(ewma_sig.quantile(0.8))

            ret_dates = pd.to_datetime(df["date"].reindex(ret.index), errors="coerce")
            latest = pd.DataFrame(
                {
                    "date": ret_dates.to_numpy(),
                    "ret": ret.to_numpy(dtype=float),
                    "ews_score": ews_score.loc[ret.index].to_numpy(dtype=float),
                    "ewma_sigma": ewma_sig.loc[ret.index].to_numpy(dtype=float),
                    "var95_hist": var95_hist.loc[ret.index].to_numpy(dtype=float),
                    "var95_norm": var95_norm.loc[ret.index].to_numpy(dtype=float),
                }
            ).dropna()
            if latest.empty:
                rows.append({"asset_id": aid, "domain": ds["domain"], "status": "fail", "reason": "no_latest_points"})
                continue

            lx = latest.iloc[-1]
            st = _status(
                float(lx["ews_score"]),
                float(lx["var95_hist"]),
                float(lx["ewma_sigma"]),
                q_ews=q_ews,
                q_var=q_var,
                q_sig=q_sig,
            )
            reason = (
                f"ews={lx['ews_score']:.3f} (q80={q_ews:.3f}), "
                f"var95={lx['var95_hist']:.4f} (q20={q_var:.4f}), "
                f"sigma={lx['ewma_sigma']:.4f} (q80={q_sig:.4f})"
            )

            asset_dir = outdir / "assets" / aid
            asset_dir.mkdir(parents=True, exist_ok=True)
            latest.to_csv(asset_dir / "timeseries_layer.csv", index=False)
            _json_dump(
                asset_dir / "summary.json",
                {
                    "status": "ok",
                    "asset_id": aid,
                    "domain": ds["domain"],
                    "source_col": used_col,
                    "n_points": int(df.shape[0]),
                    "window": int(args.window),
                    "lam": float(args.lam),
                    "latest_status": st,
                    "latest_reason": reason,
                    "latest": {
                        "ews_score": float(lx["ews_score"]),
                        "var95_hist": float(lx["var95_hist"]),
                        "var95_norm": float(lx["var95_norm"]),
                        "ewma_sigma": float(lx["ewma_sigma"]),
                    },
                    "thresholds": {"q80_ews": q_ews, "q20_var95_hist": q_var, "q80_sigma": q_sig},
                },
            )

            rows.append(
                {
                    "asset_id": aid,
                    "domain": ds["domain"],
                    "status": "ok",
                    "hybrid_status": st,
                    "reason": reason,
                    "ews_score": float(lx["ews_score"]),
                    "var95_hist": float(lx["var95_hist"]),
                    "var95_norm": float(lx["var95_norm"]),
                    "ewma_sigma": float(lx["ewma_sigma"]),
                    "thr_ews_q80": q_ews,
                    "thr_var95_q20": q_var,
                    "thr_sigma_q80": q_sig,
                }
            )

            if ds["domain"] == "finance":
                aligned = pd.Series(ret.to_numpy(dtype=float), index=ret_dates.to_numpy())
                finance_ret_panel[aid] = aligned
        except Exception as exc:
            rows.append({"asset_id": aid, "domain": ds["domain"], "status": "fail", "reason": str(exc)})

    out_df = pd.DataFrame(rows)
    out_df.to_csv(outdir / "hybrid_status_by_asset.csv", index=False)

    finance_panel = pd.DataFrame(finance_ret_panel).dropna(how="all")
    network = _build_network_layer(finance_panel, outdir)

    ok = out_df[out_df["status"] == "ok"].copy()
    summary = {
        "status": "ok" if not ok.empty else "fail",
        "n_assets_total": int(out_df.shape[0]),
        "n_assets_ok": int(ok.shape[0]),
        "n_assets_fail": int((out_df["status"] == "fail").sum()) if not out_df.empty else 0,
        "hybrid_counts": (
            ok["hybrid_status"].value_counts().to_dict() if "hybrid_status" in ok.columns else {}
        ),
        "network": network,
    }
    _json_dump(outdir / "summary.json", summary)
    print(
        f"[hybrid_risk] status={summary['status']} total={summary['n_assets_total']} "
        f"ok={summary['n_assets_ok']} counts={summary['hybrid_counts']}"
    )


if __name__ == "__main__":
    main()
