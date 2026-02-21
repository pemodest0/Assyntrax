#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(v: Any) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    if x != x:
        return None
    return x


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    arr = sorted(values)
    if len(arr) == 1:
        return arr[0]
    pos = (len(arr) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(arr) - 1)
    frac = pos - lo
    return arr[lo] * (1 - frac) + arr[hi] * frac


def _sanitize_json_line(line: str) -> str:
    return (
        line.replace("\u0000", "")
        .replace("NaN", "null")
        .replace("Infinity", "null")
        .replace("-null", "null")
    )


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            try:
                rows.append(json.loads(_sanitize_json_line(line)))
            except json.JSONDecodeError:
                continue
    return rows


@dataclass
class PriceSeries:
    dates: list[str]
    returns: list[float]
    idx_by_date: dict[str, int]


def _load_price_series(path: Path) -> PriceSeries:
    dates: list[str] = []
    returns: list[float] = []
    idx_by_date: dict[str, int] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            d = str(row.get("date", "")).strip()
            r = _safe_float(row.get("r"))
            if not d or r is None:
                continue
            dates.append(d)
            returns.append(r)
            idx_by_date[d] = len(dates) - 1
    return PriceSeries(dates=dates, returns=returns, idx_by_date=idx_by_date)


def _resolve_snapshot_path(run_id: str | None, snapshot: str | None) -> Path:
    if snapshot:
        p = (ROOT / snapshot).resolve() if not Path(snapshot).is_absolute() else Path(snapshot)
        if p.exists():
            return p
        raise FileNotFoundError(f"snapshot_not_found: {p}")

    if run_id:
        candidate = ROOT / "results" / "ops" / "snapshots" / run_id / "api_snapshot.jsonl"
        if candidate.exists():
            return candidate

    fallback = ROOT / "website-ui" / "public" / "data" / "latest" / "api_records.jsonl"
    if fallback.exists():
        return fallback
    raise FileNotFoundError("snapshot_not_found: passe --snapshot ou --run-id válido")


def _prediction_is_risk(status: str, regime: str) -> bool:
    s = status.lower().strip()
    r = regime.upper().strip()
    if s == "watch":
        return True
    return r in {"UNSTABLE", "TRANSITION"}


def main() -> None:
    ap = argparse.ArgumentParser(description="Atualiza histórico diário de acerto/erro das previsões de risco.")
    ap.add_argument("--run-id", type=str, default="")
    ap.add_argument("--snapshot", type=str, default="")
    ap.add_argument("--price-root", type=str, default="data/raw/finance/yfinance_daily")
    ap.add_argument("--lookback", type=int, default=252)
    ap.add_argument("--quantile", type=float, default=0.80)
    ap.add_argument("--min-history", type=int, default=60)
    ap.add_argument("--horizon-bars", type=int, default=1)
    ap.add_argument("--out-root", type=str, default="results/ops/prediction_truth")
    args = ap.parse_args()

    run_id = str(args.run_id).strip() or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_path = _resolve_snapshot_path(run_id if args.run_id else None, args.snapshot or None)
    price_root = ROOT / args.price_root
    out_root = ROOT / args.out_root
    out_root.mkdir(parents=True, exist_ok=True)
    details_dir = out_root / "details"
    details_dir.mkdir(parents=True, exist_ok=True)

    rows = _load_jsonl(snapshot_path)
    # Keep one record per asset/timeframe/timestamp (last one wins).
    dedup: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        asset = str(row.get("asset", "")).strip()
        tf = str(row.get("timeframe", "")).strip().lower()
        ts = str(row.get("timestamp", "")).strip()[:10]
        if not asset or not ts:
            continue
        dedup[(asset, tf, ts)] = row

    candidates = [
        r
        for (_, _, _), r in dedup.items()
        if str(r.get("domain", "")).strip().lower() == "finance"
        and str(r.get("timeframe", "")).strip().lower() == "daily"
    ]

    price_cache: dict[str, PriceSeries] = {}
    detail_rows: list[dict[str, Any]] = []

    tp = tn = fp = fn = 0
    skipped_inconclusive = 0
    skipped_no_price = 0
    skipped_no_next = 0
    skipped_short_history = 0

    for row in candidates:
        asset = str(row.get("asset", "")).strip()
        pred_date = str(row.get("timestamp", "")).strip()[:10]
        status = str(row.get("signal_status", row.get("status", ""))).strip().lower()
        regime = str(row.get("regime", "")).strip().upper()
        confidence = _safe_float(row.get("confidence"))

        if status == "inconclusive" or regime == "INCONCLUSIVE":
            skipped_inconclusive += 1
            continue

        if asset not in price_cache:
            p = price_root / f"{asset}.csv"
            if not p.exists():
                skipped_no_price += 1
                continue
            try:
                price_cache[asset] = _load_price_series(p)
            except OSError:
                skipped_no_price += 1
                continue

        series = price_cache[asset]
        idx = series.idx_by_date.get(pred_date)
        if idx is None:
            # Fallback to nearest previous available date.
            prev_dates = [d for d in series.dates if d <= pred_date]
            if not prev_dates:
                skipped_no_next += 1
                continue
            idx = series.idx_by_date.get(prev_dates[-1])
            if idx is None:
                skipped_no_next += 1
                continue

        next_idx = idx + max(1, int(args.horizon_bars))
        if next_idx >= len(series.returns):
            skipped_no_next += 1
            continue

        hist_start = max(0, idx - int(args.lookback) + 1)
        hist_abs = [abs(v) for v in series.returns[hist_start : idx + 1] if _safe_float(v) is not None]
        if len(hist_abs) < int(args.min_history):
            skipped_short_history += 1
            continue

        threshold = _quantile(hist_abs, float(args.quantile))
        realized_return = float(series.returns[next_idx])
        realized_event = abs(realized_return) >= threshold
        predicted_risk = _prediction_is_risk(status, regime)
        hit = predicted_risk == realized_event

        if predicted_risk and realized_event:
            tp += 1
        elif predicted_risk and (not realized_event):
            fp += 1
        elif (not predicted_risk) and realized_event:
            fn += 1
        else:
            tn += 1

        detail_rows.append(
            {
                "run_id": run_id,
                "asset": asset,
                "prediction_date": pred_date,
                "evaluation_date": series.dates[next_idx],
                "status": status,
                "regime": regime,
                "confidence": confidence,
                "predicted_risk": int(predicted_risk),
                "realized_risk_event": int(realized_event),
                "hit": int(hit),
                "realized_return": realized_return,
                "abs_threshold": threshold,
            }
        )

    scored = tp + tn + fp + fn
    accuracy = (tp + tn) / scored if scored else None
    precision_risk = tp / (tp + fp) if (tp + fp) else None
    recall_risk = tp / (tp + fn) if (tp + fn) else None
    false_alarm_rate = fp / (tp + fp) if (tp + fp) else None
    event_rate = (tp + fn) / scored if scored else None

    summary: dict[str, Any] = {
        "status": "ok",
        "run_id": run_id,
        "generated_at_utc": _now_iso(),
        "snapshot_path": str(snapshot_path),
        "config": {
            "lookback": int(args.lookback),
            "quantile": float(args.quantile),
            "min_history": int(args.min_history),
            "horizon_bars": int(args.horizon_bars),
        },
        "counts": {
            "records_total": len(rows),
            "finance_daily_records": len(candidates),
            "predictions_scored": scored,
            "hits": (tp + tn),
            "misses": (fp + fn),
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "skipped_inconclusive": skipped_inconclusive,
            "skipped_no_price": skipped_no_price,
            "skipped_no_next_return": skipped_no_next,
            "skipped_short_history": skipped_short_history,
        },
        "metrics": {
            "accuracy": accuracy,
            "precision_risk": precision_risk,
            "recall_risk": recall_risk,
            "false_alarm_rate": false_alarm_rate,
            "event_rate": event_rate,
        },
        "top_misses": sorted(detail_rows, key=lambda x: abs(float(x.get("realized_return", 0.0))), reverse=True)[:10],
    }

    details_csv = details_dir / f"{run_id}.csv"
    if detail_rows:
        with details_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(detail_rows[0].keys()))
            writer.writeheader()
            writer.writerows(detail_rows)
    else:
        details_csv.write_text("run_id,asset,prediction_date,evaluation_date,status,regime,confidence,predicted_risk,realized_risk_event,hit,realized_return,abs_threshold\n", encoding="utf-8")

    summary["details_csv"] = str(details_csv)

    latest_json = out_root / "latest.json"
    latest_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    history_csv = out_root / "history.csv"
    history_row = {
        "run_id": run_id,
        "generated_at_utc": summary["generated_at_utc"],
        "predictions_scored": scored,
        "accuracy": accuracy,
        "precision_risk": precision_risk,
        "recall_risk": recall_risk,
        "false_alarm_rate": false_alarm_rate,
        "event_rate": event_rate,
        "hits": (tp + tn),
        "misses": (fp + fn),
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }
    history_rows: list[dict[str, Any]] = []
    if history_csv.exists():
        with history_csv.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            history_rows = [dict(r) for r in reader if str(r.get("run_id", "")).strip()]
    # Replace same run_id if rerun.
    history_rows = [r for r in history_rows if str(r.get("run_id")) != run_id]
    history_rows.append(history_row)
    history_rows.sort(key=lambda r: str(r.get("generated_at_utc", "")))

    with history_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(history_row.keys()))
        writer.writeheader()
        writer.writerows(history_rows)

    # Save for site (public folder tracked by Vercel deploy from this repo).
    public_latest_dir = ROOT / "website-ui" / "public" / "data" / "latest"
    public_latest_dir.mkdir(parents=True, exist_ok=True)
    public_json = public_latest_dir / "prediction_truth_daily.json"
    public_csv = public_latest_dir / "prediction_truth_history.csv"
    public_json.write_text(
        json.dumps(
            {
                **summary,
                "history_tail": history_rows[-60:],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    with public_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(history_row.keys()))
        writer.writeheader()
        writer.writerows(history_rows)

    # Per-run summary for /api/ops/latest.
    run_summary = ROOT / "results" / "ops" / "runs" / run_id / "prediction_truth_summary.json"
    run_summary.parent.mkdir(parents=True, exist_ok=True)
    run_summary.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "run_id": run_id,
                "predictions_scored": scored,
                "accuracy": accuracy,
                "latest_json": str(latest_json),
                "public_json": str(public_json),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
