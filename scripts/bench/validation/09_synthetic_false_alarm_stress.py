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

OUTDIR_DEFAULT = ROOT / "results" / "validation" / "synthetic_false_alarm_stress"


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _gen_white(n: int, rng: np.random.Generator) -> np.ndarray:
    return rng.normal(0.0, 1.0, n)


def _gen_ar1(n: int, rng: np.random.Generator, phi: float = 0.85) -> np.ndarray:
    x = np.zeros(n, dtype=float)
    e = rng.normal(0.0, 1.0, n)
    for t in range(1, n):
        x[t] = phi * x[t - 1] + e[t]
    return x


def _gen_sine(n: int, rng: np.random.Generator, period: int = 40) -> np.ndarray:
    t = np.arange(n)
    sig = np.sin(2.0 * np.pi * t / period)
    noise = rng.normal(0.0, 0.2, n)
    return sig + noise


def _gen_shift(n: int, rng: np.random.Generator) -> np.ndarray:
    # Controlled two-regime synthetic: low variance then high variance.
    split = n // 2
    a = rng.normal(0.0, 0.5, split)
    b = rng.normal(0.0, 2.0, n - split)
    x = np.concatenate([a, b])
    # Slight persistence after shift.
    for t in range(split + 1, n):
        x[t] = 0.35 * x[t - 1] + x[t]
    return x


def _label_kind(name: str) -> str:
    return "has_shift" if "shift" in name else "no_shift"


def _apply_hysteresis(labels: np.ndarray, min_run: int = 5) -> np.ndarray:
    if labels.size == 0:
        return labels
    out = labels.astype(str).copy()
    changed = True
    # Merge short-lived runs into neighboring dominant state.
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
                replacement = left if left is not None else right
                if replacement is not None and replacement != out[i]:
                    out[i:j] = replacement
                    changed = True
            i = j
    return out


def _run_one(
    series: np.ndarray,
    name: str,
    seed: int,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    from engine.graph.core import run_graph_engine
    from engine.graph.embedding import estimate_embedding_params

    m, tau = estimate_embedding_params(series, max_tau=20, max_m=6)
    res = run_graph_engine(
        series,
        m=m,
        tau=tau,
        n_micro=cfg["n_micro"],
        n_regimes=cfg["n_regimes"],
        k_nn=cfg["k_nn"],
        theiler=cfg["theiler"],
        alpha=cfg["alpha"],
        seed=seed,
        timeframe="daily",
    )
    labels_raw = res.state_labels.astype(str)
    labels = _apply_hysteresis(labels_raw, min_run=cfg["min_run"])
    # Metastable regime sequence is a lower-level signal from the graph engine.
    macro_seq = res.micro_regime[res.micro_labels]
    n = len(labels)
    switches = int(np.sum(labels[1:] != labels[:-1])) if n > 1 else 0
    pct_transition = switches / max(1, (n - 1))
    mean_conf = float(np.nanmean(res.confidence))
    q = float((res.quality or {}).get("score", np.nan))
    q = float(np.clip(q, 0.0, 1.0)) if np.isfinite(q) else 0.0
    return {
        "series_id": name,
        "kind": _label_kind(name),
        "n_points": int(series.shape[0]),
        "m": int(m),
        "tau": int(tau),
        "n_regimes": int(np.unique(labels).shape[0]),
        "n_switches": switches,
        "pct_transition": float(pct_transition),
        "mean_confidence": float(mean_conf),
        "mean_quality": q,
        "dominant_first_half": str(pd.Series(labels[: max(1, n // 2)]).mode().iloc[0]),
        "dominant_second_half": str(pd.Series(labels[max(1, n // 2) :]).mode().iloc[0]),
        "dominant_macro_first_half": int(pd.Series(macro_seq[: max(1, n // 2)]).mode().iloc[0]),
        "dominant_macro_second_half": int(pd.Series(macro_seq[max(1, n // 2) :]).mode().iloc[0]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Stress test sintÃ©tico para falso alarme do motor.")
    parser.add_argument("--outdir", type=str, default=str(OUTDIR_DEFAULT))
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--runs-per-type", type=int, default=6)
    parser.add_argument("--lengths", type=str, default="500,1000,2000")
    parser.add_argument("--fa-threshold", type=float, default=0.35, help="Threshold de pct_transition para falso alarme.")
    parser.add_argument("--n-micro", type=int, default=80)
    parser.add_argument("--n-regimes", type=int, default=4)
    parser.add_argument("--k-nn", type=int, default=5)
    parser.add_argument("--theiler", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=2.0)
    parser.add_argument("--min-run", type=int, default=4, help="Minimo de persistencia (histerese) para contar troca de regime.")
    parser.add_argument("--min-detect-rate", type=float, default=0.55, help="Taxa minima de deteccao para series com shift.")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    lengths = [int(x.strip()) for x in args.lengths.split(",") if x.strip()]
    cfg = {
        "n_micro": args.n_micro,
        "n_regimes": args.n_regimes,
        "k_nn": args.k_nn,
        "theiler": args.theiler,
        "alpha": args.alpha,
        "min_run": args.min_run,
    }

    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for n in lengths:
        for r in range(args.runs_per_type):
            seed = args.seed + (n * 13) + r
            rng = np.random.default_rng(seed)
            generators = {
                f"white_n{n}_r{r}": _gen_white(n, rng),
                f"ar1_n{n}_r{r}": _gen_ar1(n, rng),
                f"sine_n{n}_r{r}": _gen_sine(n, rng, period=max(20, n // 20)),
                f"shift_n{n}_r{r}": _gen_shift(n, rng),
            }
            for sid, series in generators.items():
                try:
                    row = _run_one(series, sid, seed, cfg)
                    rows.append(row)
                except Exception as exc:
                    failures.append({"series_id": sid, "reason": str(exc)})

    detail = pd.DataFrame(rows)
    detail.to_csv(outdir / "stress_detail.csv", index=False)

    if detail.empty:
        payload = {"status": "fail", "reason": "no_successful_runs", "failures": failures}
        _json_dump(outdir / "summary.json", payload)
        print("[fail] no successful synthetic runs")
        return

    no_shift = detail[detail["kind"] == "no_shift"].copy()
    has_shift = detail[detail["kind"] == "has_shift"].copy()

    fa_rate = float((no_shift["pct_transition"] > args.fa_threshold).mean()) if not no_shift.empty else 1.0
    if not has_shift.empty:
        has_shift_detect = (
            (has_shift["dominant_first_half"] != has_shift["dominant_second_half"])
            | (has_shift["dominant_macro_first_half"] != has_shift["dominant_macro_second_half"])
            | (has_shift["pct_transition"] > max(0.08, args.fa_threshold * 0.4))
        )
        detect_rate = float(has_shift_detect.mean())
    else:
        detect_rate = 0.0

    by_type = (
        detail.assign(series_type=detail["series_id"].str.split("_").str[0])
        .groupby("series_type", as_index=False)
        .agg(
            runs=("series_id", "count"),
            mean_pct_transition=("pct_transition", "mean"),
            mean_confidence=("mean_confidence", "mean"),
            mean_quality=("mean_quality", "mean"),
        )
        .sort_values("mean_pct_transition")
    )
    by_type.to_csv(outdir / "stress_by_type.csv", index=False)

    status = "pass"
    notes: list[str] = []
    if fa_rate > 0.35:
        status = "fail"
        notes.append("false alarm alto em series sem shift")
    if detect_rate < args.min_detect_rate:
        status = "fail"
        notes.append("baixa sensibilidade em series com shift controlado")
    if not notes:
        notes.append("trade-off falso alarme/sensibilidade aceitavel no threshold atual")

    summary = {
        "status": status,
        "seed": args.seed,
        "lengths": lengths,
        "runs_per_type": args.runs_per_type,
        "false_alarm_threshold_pct_transition": args.fa_threshold,
        "min_run_hysteresis": args.min_run,
        "min_detect_rate": args.min_detect_rate,
        "n_runs_success": int(detail.shape[0]),
        "n_runs_fail": int(len(failures)),
        "false_alarm_rate_no_shift": fa_rate,
        "detection_rate_has_shift": detect_rate,
        "mean_transition_no_shift": float(no_shift["pct_transition"].mean()) if not no_shift.empty else None,
        "mean_transition_has_shift": float(has_shift["pct_transition"].mean()) if not has_shift.empty else None,
        "notes": notes,
        "failures": failures[:30],
    }
    _json_dump(outdir / "summary.json", summary)
    print(
        f"[synthetic_stress] status={status} runs={summary['n_runs_success']} "
        f"fa_rate={fa_rate:.3f} detect_rate={detect_rate:.3f}"
    )


if __name__ == "__main__":
    main()

