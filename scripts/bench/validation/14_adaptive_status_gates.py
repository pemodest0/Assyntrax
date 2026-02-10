#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUTDIR_DEFAULT = ROOT / "results" / "validation" / "adaptive_gates"


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _infer_domain(asset: str) -> str:
    a = asset.upper()
    if a.startswith("RE_"):
        return "realestate"
    if "ONS_" in a:
        return "energy"
    return "finance"


def _iter_snapshots() -> list[tuple[str, Path]]:
    root = ROOT / "results" / "ops" / "snapshots"
    if not root.exists():
        return []
    runs = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        snap = d / "api_snapshot.jsonl"
        if snap.exists():
            runs.append((d.name, snap))
    return runs


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        out.append(json.loads(s))
    return out


def _compute_transition(r: dict[str, Any]) -> float:
    t = r.get("transition_rate")
    try:
        return float(t)
    except Exception:
        pass
    regime = str(r.get("regime_label") or r.get("regime") or "").lower()
    if "unstable" in regime:
        return 0.80
    if "transition" in regime:
        return 0.45
    if "stable" in regime:
        return 0.20
    return 0.50


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _compute_entropy_norm(vals: pd.Series) -> pd.Series:
    if vals.empty:
        return vals
    lo = float(vals.min())
    hi = float(vals.max())
    if hi - lo < 1e-12:
        return pd.Series(np.zeros(len(vals)), index=vals.index)
    return ((vals - lo) / (hi - lo)).clip(0, 1)


def _status(conf: float, quality: float, transition: float, instability: float, thr: dict[str, float], cp_flag: bool) -> str:
    if (
        conf >= thr["conf_eff_q"]
        and quality >= thr["qual_q"]
        and transition <= thr["trans_q"]
        and instability <= thr["instab_q"]
        and not cp_flag
    ):
        return "validated"
    if (
        conf >= max(0.0, thr["conf_eff_q"] * 0.92)
        and quality >= max(0.0, thr["qual_q"] * 0.92)
        and instability <= max(0.0, thr["instab_q"] * 1.10)
    ):
        return "watch"
    return "inconclusive"


def _hysteresis(seq: list[str], min_persist: int) -> list[str]:
    if len(seq) < 2:
        return seq
    out = seq[:]
    for i in range(1, len(out)):
        if out[i] == out[i - 1]:
            continue
        end = min(len(out), i + min_persist)
        if end - i < min_persist:
            out[i] = out[i - 1]
            continue
        if all(out[j] == out[i] for j in range(i, end)):
            continue
        out[i] = out[i - 1]
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Adaptive per-domain gates with expanding quantiles + hysteresis.")
    parser.add_argument("--outdir", type=str, default=str(OUTDIR_DEFAULT))
    parser.add_argument("--q-conf", type=float, default=0.35)
    parser.add_argument("--q-quality", type=float, default=0.35)
    parser.add_argument("--q-transition", type=float, default=0.65)
    parser.add_argument("--q-instability", type=float, default=0.70)
    parser.add_argument("--q-changepoint", type=float, default=0.90)
    parser.add_argument("--min-history", type=int, default=6)
    parser.add_argument("--hysteresis-persist", type=int, default=2)
    parser.add_argument("--hazard-half-life-days", type=int, default=45)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    runs = _iter_snapshots()
    if not runs:
        _json_dump(outdir / "summary.json", {"status": "fail", "reason": "no_snapshots_found"})
        print("[adaptive_gates] fail no snapshots")
        return

    rows: list[dict[str, Any]] = []
    for run_id, path in runs:
        try:
            recs = _read_jsonl(path)
        except Exception:
            continue
        for r in recs:
            asset = str(r.get("asset", "")).strip()
            if not asset:
                continue
            conf = float(r.get("regime_confidence", r.get("forecast_confidence", 0.0)) or 0.0)
            quality = float(r.get("quality", 0.0) or 0.0)
            entropy = _safe_float(r.get("entropy", (r.get("metrics") or {}).get("entropy", 0.0)), 0.0)
            transition = _compute_transition(r)
            conf_eff = conf if conf > 0 else max(0.0, min(1.0, max(0.0, quality) * (1.0 - 0.5 * transition)))
            rows.append(
                {
                    "run_id": run_id,
                    "asset": asset,
                    "domain": _infer_domain(asset),
                    "confidence": conf,
                    "confidence_eff": conf_eff,
                    "quality": quality,
                    "transition": transition,
                    "entropy": entropy,
                }
            )

    hist = pd.DataFrame(rows).sort_values(["asset", "run_id"])
    if hist.empty:
        _json_dump(outdir / "summary.json", {"status": "fail", "reason": "empty_history"})
        print("[adaptive_gates] fail empty history")
        return

    status_rows: list[dict[str, Any]] = []
    threshold_rows: list[dict[str, Any]] = []

    for (domain, asset), g in hist.groupby(["domain", "asset"], sort=True):
        g = g.sort_values("run_id").reset_index(drop=True)
        entropy_norm = _compute_entropy_norm(g["entropy"].astype(float))
        g["instability"] = (((1.0 - g["confidence_eff"].astype(float)) + (1.0 - g["quality"].astype(float)) + entropy_norm) / 3.0).clip(0, 1)
        g["delta_instability"] = (g["instability"] - g["instability"].expanding(min_periods=1).median()).abs()
        raw_status: list[str] = []
        changepoint_flags: list[bool] = []
        for i in range(len(g)):
            past = g.iloc[: i + 1]
            if len(past) < args.min_history:
                thr = {"conf_q": 0.55, "conf_eff_q": 0.50, "qual_q": 0.75, "trans_q": 0.80, "instab_q": 0.85, "cp_q": 0.35}
            else:
                thr = {
                    "conf_q": float(past["confidence"].quantile(args.q_conf)),
                    "conf_eff_q": float(past["confidence_eff"].quantile(args.q_conf)),
                    "qual_q": float(past["quality"].quantile(args.q_quality)),
                    "trans_q": float(past["transition"].quantile(args.q_transition)),
                    "instab_q": float(past["instability"].quantile(args.q_instability)),
                    "cp_q": float(past["delta_instability"].quantile(args.q_changepoint)),
                }
            cp_flag = bool(float(g.loc[i, "delta_instability"]) >= thr["cp_q"])
            s = _status(
                float(g.loc[i, "confidence_eff"]),
                float(g.loc[i, "quality"]),
                float(g.loc[i, "transition"]),
                float(g.loc[i, "instability"]),
                thr,
                cp_flag,
            )
            raw_status.append(s)
            changepoint_flags.append(cp_flag)
            threshold_rows.append(
                {
                    "run_id": g.loc[i, "run_id"],
                    "asset": asset,
                    "domain": domain,
                    "thr_conf": thr["conf_q"],
                    "thr_conf_eff": thr.get("conf_eff_q", thr["conf_q"]),
                    "thr_quality": thr["qual_q"],
                    "thr_transition": thr["trans_q"],
                    "thr_instability": thr["instab_q"],
                    "thr_changepoint_delta": thr["cp_q"],
                    "history_points": int(i + 1),
                }
            )

        smooth = _hysteresis(raw_status, min_persist=args.hysteresis_persist)
        regime_age = []
        age = 0
        for i, st in enumerate(smooth):
            if i == 0 or st != smooth[i - 1]:
                age = 1
            else:
                age += 1
            regime_age.append(age)
        for i in range(len(g)):
            age_days = int(regime_age[i])
            # Hazard decreases with age; short-lived regime is less trustworthy.
            hazard = float(np.exp(-age_days / max(1, args.hazard_half_life_days)))
            reason = "validated_gate_ok"
            if smooth[i] == "watch":
                reason = "watch_transition_or_instability"
            if smooth[i] == "inconclusive":
                reason = "inconclusive_low_quality_or_breaking_regime"
            status_rows.append(
                {
                    "run_id": g.loc[i, "run_id"],
                    "asset": asset,
                    "domain": domain,
                    "confidence": float(g.loc[i, "confidence"]),
                    "confidence_eff": float(g.loc[i, "confidence_eff"]),
                    "quality": float(g.loc[i, "quality"]),
                    "transition": float(g.loc[i, "transition"]),
                    "entropy": float(g.loc[i, "entropy"]),
                    "instability_score": float(g.loc[i, "instability"]),
                    "delta_instability": float(g.loc[i, "delta_instability"]),
                    "changepoint_flag": bool(changepoint_flags[i]),
                    "regime_age_days": age_days,
                    "hazard_score": hazard,
                    "status_raw": raw_status[i],
                    "status_hysteresis": smooth[i],
                    "status_reason": reason,
                }
            )

    status_df = pd.DataFrame(status_rows)
    thr_df = pd.DataFrame(threshold_rows)
    status_df.to_csv(outdir / "status_history.csv", index=False)
    thr_df.to_csv(outdir / "adaptive_thresholds.csv", index=False)

    latest_run = status_df["run_id"].max()
    latest = status_df[status_df["run_id"] == latest_run].copy()
    latest = latest.sort_values(["domain", "asset"])
    latest.to_csv(outdir / "latest_status.csv", index=False)

    counts = latest["status_hysteresis"].value_counts().to_dict()
    summary = {
        "status": "ok",
        "latest_run_id": str(latest_run),
        "n_assets": int(latest["asset"].nunique()),
        "counts": {
            "validated": int(counts.get("validated", 0)),
            "watch": int(counts.get("watch", 0)),
            "inconclusive": int(counts.get("inconclusive", 0)),
        },
        "params": {
            "q_conf": args.q_conf,
            "q_quality": args.q_quality,
            "q_transition": args.q_transition,
            "q_instability": args.q_instability,
            "q_changepoint": args.q_changepoint,
            "min_history": args.min_history,
            "hysteresis_persist": args.hysteresis_persist,
            "hazard_half_life_days": args.hazard_half_life_days,
        },
    }
    _json_dump(outdir / "summary.json", summary)
    print(
        f"[adaptive_gates] run={latest_run} assets={summary['n_assets']} "
        f"validated={summary['counts']['validated']} watch={summary['counts']['watch']} "
        f"inconclusive={summary['counts']['inconclusive']}"
    )


if __name__ == "__main__":
    main()
