#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.temporal.temporal_engine import TemporalConfig, YearResult, build_temporal_report, compare_models
from engine.validation_gate import evaluate_gate, load_gate_config

OUTDIR_DEFAULT = ROOT / "results" / "validated" / "latest"


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        rows.append(json.loads(s))
    return rows


def _find_api_records_path() -> Path:
    candidates = [
        ROOT / "results" / "latest" / "api_records.jsonl",
        ROOT / "results" / "latest_graph" / "api_records.jsonl",
        ROOT / "website-ui" / "public" / "data" / "latest" / "api_records.jsonl",
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError("api_records.jsonl not found in results/latest, results/latest_graph or website-ui/public/data/latest")


def _load_group_map() -> dict[str, str]:
    p = ROOT / "data" / "asset_groups.csv"
    if not p.exists():
        return {}
    try:
        df = pd.read_csv(p)
    except Exception:
        return {}
    cols = {c.lower(): c for c in df.columns}
    a_col = cols.get("asset") or cols.get("ticker") or cols.get("symbol")
    g_col = cols.get("group") or cols.get("sector") or cols.get("category")
    if not a_col or not g_col:
        return {}
    out: dict[str, str] = {}
    for _, r in df.iterrows():
        out[str(r[a_col])] = str(r[g_col])
    return out


def _load_quality_fallback() -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    cands = [
        ROOT / "results" / "validation" / "universe_mini_full" / "master_summary.csv",
        ROOT / "results" / "validation" / "universe_mini" / "master_summary.csv",
    ]
    for p in cands:
        if not p.exists():
            continue
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        if "asset_id" not in df.columns:
            continue
        for _, r in df.iterrows():
            asset = str(r.get("asset_id", ""))
            if not asset:
                continue
            out[asset] = {
                "quality": float(r.get("mean_quality")) if pd.notna(r.get("mean_quality")) else None,
                "confidence": float(r.get("mean_confidence")) if pd.notna(r.get("mean_confidence")) else None,
            }
    return out


def _normalize_regime(rec: dict[str, Any]) -> str:
    lbl = str(rec.get("regime_label") or "").upper().strip()
    if lbl in {"STABLE", "TRANSITION", "UNSTABLE"}:
        return lbl
    warnings = [str(w).upper() for w in (rec.get("warnings") or [])]
    tr = rec.get("transition_rate")
    try:
        trv = float(tr)
    except Exception:
        trv = None
    if "REGIME_INSTAVEL" in warnings:
        return "UNSTABLE"
    if trv is not None and trv > 0.40:
        return "TRANSITION"
    return "STABLE"


def _load_universe_fallback_records() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    cands = [
        ROOT / "results" / "validation" / "universe_mini_full",
        ROOT / "results" / "validation" / "universe_mini",
    ]
    for root in cands:
        master = root / "master_summary.csv"
        if not master.exists():
            continue
        try:
            mdf = pd.read_csv(master)
        except Exception:
            continue
        for _, r in mdf.iterrows():
            if str(r.get("status", "")).lower() != "ok":
                continue
            asset = str(r.get("asset_id", "")).strip()
            if not asset:
                continue
            asset_dir = root / asset
            regimes = asset_dir / "regimes.csv"
            if not regimes.exists():
                continue
            try:
                rdf = pd.read_csv(regimes)
            except Exception:
                continue
            if rdf.empty:
                continue
            last = rdf.iloc[-1]
            dt = str(last.get("date", ""))[:10] or "1970-01-01"
            try:
                conf = float(last.get("confidence", np.nan))
            except Exception:
                conf = np.nan
            quality = r.get("mean_quality")
            try:
                quality = float(quality)
            except Exception:
                quality = np.nan
            tf = str(r.get("timeframe", "daily"))
            out.append(
                {
                    "timestamp": dt,
                    "asset": asset,
                    "timeframe": tf,
                    "regime_label": str(last.get("regime_label", "")),
                    "regime_confidence": conf,
                    "quality": quality,
                    "transition_rate": r.get("pct_transition"),
                    "novelty_score": None,
                    "warnings": [],
                }
            )
        if out:
            return out
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build validated artifacts for API/dashboard consumption.")
    parser.add_argument("--outdir", type=str, default=str(OUTDIR_DEFAULT))
    parser.add_argument("--gate-config", type=str, default=str(ROOT / "config" / "validation_gates.json"))
    parser.add_argument("--include-universe-fallback", action="store_true", help="Augmenta com ativos de universe_mini(_full).")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    gate_cfg = load_gate_config(args.gate_config)
    records_path = _find_api_records_path()
    records = _load_jsonl(records_path)
    # Augment with broader validated universe results when available.
    if args.include_universe_fallback:
        extra = _load_universe_fallback_records()
        if extra:
            seen = {(str(x.get("asset")), str(x.get("timeframe"))) for x in records}
            for r in extra:
                k = (str(r.get("asset")), str(r.get("timeframe")))
                if k not in seen:
                    records.append(r)
                    seen.add(k)
    if not records:
        (outdir / "summary.json").write_text(
            json.dumps({"status": "fail", "reason": "empty_api_records", "source": str(records_path)}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print("[fail] empty api_records")
        return

    df = pd.DataFrame(records)
    if "timestamp" not in df.columns or "asset" not in df.columns:
        (outdir / "summary.json").write_text(
            json.dumps({"status": "fail", "reason": "invalid_api_records_schema", "source": str(records_path)}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print("[fail] invalid api_records schema")
        return

    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df[df["timestamp"].notna()].copy()
    if "timeframe" not in df.columns:
        df["timeframe"] = "daily"

    group_map = _load_group_map()
    fallback = _load_quality_fallback()

    latest_rows = []
    universe_by_tf: dict[str, list[dict[str, Any]]] = {"daily": [], "weekly": []}

    for (asset, timeframe), g in df.groupby(["asset", "timeframe"]):
        g = g.sort_values("timestamp")
        rec = g.iloc[-1].to_dict()
        group = group_map.get(str(asset), "unknown")
        fb = fallback.get(str(asset), {})
        quality_raw = rec.get("quality")
        confidence_raw = rec.get("regime_confidence")
        if confidence_raw is None:
            confidence_raw = rec.get("forecast_confidence")
        if quality_raw is None:
            quality_raw = fb.get("quality")
        if confidence_raw is None:
            confidence_raw = fb.get("confidence")

        quality = pd.to_numeric(pd.Series([quality_raw]), errors="coerce").iloc[0]
        confidence = pd.to_numeric(pd.Series([confidence_raw]), errors="coerce").iloc[0]

        # Conservative fallback: when quality is missing, mirror confidence.
        if pd.isna(quality) and not pd.isna(confidence):
            quality = confidence
        if pd.isna(confidence) and not pd.isna(quality):
            confidence = quality
        if pd.isna(quality) and pd.isna(confidence):
            quality = 0.0
            confidence = 0.0

        gate = evaluate_gate(
            asset=str(asset),
            group=group,
            quality=quality,
            confidence=confidence,
            transition_rate=rec.get("transition_rate"),
            novelty=rec.get("novelty_score"),
            config=gate_cfg,
        )
        regime = _normalize_regime(rec)
        if gate.status != "validated":
            regime = "INCONCLUSIVE"

        item = {
            "asset": str(asset),
            "group": group,
            "timeframe": str(timeframe),
            "state": {"label": regime},
            "metrics": {
                "confidence": gate.confidence,
                "quality": gate.quality,
                "transition_rate": gate.transition_rate,
                "novelty": gate.novelty,
            },
            "validation": gate.to_dict(),
            "timestamp": pd.to_datetime(rec["timestamp"]).strftime("%Y-%m-%d"),
        }
        latest_rows.append(item)
        if str(timeframe) in universe_by_tf:
            universe_by_tf[str(timeframe)].append(item)

    for tf, items in universe_by_tf.items():
        (outdir / f"universe_{tf}.json").write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

    status_df = pd.DataFrame(
        [
            {
                "asset": r["asset"],
                "group": r["group"],
                "timeframe": r["timeframe"],
                "timestamp": r["timestamp"],
                "regime": r["state"]["label"],
                "status": r["validation"]["status"],
                "reason": ";".join(r["validation"]["reasons"]),
                "confidence": r["metrics"]["confidence"],
                "quality": r["metrics"]["quality"],
                "transition_rate": r["metrics"]["transition_rate"],
                "novelty": r["metrics"]["novelty"],
            }
            for r in latest_rows
        ]
    )
    status_df.to_csv(outdir / "asset_status.csv", index=False)

    # Temporal summary using yearly aggregation from api records.
    yearly = df.copy()
    yearly["year"] = yearly["timestamp"].dt.year
    horizon_col = "horizon" if "horizon" in yearly.columns else None
    models: dict[str, dict[str, list[YearResult]]] = {"gated_forecast": {}}
    if horizon_col is not None and "mase_6m" in yearly.columns:
        for h, gh in yearly.groupby(horizon_col):
            rows = []
            for year, gy in gh.groupby("year"):
                vals = pd.to_numeric(gy["mase_6m"], errors="coerce").dropna()
                if vals.empty:
                    continue
                rows.append(YearResult(year=int(year), model_error=float(vals.mean()), baseline_error=1.0))
            if rows:
                models["gated_forecast"][f"h{int(h)}"] = rows
    temporal = build_temporal_report(compare_models(models, TemporalConfig()), TemporalConfig())
    (outdir / "temporal_summary.json").write_text(json.dumps(temporal, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = {
        "status": "ok",
        "source_api_records": str(records_path),
        "n_assets": int(status_df["asset"].nunique()),
        "n_asset_timeframes": int(status_df.shape[0]),
        "validated_count": int((status_df["status"] == "validated").sum()),
        "inconclusive_count": int((status_df["status"] != "validated").sum()),
        "validated_ratio": float((status_df["status"] == "validated").mean()) if not status_df.empty else 0.0,
        "outputs": {
            "universe_daily": str(outdir / "universe_daily.json"),
            "universe_weekly": str(outdir / "universe_weekly.json"),
            "asset_status": str(outdir / "asset_status.csv"),
            "temporal_summary": str(outdir / "temporal_summary.json"),
        },
    }
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"[validated_artifacts] assets={summary['n_assets']} "
        f"validated={summary['validated_count']} inconclusive={summary['inconclusive_count']}"
    )


if __name__ == "__main__":
    main()
