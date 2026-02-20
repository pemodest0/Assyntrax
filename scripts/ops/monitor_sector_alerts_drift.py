#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]


def _safe_float(x: object) -> float | None:
    try:
        v = float(x)
    except Exception:
        return None
    return v if math.isfinite(v) else None


def _run_ts(x: str) -> datetime:
    return datetime.fromisoformat(str(x).replace("Z", "+00:00")).astimezone(timezone.utc)


def _load_profile_defaults(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    drift_cfg = payload.get("drift_monitor", {})
    if not isinstance(drift_cfg, dict):
        return {}
    out: dict[str, float] = {}
    for k in ["baseline_days", "min_history_runs", "warn_zscore", "block_zscore"]:
        if k in drift_cfg:
            v = _safe_float(drift_cfg.get(k))
            if v is not None:
                out[k] = float(v)
    return out


def _agg_for_run(conn: sqlite3.Connection, run_id: str) -> dict[str, float]:
    q = """
    SELECT
      COUNT(*) AS sectors_total,
      SUM(CASE WHEN LOWER(COALESCE(alert_level, 'verde'))='vermelho' THEN 1 ELSE 0 END) AS n_red,
      SUM(CASE WHEN LOWER(COALESCE(alert_level, 'verde'))='amarelo' THEN 1 ELSE 0 END) AS n_yellow,
      AVG(sector_score) AS mean_score,
      AVG(share_unstable) AS mean_unstable,
      AVG(share_transition) AS mean_transition,
      AVG(mean_confidence) AS mean_confidence
    FROM sector_snapshots
    WHERE run_id=?
    """
    row = conn.execute(q, (run_id,)).fetchone()
    if row is None:
        return {
            "sectors_total": 0.0,
            "red_ratio": float("nan"),
            "yellow_ratio": float("nan"),
            "mean_score": float("nan"),
            "mean_unstable": float("nan"),
            "mean_transition": float("nan"),
            "mean_confidence": float("nan"),
        }
    total = float(row[0] or 0.0)
    n_red = float(row[1] or 0.0)
    n_yellow = float(row[2] or 0.0)
    red_ratio = (n_red / total) if total > 0 else float("nan")
    yellow_ratio = (n_yellow / total) if total > 0 else float("nan")
    return {
        "sectors_total": total,
        "red_ratio": red_ratio,
        "yellow_ratio": yellow_ratio,
        "mean_score": float(row[3]) if row[3] is not None else float("nan"),
        "mean_unstable": float(row[4]) if row[4] is not None else float("nan"),
        "mean_transition": float(row[5]) if row[5] is not None else float("nan"),
        "mean_confidence": float(row[6]) if row[6] is not None else float("nan"),
    }


def _levels_for_run(conn: sqlite3.Connection, run_id: str) -> dict[str, str]:
    q = "SELECT sector, LOWER(COALESCE(alert_level, 'verde')) FROM sector_snapshots WHERE run_id=?"
    return {str(sec): str(level) for sec, level in conn.execute(q, (run_id,)).fetchall()}


def _zscore(cur: float, arr: np.ndarray) -> float:
    if arr.size == 0 or not np.isfinite(cur):
        return float("nan")
    mu = float(np.nanmean(arr))
    sd = float(np.nanstd(arr))
    if not np.isfinite(mu) or not np.isfinite(sd) or sd <= 1e-12:
        return float("nan")
    return float((cur - mu) / sd)


def _clean(obj: object) -> object:
    if isinstance(obj, dict):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    if isinstance(obj, float):
        if not math.isfinite(obj):
            return None
        return obj
    return obj


def main() -> None:
    defaults = {
        "baseline_days": 30,
        "min_history_runs": 7,
        "warn_zscore": 2.0,
        "block_zscore": 3.0,
    }
    ap = argparse.ArgumentParser(description="Monitor de drift do painel setorial (usa historico em SQLite).")
    ap.add_argument("--db-path", type=str, default="results/event_study_sectors/sector_alerts.db")
    ap.add_argument("--current-run-id", type=str, default="")
    ap.add_argument("--baseline-days", type=int, default=int(defaults["baseline_days"]))
    ap.add_argument("--min-history-runs", type=int, default=int(defaults["min_history_runs"]))
    ap.add_argument("--warn-zscore", type=float, default=float(defaults["warn_zscore"]))
    ap.add_argument("--block-zscore", type=float, default=float(defaults["block_zscore"]))
    ap.add_argument("--profile-file", type=str, default="config/sector_alerts_profile.json")
    ap.add_argument("--ignore-profile", action="store_true")
    ap.add_argument("--out-json", type=str, default="")
    ap.add_argument("--out-root", type=str, default="results/event_study_sectors/drift")
    args = ap.parse_args()

    if (not args.ignore_profile) and str(args.profile_file).strip():
        profile_defaults = _load_profile_defaults(ROOT / str(args.profile_file))
        if profile_defaults:
            if int(args.baseline_days) == int(defaults["baseline_days"]):
                args.baseline_days = int(profile_defaults.get("baseline_days", args.baseline_days))
            if int(args.min_history_runs) == int(defaults["min_history_runs"]):
                args.min_history_runs = int(profile_defaults.get("min_history_runs", args.min_history_runs))
            if float(args.warn_zscore) == float(defaults["warn_zscore"]):
                args.warn_zscore = float(profile_defaults.get("warn_zscore", args.warn_zscore))
            if float(args.block_zscore) == float(defaults["block_zscore"]):
                args.block_zscore = float(profile_defaults.get("block_zscore", args.block_zscore))

    db_path = ROOT / str(args.db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")
    conn = sqlite3.connect(db_path)

    run_rows = conn.execute("SELECT run_id, generated_at_utc FROM runs ORDER BY generated_at_utc").fetchall()
    if not run_rows:
        raise RuntimeError("No runs in DB.")
    run_ts_map = {str(rid): str(ts) for rid, ts in run_rows}
    current_run_id = str(args.current_run_id).strip() or str(run_rows[-1][0])
    if current_run_id not in run_ts_map:
        raise RuntimeError(f"Run not found in DB: {current_run_id}")

    now_ts = _run_ts(run_ts_map[current_run_id])
    start_ts = now_ts - timedelta(days=int(max(1, args.baseline_days)))
    baseline_run_ids = [
        str(rid)
        for rid, ts_raw in run_rows
        if (str(rid) != current_run_id) and (_run_ts(str(ts_raw)) >= start_ts) and (_run_ts(str(ts_raw)) < now_ts)
    ]

    metric_keys = [
        "red_ratio",
        "yellow_ratio",
        "mean_score",
        "mean_unstable",
        "mean_transition",
        "mean_confidence",
    ]
    current_metrics = _agg_for_run(conn, current_run_id)
    baseline_metrics: dict[str, list[float]] = {k: [] for k in metric_keys}
    for rid in baseline_run_ids:
        m = _agg_for_run(conn, rid)
        for k in metric_keys:
            v = float(m.get(k, float("nan")))
            if np.isfinite(v):
                baseline_metrics[k].append(v)

    baseline_summary: dict[str, dict[str, float]] = {}
    z_scores: dict[str, float] = {}
    for k in metric_keys:
        arr = np.array(baseline_metrics.get(k, []), dtype=float)
        baseline_summary[k] = {
            "mean": float(np.nanmean(arr)) if arr.size else float("nan"),
            "std": float(np.nanstd(arr)) if arr.size else float("nan"),
            "n": float(arr.size),
        }
        z_scores[k] = _zscore(float(current_metrics.get(k, float("nan"))), arr)

    previous_run_id = str(run_rows[-2][0]) if len(run_rows) >= 2 and str(run_rows[-1][0]) == current_run_id else ""
    changed_ratio = float("nan")
    if previous_run_id:
        cur_levels = _levels_for_run(conn, current_run_id)
        prev_levels = _levels_for_run(conn, previous_run_id)
        sectors = sorted(set(cur_levels) | set(prev_levels))
        if sectors:
            changed = sum(1 for sec in sectors if cur_levels.get(sec, "verde") != prev_levels.get(sec, "verde"))
            changed_ratio = float(changed / len(sectors))
    conn.close()

    z_abs = [abs(v) for v in z_scores.values() if np.isfinite(v)]
    drift_score = float(max(z_abs)) if z_abs else float("nan")
    drift_level = "ok"
    reasons: list[str] = []
    if len(baseline_run_ids) < int(args.min_history_runs):
        drift_level = "unknown"
        reasons.append("historico insuficiente para drift confiavel")
    else:
        if np.isfinite(drift_score) and drift_score >= float(args.block_zscore):
            drift_level = "block"
        elif np.isfinite(drift_score) and drift_score >= float(args.warn_zscore):
            drift_level = "watch"
        for k in metric_keys:
            z = z_scores.get(k, float("nan"))
            if np.isfinite(z) and abs(z) >= float(args.warn_zscore):
                reasons.append(f"{k} fora da faixa historica (z={z:.2f})")
        if np.isfinite(changed_ratio) and changed_ratio >= 0.35:
            reasons.append(f"muita troca de nivel entre runs ({changed_ratio:.1%})")

    payload = {
        "status": "ok",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "current_run_id": current_run_id,
        "current_generated_at_utc": run_ts_map[current_run_id],
        "previous_run_id": previous_run_id or None,
        "config": {
            "baseline_days": int(args.baseline_days),
            "min_history_runs": int(args.min_history_runs),
            "warn_zscore": float(args.warn_zscore),
            "block_zscore": float(args.block_zscore),
        },
        "baseline_window": {
            "start_utc": start_ts.isoformat(),
            "end_utc": now_ts.isoformat(),
            "n_runs": int(len(baseline_run_ids)),
            "run_ids": baseline_run_ids,
        },
        "current_metrics": current_metrics,
        "baseline_metrics": baseline_summary,
        "z_scores": z_scores,
        "changed_ratio_vs_prev_run": changed_ratio,
        "drift_score": drift_score,
        "drift_level": drift_level,
        "reasons": reasons,
    }
    clean_payload = _clean(payload)

    out_root = ROOT / str(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)
    out_json = Path(str(args.out_json)).expanduser() if str(args.out_json).strip() else (out_root / f"drift_{current_run_id}.json")
    if not out_json.is_absolute():
        out_json = ROOT / str(out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(clean_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (out_root / "latest_drift.json").write_text(json.dumps(clean_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "current_run_id": current_run_id,
                "drift_level": clean_payload.get("drift_level"),
                "drift_score": clean_payload.get("drift_score"),
                "out_json": str(out_json),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
