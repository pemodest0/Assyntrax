#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTDIR_DEFAULT = ROOT / "results" / "validation" / "asset_regime_truth_report"


@dataclass
class RunRef:
    run_id: str
    summary: dict[str, Any]
    snapshot_path: Path
    summary_path: Path


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        fixed = line.replace("NaN", "null").replace("Infinity", "null").replace("-null", "null")
        try:
            out.append(json.loads(fixed))
        except Exception:
            continue
    return out


def _find_latest_valid_run(results_root: Path) -> RunRef:
    snapshots_root = results_root / "ops" / "snapshots"
    if not snapshots_root.exists():
        raise FileNotFoundError(f"Snapshots root not found: {snapshots_root}")

    run_dirs = sorted([p for p in snapshots_root.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True)
    for run_dir in run_dirs:
        summary_path = run_dir / "summary.json"
        snapshot_path = run_dir / "api_snapshot.jsonl"
        if not summary_path.exists() or not snapshot_path.exists():
            continue
        try:
            summary = _read_json(summary_path)
        except Exception:
            continue
        status = str(summary.get("status", "")).lower()
        blocked = bool(((summary.get("deployment_gate") or {}).get("blocked", False)))
        if status == "ok" and not blocked and snapshot_path.stat().st_size > 0:
            return RunRef(run_id=run_dir.name, summary=summary, snapshot_path=snapshot_path, summary_path=summary_path)
    raise RuntimeError("No valid run found (status=ok and deployment_gate.blocked=false)")


def _pick_price_column(df: pd.DataFrame) -> str:
    cols = {str(c).lower(): str(c) for c in df.columns}
    for cand in ["close", "price", "adj_close", "value"]:
        if cand in cols:
            return cols[cand]
    raise ValueError("No price-like column found in raw series")


def _run_lengths(labels: np.ndarray, dates: pd.Series) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if labels.size == 0:
        return out
    start = 0
    n = labels.size
    for i in range(1, n + 1):
        if i == n or labels[i] != labels[start]:
            d0 = pd.Timestamp(dates.iloc[start])
            d1 = pd.Timestamp(dates.iloc[i - 1])
            out.append(
                {
                    "label": str(labels[start]),
                    "start_idx": int(start),
                    "end_idx": int(i - 1),
                    "start_date": d0.strftime("%Y-%m-%d"),
                    "end_date": d1.strftime("%Y-%m-%d"),
                    "duration_days": int((d1 - d0).days) + 1,
                }
            )
            start = i
    return out


def _entry_count(labels: np.ndarray, target: str) -> int:
    if labels.size == 0:
        return 0
    arr = labels.astype(str)
    entries = int(arr[0] == target)
    for i in range(1, arr.size):
        if arr[i] == target and arr[i - 1] != target:
            entries += 1
    return entries


def _apply_hysteresis(labels: np.ndarray, min_run: int = 5) -> np.ndarray:
    if labels.size == 0:
        return labels
    out = labels.astype(str).copy()
    changed = True
    while changed:
        changed = False
        i = 0
        n = out.size
        while i < n:
            j = i + 1
            while j < n and out[j] == out[i]:
                j += 1
            run_len = j - i
            if run_len < min_run:
                left = out[i - 1] if i > 0 else None
                right = out[j] if j < n else None
                repl = left if left is not None else right
                if repl is not None and repl != out[i]:
                    out[i:j] = repl
                    changed = True
            i = j
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Asset-by-asset regime truth report (top N assets)")
    parser.add_argument("--outdir", type=str, default=str(OUTDIR_DEFAULT))
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--domain", type=str, default="finance")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--timeframe", type=str, default="daily")
    parser.add_argument("--min-run", type=int, default=5, help="Regime persistence (hysteresis) for counting switches")
    parser.add_argument("--assets", type=str, default="", help="Comma-separated explicit assets list (optional)")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    results_root = ROOT / "results"

    from engine.graph.core import run_graph_engine
    from engine.graph.embedding import estimate_embedding_params

    run = _find_latest_valid_run(results_root)
    snapshot_rows = _read_jsonl(run.snapshot_path)
    if not snapshot_rows:
        raise RuntimeError(f"Empty snapshot in run {run.run_id}")

    snap_df = pd.DataFrame(snapshot_rows)
    if "asset" not in snap_df.columns:
        raise RuntimeError("Snapshot missing 'asset' column")

    snap_df["asset"] = snap_df["asset"].astype(str)
    snap_df["domain"] = snap_df.get("domain", "").astype(str)
    snap_df["timestamp"] = snap_df.get("timestamp", "").astype(str)

    if args.assets.strip():
        assets = [a.strip() for a in args.assets.split(",") if a.strip()]
    else:
        sub = snap_df[snap_df["domain"].str.lower() == args.domain.lower()].copy()
        if sub.empty:
            sub = snap_df.copy()
        assets = sorted(sub["asset"].dropna().astype(str).unique().tolist())[: max(1, args.top)]

    asset_status_path = results_root / "validated" / "latest" / "asset_status.csv"
    status_map: dict[str, dict[str, str]] = {}
    if asset_status_path.exists():
        as_df = pd.read_csv(asset_status_path)
        for _, r in as_df.iterrows():
            key = f"{str(r.get('asset', ''))}__{str(r.get('timeframe', ''))}"
            status_map[key] = {
                "status": str(r.get("status", "")),
                "reason": str(r.get("reason", "")),
            }

    risk_truth_path = results_root / "validation" / "risk_truth_panel.json"
    risk_map: dict[str, str] = {}
    if risk_truth_path.exists():
        panel = _read_json(risk_truth_path)
        for e in panel.get("entries", []) or []:
            risk_map[str(e.get("asset_id", ""))] = str(e.get("risk_truth_status", "unknown")).lower()

    rows: list[dict[str, Any]] = []
    runlens_all: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for asset in assets:
        try:
            raw_path = ROOT / "data" / "raw" / "finance" / "yfinance_daily" / f"{asset}.csv"
            if not raw_path.exists():
                raise FileNotFoundError(f"raw series missing: {raw_path}")

            raw_df = pd.read_csv(raw_path)
            if "date" not in {str(c).lower() for c in raw_df.columns}:
                raise ValueError("raw series missing date column")
            date_col = [c for c in raw_df.columns if str(c).lower() == "date"][0]
            value_col = _pick_price_column(raw_df)
            series_df = pd.DataFrame(
                {
                    "date": pd.to_datetime(raw_df[date_col], errors="coerce"),
                    "value": pd.to_numeric(raw_df[value_col], errors="coerce"),
                }
            ).dropna()
            series_df = series_df.sort_values("date").drop_duplicates(subset=["date"], keep="last")
            if series_df.shape[0] < 300:
                raise ValueError(f"series too short: {series_df.shape[0]}")

            values = series_df["value"].to_numpy(dtype=float)
            m, tau = estimate_embedding_params(values, max_tau=20, max_m=6, tau_method="ami", m_method="cao")
            res = run_graph_engine(
                values,
                m=int(m),
                tau=int(tau),
                n_micro=80,
                n_regimes=4,
                k_nn=5,
                theiler=10,
                alpha=2.0,
                seed=int(args.seed),
                timeframe=args.timeframe,
                use_multilayer=True,
            )

            labels_raw = np.asarray(res.state_labels).astype(str)
            labels = _apply_hysteresis(labels_raw, min_run=max(1, int(args.min_run)))
            conf = np.asarray(res.confidence, dtype=float)
            offset = series_df.shape[0] - labels.shape[0]
            if offset < 0:
                offset = 0
            aligned_dates = series_df["date"].reset_index(drop=True).iloc[offset : offset + labels.shape[0]].reset_index(drop=True)

            runs = _run_lengths(labels, aligned_dates)
            for item in runs:
                item["asset"] = asset
            runlens_all.extend(runs)

            durations = np.array([int(r["duration_days"]) for r in runs], dtype=float) if runs else np.array([], dtype=float)
            counts_by_label: dict[str, int] = {}
            pct_by_label: dict[str, float] = {}
            for lb in ["STABLE", "TRANSITION", "UNSTABLE", "NOISY"]:
                c = int(np.sum(labels == lb))
                counts_by_label[lb] = c
                pct_by_label[lb] = float(c / max(1, labels.size))

            snap_asset = snap_df[snap_df["asset"] == asset].sort_values("timestamp").tail(1)
            snap_regime = str(snap_asset["regime"].iloc[0]) if not snap_asset.empty and "regime" in snap_asset.columns else ""
            snap_status = str(snap_asset["status"].iloc[0]) if not snap_asset.empty and "status" in snap_asset.columns else ""
            snap_conf = float(snap_asset["confidence"].iloc[0]) if not snap_asset.empty and "confidence" in snap_asset.columns else np.nan
            snap_ts = str(snap_asset["timestamp"].iloc[0]) if not snap_asset.empty and "timestamp" in snap_asset.columns else ""

            gate = status_map.get(f"{asset}__{args.timeframe}", {})
            risk_status = risk_map.get(asset, "unknown")

            current_label = str(labels[-1]) if labels.size else "INCONCLUSIVE"
            current_conf = float(conf[-1]) if conf.size else float("nan")
            ml = (res.multilayer or {}).get("decision", {}) if isinstance(res.multilayer, dict) else {}

            rows.append(
                {
                    "asset": asset,
                    "run_id": run.run_id,
                    "m": int(m),
                    "tau": int(tau),
                    "n_points_raw": int(series_df.shape[0]),
                    "n_points_embedded": int(labels.size),
                    "n_switches_raw": int(np.sum(labels_raw[1:] != labels_raw[:-1])) if labels_raw.size > 1 else 0,
                    "n_switches": int(np.sum(labels[1:] != labels[:-1])) if labels.size > 1 else 0,
                    "n_entries_unstable": _entry_count(labels, "UNSTABLE"),
                    "n_entries_transition": _entry_count(labels, "TRANSITION"),
                    "current_regime_engine": current_label,
                    "current_conf_engine": current_conf,
                    "current_regime_multilayer": str(ml.get("label", "")),
                    "current_conf_multilayer": float(ml.get("confidence", np.nan))
                    if ml.get("confidence", None) is not None
                    else np.nan,
                    "snapshot_regime": snap_regime,
                    "snapshot_status": snap_status,
                    "snapshot_confidence": snap_conf,
                    "snapshot_timestamp": snap_ts,
                    "risk_truth_status": risk_status,
                    "validated_status": gate.get("status", ""),
                    "validated_reason": gate.get("reason", ""),
                    "regime_match_engine_vs_snapshot": bool(current_label == str(snap_regime).upper()) if snap_regime else False,
                    "pct_stable": pct_by_label["STABLE"],
                    "pct_transition": pct_by_label["TRANSITION"],
                    "pct_unstable": pct_by_label["UNSTABLE"],
                    "pct_noisy": pct_by_label["NOISY"],
                    "mean_run_days": float(np.mean(durations)) if durations.size else np.nan,
                    "median_run_days": float(np.median(durations)) if durations.size else np.nan,
                    "max_run_days": float(np.max(durations)) if durations.size else np.nan,
                    "count_stable": counts_by_label["STABLE"],
                    "count_transition": counts_by_label["TRANSITION"],
                    "count_unstable": counts_by_label["UNSTABLE"],
                    "count_noisy": counts_by_label["NOISY"],
                }
            )
        except Exception as exc:
            failures.append({"asset": asset, "reason": str(exc)})

    report_df = pd.DataFrame(rows).sort_values("asset")
    runs_df = pd.DataFrame(runlens_all)
    report_df.to_csv(outdir / "asset_regime_report.csv", index=False)
    if not runs_df.empty:
        runs_df.to_csv(outdir / "asset_regime_runs.csv", index=False)

    summary = {
        "status": "ok" if not report_df.empty else "fail",
        "run_id": run.run_id,
        "top_requested": int(args.top),
        "assets_selected": assets,
        "assets_ok": int(report_df.shape[0]),
        "assets_fail": int(len(failures)),
        "mean_switches": float(report_df["n_switches"].mean()) if not report_df.empty else None,
        "mean_pct_unstable": float(report_df["pct_unstable"].mean()) if not report_df.empty else None,
        "regime_match_rate_engine_vs_snapshot": float(report_df["regime_match_engine_vs_snapshot"].mean())
        if not report_df.empty
        else None,
        "mean_current_conf_engine": float(report_df["current_conf_engine"].mean()) if not report_df.empty else None,
        "mean_current_conf_multilayer": float(report_df["current_conf_multilayer"].mean()) if not report_df.empty else None,
        "failures": failures,
        "files": {
            "asset_report_csv": str(outdir / "asset_regime_report.csv"),
            "run_lengths_csv": str(outdir / "asset_regime_runs.csv"),
        },
    }
    _json_dump(outdir / "summary.json", summary)
    print(
        f"[asset_truth] run={run.run_id} assets_ok={summary['assets_ok']} assets_fail={summary['assets_fail']} "
        f"match_rate={summary['regime_match_rate_engine_vs_snapshot']}"
    )


if __name__ == "__main__":
    main()
