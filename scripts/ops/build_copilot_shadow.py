#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.diagnostics.auto_regime_model import FEATURE_NAMES

MODEL_C_FEATURE_NAMES = (
    "mean_confidence",
    "mean_quality",
    "pct_transition",
    "hazard_score",
    "hybrid_ews_score",
    "hybrid_var95_hist",
    "hybrid_ewma_sigma",
    "regime_age_days",
    "changepoint_flag",
    "pseudo_bifurcation_flag",
)


def _read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        try:
            rows.append(json.loads(raw))
        except Exception:
            continue
    return rows


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        n = float(value)
        if math.isfinite(n):
            return n
    except Exception:
        pass
    return float(default)


def _to_str(value: Any, default: str = "") -> str:
    return value if isinstance(value, str) else default


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return float(numerator / denominator)


def _acf(values: np.ndarray, lag: int) -> float:
    if values.size <= lag or lag <= 0:
        return 0.0
    v = values.astype(float)
    m = float(np.nanmean(v))
    v = v - m
    den = float(np.dot(v, v))
    if den <= 0:
        return 0.0
    num = float(np.dot(v[:-lag], v[lag:]))
    return num / den


def _entropy_norm(counts: np.ndarray) -> float:
    total = float(np.sum(counts))
    if total <= 0:
        return 0.0
    probs = counts / total
    e = float(-np.sum(probs * np.log2(probs + 1e-12)))
    max_e = math.log2(max(2, counts.size))
    return float(e / max_e) if max_e > 0 else 0.0


def _kurtosis(values: np.ndarray) -> float:
    if values.size < 4:
        return 0.0
    x = values.astype(float)
    m = float(np.mean(x))
    s = float(np.std(x))
    if s <= 1e-12:
        return 0.0
    z = (x - m) / s
    return float(np.mean(z**4) - 3.0)


def _skew(values: np.ndarray) -> float:
    if values.size < 3:
        return 0.0
    x = values.astype(float)
    m = float(np.mean(x))
    s = float(np.std(x))
    if s <= 1e-12:
        return 0.0
    z = (x - m) / s
    return float(np.mean(z**3))


def _regime_to_risk(regime: str, fallback: float) -> float:
    r = regime.lower()
    if "stable" in r or "validated" in r:
        return 0.2
    if "transition" in r or "watch" in r:
        return 0.55
    if "stress" in r or "unstable" in r or "crisis" in r:
        return 0.85
    if "dispersion" in r or "inconclusive" in r:
        return 0.7
    return fallback


@dataclass
class RunContext:
    run_id: str
    summary_path: Path
    snapshot_path: Path
    summary: dict[str, Any]
    rows: list[dict[str, Any]]


def _find_run(run_id: str | None) -> RunContext:
    snapshots_root = ROOT / "results" / "ops" / "snapshots"
    if run_id:
        summary_path = snapshots_root / run_id / "summary.json"
        snapshot_path = snapshots_root / run_id / "api_snapshot.jsonl"
        summary = _read_json(summary_path, {})
        rows = _read_jsonl(snapshot_path)
        if not summary or not rows:
            raise RuntimeError(f"run_id {run_id} sem summary/snapshot valido.")
        return RunContext(run_id=run_id, summary_path=summary_path, snapshot_path=snapshot_path, summary=summary, rows=rows)

    candidates = sorted([p for p in snapshots_root.iterdir() if p.is_dir()], reverse=True)
    for run_dir in candidates:
        summary_path = run_dir / "summary.json"
        snapshot_path = run_dir / "api_snapshot.jsonl"
        summary = _read_json(summary_path, {})
        rows = _read_jsonl(snapshot_path)
        if not summary or not rows:
            continue
        status = _to_str(summary.get("status"), "").lower()
        blocked = bool((_read_json(summary_path, {}).get("deployment_gate") or {}).get("blocked", False))
        if status == "ok" and not blocked:
            return RunContext(
                run_id=run_dir.name,
                summary_path=summary_path,
                snapshot_path=snapshot_path,
                summary=summary,
                rows=rows,
            )
    raise RuntimeError("nenhum run valido encontrado em results/ops/snapshots.")


def _load_lab_context() -> dict[str, Any]:
    lab_root = ROOT / "results" / "lab_corr_macro"
    latest_release = _read_json(lab_root / "latest_release.json", {})
    run_id = _to_str(latest_release.get("run_id"), "")
    if not run_id:
        return {"run_id": "missing", "summary": {}, "timeseries": [], "playbook_latest": {}}

    run_dir = lab_root / run_id
    summary = _read_json(run_dir / "summary.json", {})
    playbook_latest: dict[str, Any] = {}
    playbook_path = run_dir / "action_playbook_T120.json"
    playbook_rows = _read_json(playbook_path, [])
    if isinstance(playbook_rows, list) and playbook_rows:
        last = playbook_rows[-1]
        if isinstance(last, dict):
            playbook_latest = last

    ts_rows: list[dict[str, Any]] = []
    ts_path = run_dir / "macro_timeseries_T120.csv"
    if ts_path.exists():
        try:
            with ts_path.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                ts_rows = [dict(row) for row in reader]
        except Exception:
            ts_rows = []

    return {"run_id": run_id, "summary": summary, "timeseries": ts_rows, "playbook_latest": playbook_latest}


def _extract_arrays(rows: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    conf = np.array([_to_float(r.get("confidence"), np.nan) for r in rows], dtype=float)
    qual = np.array([_to_float(r.get("quality"), np.nan) for r in rows], dtype=float)
    status = np.array([_to_str(r.get("signal_status") or r.get("status"), "inconclusive").lower() for r in rows], dtype=object)
    inst = np.array(
        [
            _to_float(
                r.get("instability_score"),
                1.0 - (0.5 * _to_float(r.get("confidence"), 0.5) + 0.5 * _to_float(r.get("quality"), 0.5)),
            )
            for r in rows
        ],
        dtype=float,
    )
    conf = np.nan_to_num(conf, nan=0.5, posinf=0.5, neginf=0.5)
    qual = np.nan_to_num(qual, nan=0.5, posinf=0.5, neginf=0.5)
    inst = np.nan_to_num(inst, nan=0.5, posinf=0.5, neginf=0.5)
    return {"conf": conf, "qual": qual, "status": status, "inst": inst}


def _count_segments(labels: np.ndarray) -> int:
    if labels.size == 0:
        return 0
    segments = 1
    current = labels[0]
    for value in labels[1:]:
        if value != current:
            segments += 1
            current = value
    return segments


def _build_model_b(
    *,
    rows: list[dict[str, Any]],
    lab_context: dict[str, Any],
) -> dict[str, Any]:
    arrays = _extract_arrays(rows)
    conf = arrays["conf"]
    qual = arrays["qual"]
    inst = arrays["inst"]
    status = arrays["status"]
    total = max(1, status.size)

    validated = int(np.sum(status == "validated"))
    watch = int(np.sum(status == "watch"))
    inconclusive = int(np.sum(status == "inconclusive"))
    watch_ratio = _safe_pct(watch, total)
    inconclusive_ratio = _safe_pct(inconclusive, total)
    validated_ratio = _safe_pct(validated, total)
    fallback_risk = float(np.clip(0.25 + 0.5 * watch_ratio + 0.75 * inconclusive_ratio, 0.0, 1.0))

    status_counts = np.array([validated, watch, inconclusive], dtype=float)
    entropy = _entropy_norm(status_counts)

    conf_diff = np.diff(conf) if conf.size > 1 else np.array([0.0], dtype=float)
    ts_rows = lab_context.get("timeseries") if isinstance(lab_context, dict) else []
    structure_series = []
    if isinstance(ts_rows, list):
        for row in ts_rows[-200:]:
            if isinstance(row, dict):
                structure_series.append(_to_float(row.get("structure_score"), 0.0))
    structure = np.array(structure_series if structure_series else [0.0], dtype=float)

    feature_row: dict[str, float] = {
        "mean_x": float(np.mean(conf)),
        "std_x": float(np.std(conf)),
        "abs_mean_x": float(abs(np.mean(conf))),
        "mean_v": float(np.mean(conf_diff)),
        "std_v": float(np.std(conf_diff)),
        "abs_mean_v": float(abs(np.mean(conf_diff))),
        "mean_energy": float(np.mean(inst)),
        "std_energy": float(np.std(inst)),
        "energy_p10": float(np.percentile(inst, 10)),
        "energy_p90": float(np.percentile(inst, 90)),
        "percent": float(100.0 * watch_ratio),
        "transitions_out": float(inconclusive),
        "segments": float(_count_segments(status)),
        "mean_local_entropy": float(entropy),
        "mean_local_rr": float(validated_ratio),
        "mean_local_skew": float(_skew(conf)),
        "mean_local_kurtosis": float(_kurtosis(conf)),
        "mean_acf1": float(_acf(structure, 1)),
        "mean_acf2": float(_acf(structure, 2)),
        "mean_acf3": float(_acf(structure, 3)),
        "mean_acf4": float(_acf(structure, 4)),
        "mean_acf5": float(_acf(structure, 5)),
        "kinetic_mean": float(np.mean(np.abs(conf_diff))),
        "potential_mean": float(np.mean(qual)),
    }

    model_path = ROOT / "models" / "auto_regime_model.joblib"
    predicted_regime = "transition"
    probability = None
    risk_score = fallback_risk
    mode = "fallback_heuristic"
    error_msg = ""

    if model_path.exists():
        try:
            import joblib

            model = joblib.load(model_path)
            vector = np.array([feature_row.get(name, 0.0) for name in FEATURE_NAMES], dtype=float).reshape(1, -1)
            pred = model.predict(vector)[0]
            predicted_regime = str(pred)
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba(vector)
                if probs is not None and probs.size:
                    probability = float(np.max(probs))
            if probability is None:
                probability = float(np.clip(1.0 - abs(risk_score - 0.5), 0.1, 0.9))
            risk_score = _regime_to_risk(predicted_regime, fallback=fallback_risk)
            mode = "model_file"
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"

    return {
        "mode": mode,
        "model_path": str(model_path),
        "predicted_regime": predicted_regime,
        "probability": probability,
        "risk_score": float(np.clip(risk_score, 0.0, 1.0)),
        "feature_names": list(FEATURE_NAMES),
        "feature_row": feature_row,
        "fallback_risk": fallback_risk,
        "error": error_msg,
    }


def _relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(x, 0.0)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    x_clip = np.clip(x, -20.0, 20.0)
    return 1.0 / (1.0 + np.exp(-x_clip))


def _extract_model_c_inputs(panel: dict[str, Any]) -> tuple[np.ndarray, dict[str, float]]:
    entries = panel.get("entries")
    if not isinstance(entries, list):
        entries = []

    rows: list[list[float]] = []
    qualities: list[float] = []
    pseudo_flags = 0

    for row in entries:
        if not isinstance(row, dict):
            continue
        micro = row.get("micro")
        gates = row.get("gates")
        macro = row.get("macro")
        mean_conf = _to_float(micro.get("mean_confidence"), 0.5) if isinstance(micro, dict) else 0.5
        mean_quality = _to_float(micro.get("mean_quality"), 0.5) if isinstance(micro, dict) else 0.5
        pct_transition = _to_float(micro.get("pct_transition"), 0.5) if isinstance(micro, dict) else 0.5
        hazard = _to_float(gates.get("hazard_score"), 0.5) if isinstance(gates, dict) else 0.5
        ews = _to_float(gates.get("hybrid_ews_score"), 0.5) if isinstance(gates, dict) else 0.5
        var95 = _to_float(gates.get("hybrid_var95_hist"), 0.0) if isinstance(gates, dict) else 0.0
        ewma_sigma = _to_float(gates.get("hybrid_ewma_sigma"), 0.0) if isinstance(gates, dict) else 0.0
        regime_age = _to_float(gates.get("regime_age_days"), 0.0) if isinstance(gates, dict) else 0.0
        changepoint = 1.0 if (isinstance(gates, dict) and bool(gates.get("changepoint_flag", False))) else 0.0
        pseudo_flag = 1.0 if (isinstance(macro, dict) and bool(macro.get("pseudo_bifurcation_flag", False))) else 0.0

        rows.append(
            [
                mean_conf,
                mean_quality,
                pct_transition,
                hazard,
                ews,
                var95,
                ewma_sigma,
                regime_age,
                changepoint,
                pseudo_flag,
            ]
        )
        qualities.append(mean_quality)
        if pseudo_flag > 0:
            pseudo_flags += 1

    X = np.array(rows, dtype=float) if rows else np.zeros((0, len(MODEL_C_FEATURE_NAMES)), dtype=float)
    n = int(X.shape[0])
    summary = {
        "assets_considered": n,
        "mean_quality": float(np.mean(qualities)) if qualities else 0.0,
        "pseudo_bifurcation_rate": _safe_pct(float(pseudo_flags), float(n)) if n > 0 else 1.0,
        "confidence_dispersion": float(np.std(X[:, 0])) if n > 0 else 1.0,
    }
    return X, summary


def _build_knn_graph(Xz: np.ndarray, k_neighbors: int) -> np.ndarray:
    n = Xz.shape[0]
    if n == 0:
        return np.zeros((0, 0), dtype=float)
    if n == 1:
        return np.eye(1, dtype=float)
    k_eff = max(1, min(k_neighbors, n - 1))
    sim = Xz @ Xz.T
    np.fill_diagonal(sim, -1e9)
    A = np.zeros((n, n), dtype=float)
    for i in range(n):
        idx = np.argpartition(sim[i], -k_eff)[-k_eff:]
        A[i, idx] = 1.0
    A = np.maximum(A, A.T)
    np.fill_diagonal(A, 1.0)
    deg = np.sum(A, axis=1)
    inv_sqrt = np.diag(1.0 / np.sqrt(np.maximum(deg, 1e-8)))
    return inv_sqrt @ A @ inv_sqrt


def _infer_model_c_checkpoint(checkpoint_payload: dict[str, Any], X: np.ndarray) -> dict[str, Any]:
    ckpt = checkpoint_payload.get("checkpoint")
    if not isinstance(ckpt, dict):
        raise RuntimeError("checkpoint_model_c_invalido")

    feat = ckpt.get("feature_names")
    if not isinstance(feat, list) or list(feat) != list(MODEL_C_FEATURE_NAMES):
        raise RuntimeError("feature_names_model_c_incompativeis")
    if X.shape[1] != len(feat):
        raise RuntimeError("dimensao_input_model_c_invalida")

    norm = ckpt.get("normalization")
    graph = ckpt.get("graph")
    weights = ckpt.get("weights")
    if not isinstance(norm, dict) or not isinstance(graph, dict) or not isinstance(weights, dict):
        raise RuntimeError("checkpoint_model_c_incompleto")

    mean = np.array(norm.get("mean", []), dtype=float)
    std = np.array(norm.get("std", []), dtype=float)
    if mean.shape[0] != X.shape[1] or std.shape[0] != X.shape[1]:
        raise RuntimeError("normalizacao_model_c_invalida")
    Xz = (X - mean) / np.where(std < 1e-8, 1.0, std)

    k = int(_to_float(graph.get("k_neighbors"), 4.0))
    A = _build_knn_graph(Xz, k_neighbors=k)

    W1 = np.array(weights.get("W1"), dtype=float)
    b1 = np.array(weights.get("b1"), dtype=float)
    W2 = np.array(weights.get("W2"), dtype=float)
    b2 = np.array(weights.get("b2"), dtype=float)
    w_out = np.array(weights.get("w_out"), dtype=float)
    b_out = float(_to_float(weights.get("b_out"), 0.0))

    H1 = _relu(A @ Xz @ W1 + b1)
    H2 = _relu(A @ H1 @ W2 + b2)
    node_scores = _sigmoid(H2 @ w_out + b_out)

    risk_score = float(np.clip(np.mean(node_scores), 0.0, 1.0))
    confidence = float(np.clip(1.0 - np.std(node_scores), 0.0, 1.0))
    return {
        "node_scores": node_scores.tolist(),
        "risk_score": risk_score,
        "confidence": confidence,
        "checkpoint_version": _to_str(checkpoint_payload.get("version"), "unknown"),
    }


def _build_model_c_shadow_proxy(panel: dict[str, Any]) -> dict[str, Any]:
    entries = panel.get("entries")
    if not isinstance(entries, list):
        entries = []

    hazards: list[float] = []
    transitions: list[float] = []
    confidences: list[float] = []
    qualities: list[float] = []
    pseudo_flags = 0

    for row in entries:
        if not isinstance(row, dict):
            continue
        micro = row.get("micro")
        gates = row.get("gates")
        macro = row.get("macro")
        if isinstance(micro, dict):
            transitions.append(_to_float(micro.get("pct_transition"), 0.0))
            confidences.append(_to_float(micro.get("mean_confidence"), 0.5))
            qualities.append(_to_float(micro.get("mean_quality"), 0.5))
        if isinstance(gates, dict):
            hazards.append(_to_float(gates.get("hazard_score"), 0.5))
        if isinstance(macro, dict) and bool(macro.get("pseudo_bifurcation_flag", False)):
            pseudo_flags += 1

    n = len(entries)
    if n == 0:
        return {
            "mode": "shadow_proxy_fallback",
            "status": "insufficient_data",
            "risk_score": 0.5,
            "confidence": 0.2,
            "regime": "indefinido",
            "metrics": {},
            "publish_ready": False,
            "reasons": ["risk_truth_panel_sem_entries"],
        }

    mean_hazard = float(np.mean(hazards)) if hazards else 0.5
    mean_transition = float(np.mean(transitions)) if transitions else 0.5
    mean_conf = float(np.mean(confidences)) if confidences else 0.5
    mean_quality = float(np.mean(qualities)) if qualities else 0.5
    dispersion = float(np.std(confidences)) if confidences else 0.0
    pseudo_rate = _safe_pct(float(pseudo_flags), float(n))
    risk_score = float(
        np.clip(
            0.40 * np.clip(mean_transition, 0.0, 1.0)
            + 0.35 * np.clip(mean_hazard, 0.0, 1.0)
            + 0.25 * np.clip(1.0 - mean_conf, 0.0, 1.0),
            0.0,
            1.0,
        )
    )
    confidence = float(np.clip(0.2 + 0.5 * mean_quality + 0.3 * np.clip(1.0 - pseudo_rate, 0.0, 1.0), 0.0, 1.0))
    if risk_score < 0.35:
        regime = "stable"
    elif risk_score < 0.65:
        regime = "transition"
    else:
        regime = "stress"
    reasons = ["checkpoint_model_c_ausente"]
    if n < 8:
        reasons.append("cobertura_painel_baixa")
    if pseudo_rate > 0.15:
        reasons.append("pseudo_bifurcation_rate_alta")
    if mean_quality < 0.5:
        reasons.append("qualidade_media_baixa")
    return {
        "mode": "shadow_proxy_fallback",
        "status": "watch",
        "risk_score": risk_score,
        "confidence": confidence,
        "regime": regime,
        "metrics": {
            "assets_considered": n,
            "mean_hazard": mean_hazard,
            "mean_transition": mean_transition,
            "mean_confidence": mean_conf,
            "mean_quality": mean_quality,
            "confidence_dispersion": dispersion,
            "pseudo_bifurcation_rate": pseudo_rate,
        },
        "publish_ready": False,
        "reasons": reasons,
    }


def _build_model_c(*, panel: dict[str, Any], checkpoint_path: Path) -> dict[str, Any]:
    X, summary = _extract_model_c_inputs(panel)
    n = int(X.shape[0])
    if n == 0:
        return {
            "mode": "gnn_checkpoint",
            "status": "insufficient_data",
            "risk_score": 0.5,
            "confidence": 0.2,
            "regime": "indefinido",
            "metrics": {},
            "publish_ready": False,
            "reasons": ["risk_truth_panel_sem_entries"],
            "checkpoint_path": str(checkpoint_path),
        }

    if not checkpoint_path.exists():
        return _build_model_c_shadow_proxy(panel)

    ckpt_payload = _read_json(checkpoint_path, {})
    if not isinstance(ckpt_payload, dict):
        return _build_model_c_shadow_proxy(panel)

    try:
        infer = _infer_model_c_checkpoint(ckpt_payload, X)
    except Exception as exc:
        out = _build_model_c_shadow_proxy(panel)
        out["reasons"] = list(dict.fromkeys([*out.get("reasons", []), f"checkpoint_invalido:{type(exc).__name__}"]))
        return out

    risk_score = float(np.clip(infer.get("risk_score", 0.5), 0.0, 1.0))
    confidence = float(np.clip(infer.get("confidence", 0.5), 0.0, 1.0))
    if risk_score < 0.35:
        regime = "stable"
    elif risk_score < 0.65:
        regime = "transition"
    else:
        regime = "stress"

    reasons: list[str] = []
    if summary.get("assets_considered", 0) < 8:
        reasons.append("cobertura_painel_baixa")
    if summary.get("pseudo_bifurcation_rate", 1.0) > 0.15:
        reasons.append("pseudo_bifurcation_rate_alta")
    if summary.get("mean_quality", 0.0) < 0.5:
        reasons.append("qualidade_media_baixa")
    if confidence < 0.45:
        reasons.append("confianca_baixa_model_c")
    publish_ready = len(reasons) == 0

    return {
        "mode": "gnn_checkpoint",
        "status": "ok" if publish_ready else "watch",
        "risk_score": risk_score,
        "confidence": confidence,
        "regime": regime,
        "metrics": {
            "assets_considered": int(summary.get("assets_considered", 0)),
            "mean_quality": float(summary.get("mean_quality", 0.0)),
            "pseudo_bifurcation_rate": float(summary.get("pseudo_bifurcation_rate", 1.0)),
            "confidence_dispersion": float(summary.get("confidence_dispersion", 1.0)),
            "node_score_min": float(np.min(infer.get("node_scores", [risk_score]))),
            "node_score_max": float(np.max(infer.get("node_scores", [risk_score]))),
            "node_score_std": float(np.std(infer.get("node_scores", [risk_score]))),
        },
        "publish_ready": publish_ready,
        "reasons": reasons,
        "checkpoint_path": str(checkpoint_path),
        "checkpoint_version": _to_str(ckpt_payload.get("version"), "unknown"),
    }


def _build_integrity(run_ctx: RunContext, instruction_core: dict[str, Any]) -> dict[str, Any]:
    rows = run_ctx.rows
    summary = run_ctx.summary
    gate = summary.get("deployment_gate") if isinstance(summary, dict) else {}
    if not isinstance(gate, dict):
        gate = {}
    gate_blocked = bool(gate.get("blocked", False))

    run_ids = {str(r.get("run_id", "")) for r in rows if isinstance(r, dict)}
    run_id_ok = run_ids.issubset({run_ctx.run_id, ""})
    has_policy = bool(_to_str(summary.get("policy_path"), "")) or (ROOT / "config" / "production_gate.v1.json").exists()
    status_ok = _to_str(summary.get("status"), "").lower() == "ok"
    has_instruction_core = bool(instruction_core.get("version"))
    rows_ok = len(rows) > 0

    checks = {
        "rows_available": rows_ok,
        "run_id_consistent": run_id_ok,
        "status_ok": status_ok,
        "policy_declared": has_policy,
        "instruction_core_loaded": has_instruction_core,
        "gate_unblocked": not gate_blocked,
    }
    ok = all(checks.values())
    reasons = [k for k, v in checks.items() if not bool(v)]
    gate_reasons = gate.get("reasons") if isinstance(gate.get("reasons"), list) else []
    return {
        "ok": ok,
        "checks": checks,
        "reasons": reasons,
        "gate_blocked": gate_blocked,
        "gate_reasons": [str(x) for x in gate_reasons],
    }


def _build_fusion(model_b: dict[str, Any], model_c: dict[str, Any], integrity: dict[str, Any]) -> dict[str, Any]:
    b_risk = _to_float(model_b.get("risk_score"), 0.5)
    c_risk = _to_float(model_c.get("risk_score"), 0.5)
    b_conf = _to_float(model_b.get("probability"), 0.5)
    c_conf = _to_float(model_c.get("confidence"), 0.5)

    risk = float(np.clip(0.45 * b_risk + 0.55 * c_risk, 0.0, 1.0))
    confidence = float(np.clip(0.5 * b_conf + 0.5 * c_conf, 0.0, 1.0))

    if risk < 0.35:
        level = "baixo"
    elif risk < 0.7:
        level = "medio"
    else:
        level = "alto"

    publishable = bool(integrity.get("ok", False)) and bool(model_c.get("publish_ready", False))
    reasons: list[str] = []
    if not bool(integrity.get("ok", False)):
        reasons.extend([f"integrity:{x}" for x in integrity.get("reasons", [])])
    if not bool(model_c.get("publish_ready", False)):
        reasons.extend([f"model_c:{x}" for x in model_c.get("reasons", [])])

    return {
        "risk_structural": risk,
        "confidence": confidence,
        "risk_level": level,
        "publishable": publishable,
        "publish_blockers": reasons,
        "weights": {"model_b": 0.45, "model_c": 0.55},
    }


def _build_text_summaries(payload: dict[str, Any]) -> tuple[str, str]:
    run = payload.get("run", {})
    fusion = payload.get("fusion", {})
    b = payload.get("model_b", {})
    c = payload.get("model_c", {})
    integ = payload.get("integrity", {})

    executive = "\n".join(
        [
            "Resumo executivo (copiloto):",
            f"- Run: {run.get('run_id', 'n/a')} | publishable: {fusion.get('publishable', False)}",
            f"- Risco estrutural: {fusion.get('risk_structural', 0):.3f} ({fusion.get('risk_level', 'indefinido')})",
            f"- Confianca agregada: {fusion.get('confidence', 0):.3f}",
            f"- Modelo B: regime={b.get('predicted_regime', '--')} risco={_to_float(b.get('risk_score'), 0):.3f}",
            f"- Modelo C: regime={c.get('regime', '--')} risco={_to_float(c.get('risk_score'), 0):.3f}",
            "- Sem recomendacao de compra/venda. Uso para diagnostico estrutural.",
        ]
    )

    technical = "\n".join(
        [
            "# Copilot Shadow Technical",
            "",
            f"- generated_at_utc: {payload.get('generated_at_utc', '')}",
            f"- run_id: {run.get('run_id', '')}",
            f"- run_status: {run.get('status', '')}",
            f"- gate_blocked: {integ.get('gate_blocked', False)}",
            f"- gate_reasons: {', '.join(integ.get('gate_reasons', [])) or 'none'}",
            f"- publishable: {fusion.get('publishable', False)}",
            f"- publish_blockers: {', '.join(fusion.get('publish_blockers', [])) or 'none'}",
            "",
            "## Model B",
            f"- mode: {b.get('mode', '')}",
            f"- predicted_regime: {b.get('predicted_regime', '')}",
            f"- probability: {_to_float(b.get('probability'), 0):.4f}",
            f"- risk_score: {_to_float(b.get('risk_score'), 0):.4f}",
            "",
            "## Model C",
            f"- mode: {c.get('mode', '')}",
            f"- status: {c.get('status', '')}",
            f"- regime: {c.get('regime', '')}",
            f"- risk_score: {_to_float(c.get('risk_score'), 0):.4f}",
            f"- confidence: {_to_float(c.get('confidence'), 0):.4f}",
            "",
            "## Fusion",
            f"- risk_structural: {_to_float(fusion.get('risk_structural'), 0):.4f}",
            f"- confidence: {_to_float(fusion.get('confidence'), 0):.4f}",
            f"- risk_level: {fusion.get('risk_level', '')}",
        ]
    )

    return executive, technical


def main() -> None:
    parser = argparse.ArgumentParser(description="Build copilot shadow artifact (model B + model C + gate).")
    parser.add_argument("--run-id", type=str, default="", help="Run id em results/ops/snapshots.")
    parser.add_argument("--out-root", type=str, default="results/ops/copilot", help="Diretorio raiz de saida.")
    parser.add_argument(
        "--model-c-checkpoint",
        type=str,
        default="models/model_c_gnn_checkpoint.json",
        help="Checkpoint do modelo C (GNN).",
    )
    parser.add_argument(
        "--instruction-core",
        type=str,
        default="config/copilot_instruction_core.v1.json",
        help="Arquivo de nucleo de instrucoes.",
    )
    args = parser.parse_args()

    run_ctx = _find_run(args.run_id.strip() or None)
    panel = _read_json(ROOT / "results" / "validation" / "risk_truth_panel.json", {})
    lab_context = _load_lab_context()
    instruction_core = _read_json(ROOT / args.instruction_core, {})
    checkpoint_path = ROOT / args.model_c_checkpoint

    model_b = _build_model_b(rows=run_ctx.rows, lab_context=lab_context)
    model_c = _build_model_c(panel=panel if isinstance(panel, dict) else {}, checkpoint_path=checkpoint_path)
    integrity = _build_integrity(run_ctx, instruction_core if isinstance(instruction_core, dict) else {})
    fusion = _build_fusion(model_b, model_c, integrity)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run": {
            "run_id": run_ctx.run_id,
            "status": _to_str(run_ctx.summary.get("status"), "unknown"),
            "summary_path": str(run_ctx.summary_path),
            "snapshot_path": str(run_ctx.snapshot_path),
            "policy_path": _to_str(run_ctx.summary.get("policy_path"), "production_policy_lock.json"),
            "official_window": _to_float(run_ctx.summary.get("official_window"), 120.0),
        },
        "instruction_core": {
            "path": str(ROOT / args.instruction_core),
            "version": _to_str(instruction_core.get("version"), "unknown") if isinstance(instruction_core, dict) else "missing",
        },
        "model_b": model_b,
        "model_c": model_c,
        "integrity": integrity,
        "fusion": fusion,
        "sources": [
            str(run_ctx.summary_path),
            str(run_ctx.snapshot_path),
            str(ROOT / "results" / "validation" / "risk_truth_panel.json"),
            str(ROOT / "results" / "lab_corr_macro" / _to_str(lab_context.get("run_id"), "missing") / "summary.json"),
            str(checkpoint_path),
        ],
    }

    out_root = ROOT / args.out_root
    out_dir = out_root / run_ctx.run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    shadow_path = out_dir / "shadow_summary.json"
    shadow_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    executive, technical = _build_text_summaries(payload)
    (out_dir / "executive_summary.txt").write_text(executive, encoding="utf-8")
    (out_dir / "technical_summary.md").write_text(technical, encoding="utf-8")

    latest = {
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_ctx.run_id,
        "run_dir": str(out_dir),
        "shadow_summary": str(shadow_path),
        "publishable": bool(fusion.get("publishable", False)),
    }
    (out_root / "latest_release.json").write_text(json.dumps(latest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        f"[copilot_shadow] run_id={run_ctx.run_id} "
        f"publishable={fusion.get('publishable', False)} "
        f"risk={_to_float(fusion.get('risk_structural'), 0.0):.3f} "
        f"confidence={_to_float(fusion.get('confidence'), 0.0):.3f}"
    )


if __name__ == "__main__":
    main()
