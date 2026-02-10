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

OUTDIR_DEFAULT = ROOT / "results" / "validation" / "ablation"


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _load_series(dataset: Path, value_col: str, date_col: str | None) -> pd.DataFrame:
    df = pd.read_csv(dataset)
    cols = {str(c).lower(): str(c) for c in df.columns}
    vc = cols.get(str(value_col).lower())
    dc = cols.get(str(date_col).lower()) if date_col else None
    if vc is None:
        for cand in ["close", "adj_close", "value", "price"]:
            if cand in cols:
                vc = cols[cand]
                break
    if vc is None:
        raise ValueError(f"value col not found: {value_col}")
    if date_col and dc is None:
        for cand in ["date", "data", "datetime", "timestamp"]:
            if cand in cols:
                dc = cols[cand]
                break
        if dc is None:
            raise ValueError(f"date col not found: {date_col}")
    out = pd.DataFrame({"value": pd.to_numeric(df[vc], errors="coerce")})
    if date_col:
        out["date"] = pd.to_datetime(df[dc], errors="coerce")
    else:
        out["date"] = pd.RangeIndex(0, len(df), 1)
    out = out.dropna(subset=["value"]).reset_index(drop=True)
    if out.shape[0] < 300:
        raise ValueError("series too short for ablation")
    return out


def _phase_randomized(x: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = x.shape[0]
    xf = np.fft.rfft(x)
    amp = np.abs(xf)
    phase = np.angle(xf)
    rand_phase = rng.uniform(-np.pi, np.pi, size=phase.shape[0])
    rand_phase[0] = phase[0]
    if n % 2 == 0:
        rand_phase[-1] = phase[-1]
    xf_new = amp * np.exp(1j * rand_phase)
    y = np.fft.irfft(xf_new, n=n)
    return y.astype(float)


def _apply_hysteresis(labels: np.ndarray, min_run: int = 4) -> np.ndarray:
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
            if (j - i) < min_run:
                left = out[i - 1] if i > 0 else None
                right = out[j] if j < n else None
                repl = left if left is not None else right
                if repl is not None and repl != out[i]:
                    out[i:j] = repl
                    changed = True
            i = j
    return out


def _run_variant(name: str, series: np.ndarray, seed: int, m: int | None, tau: int | None, theiler: int) -> dict[str, Any]:
    from engine.graph.core import run_graph_engine
    from engine.graph.embedding import estimate_embedding_params

    if m is None or tau is None:
        m_hat, tau_hat = estimate_embedding_params(series, max_tau=20, max_m=6)
    else:
        m_hat, tau_hat = m, tau

    res = run_graph_engine(
        series,
        m=int(m_hat),
        tau=int(tau_hat),
        n_micro=80,
        n_regimes=4,
        k_nn=5,
        theiler=int(theiler),
        alpha=2.0,
        seed=seed,
        timeframe="daily",
    )
    labels = _apply_hysteresis(np.asarray(res.state_labels).astype(str), min_run=4)
    n = labels.shape[0]
    switches = int(np.sum(labels[1:] != labels[:-1])) if n > 1 else 0
    pct_transition = float(switches / max(1, n - 1))
    q = float((res.quality or {}).get("score", np.nan))
    quality = float(np.clip(q, 0.0, 1.0)) if np.isfinite(q) else 0.0
    conf = float(np.nanmean(np.asarray(res.confidence, dtype=float)))
    return {
        "variant": name,
        "m": int(m_hat),
        "tau": int(tau_hat),
        "theiler": int(theiler),
        "n_regimes": int(np.unique(labels).shape[0]),
        "pct_transition": pct_transition,
        "mean_confidence": conf,
        "mean_quality": quality,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Formal ablation: shuffle/phase/no-embedding/no-theiler.")
    parser.add_argument("--dataset", type=str, default=str(ROOT / "data" / "raw" / "finance" / "yfinance_daily" / "^VIX.csv"))
    parser.add_argument("--value-col", type=str, default="close")
    parser.add_argument("--date-col", type=str, default="date")
    parser.add_argument("--outdir", type=str, default=str(OUTDIR_DEFAULT))
    parser.add_argument("--seed", type=int, default=11)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    try:
        df = _load_series(Path(args.dataset), args.value_col, args.date_col)
    except Exception as exc:
        _json_dump(outdir / "ablation_report.json", {"status": "fail", "reason": str(exc)})
        print(f"[ablation] fail {exc}")
        return

    x = df["value"].to_numpy(dtype=float)
    rng = np.random.default_rng(args.seed)
    variants = [
        ("full", x, None, None, 10),
        ("no_embedding", x, 1, 1, 10),
        ("no_theiler", x, None, None, 0),
        ("shuffle", rng.permutation(x), None, None, 10),
        ("phase_randomized", _phase_randomized(x, args.seed + 1), None, None, 10),
    ]

    rows: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for name, s, m, tau, th in variants:
        try:
            rows.append(_run_variant(name, s, args.seed, m, tau, th))
        except Exception as exc:
            failures.append({"variant": name, "reason": str(exc)})

    detail = pd.DataFrame(rows)
    detail.to_csv(outdir / "ablation_detail.csv", index=False)
    if detail.empty:
        _json_dump(outdir / "ablation_report.json", {"status": "fail", "reason": "all_variants_failed", "failures": failures})
        print("[ablation] fail all variants")
        return

    def _row(name: str) -> dict[str, Any]:
        hit = detail[detail["variant"] == name]
        return hit.iloc[0].to_dict() if not hit.empty else {}

    full = _row("full")
    shuffle = _row("shuffle")
    phase = _row("phase_randomized")
    no_emb = _row("no_embedding")
    no_theiler = _row("no_theiler")

    q_full = float(full.get("mean_quality", np.nan))
    q_shuffle = float(shuffle.get("mean_quality", np.nan))
    q_phase = float(phase.get("mean_quality", np.nan))
    t_full = float(full.get("pct_transition", np.nan))
    t_no_theiler = float(no_theiler.get("pct_transition", np.nan))
    c_full = float(full.get("mean_confidence", np.nan))
    c_no_emb = float(no_emb.get("mean_confidence", np.nan))

    d_conf_shuffle = (c_full - float(shuffle.get("mean_confidence", np.nan))) if np.isfinite(c_full) else np.nan
    d_conf_phase = (c_full - float(phase.get("mean_confidence", np.nan))) if np.isfinite(c_full) else np.nan
    gates = {
        "placebo_rejection_shuffle": bool(np.isfinite(d_conf_shuffle) and d_conf_shuffle >= 0.12),
        "placebo_rejection_phase": bool(np.isfinite(d_conf_phase) and d_conf_phase >= 0.08),
        "theiler_effect_visible": bool(np.isfinite(t_full) and np.isfinite(t_no_theiler) and abs(t_no_theiler - t_full) >= 0.01),
        "embedding_adds_signal": bool(np.isfinite(c_no_emb) and np.isfinite(c_full) and (c_full - c_no_emb) >= 0.02),
    }
    required = ["placebo_rejection_shuffle", "placebo_rejection_phase", "theiler_effect_visible"]
    status = "ok" if all(gates[k] for k in required) else "fail"

    report = {
        "status": status,
        "dataset": str(Path(args.dataset)),
        "seed": args.seed,
        "rows": rows,
        "gates": gates,
        "deltas": {
            "quality_full_minus_shuffle": (q_full - q_shuffle) if np.isfinite(q_full) and np.isfinite(q_shuffle) else None,
            "quality_full_minus_phase": (q_full - q_phase) if np.isfinite(q_full) and np.isfinite(q_phase) else None,
            "confidence_full_minus_shuffle": d_conf_shuffle if np.isfinite(d_conf_shuffle) else None,
            "confidence_full_minus_phase": d_conf_phase if np.isfinite(d_conf_phase) else None,
            "transition_no_theiler_minus_full": (t_no_theiler - t_full) if np.isfinite(t_no_theiler) and np.isfinite(t_full) else None,
            "confidence_full_minus_no_embedding": (c_full - c_no_emb) if np.isfinite(c_full) and np.isfinite(c_no_emb) else None,
        },
        "failures": failures,
    }
    _json_dump(outdir / "ablation_report.json", report)
    print(f"[ablation] status={status} variants_ok={len(rows)} variants_fail={len(failures)}")


if __name__ == "__main__":
    main()

