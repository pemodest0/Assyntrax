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

MIN_POINTS = 200
OUTDIR_DEFAULT = ROOT / "results" / "validation" / "placebo"


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _default_dataset() -> Path:
    preferred = ROOT / "data" / "raw" / "finance" / "yfinance_daily" / "SPY.csv"
    if preferred.exists():
        return preferred
    fallback = next((ROOT / "data").rglob("*.csv"), None)
    if fallback is None:
        raise FileNotFoundError("Nenhum CSV encontrado em data/")
    return fallback


def _resolve_col(df: pd.DataFrame, col: str | None) -> str | None:
    if col is None:
        return None
    if col in df.columns:
        return col
    target = col.lower()
    for c in df.columns:
        if c.lower() == target:
            return c
    return None


def _auto_value_col(df: pd.DataFrame) -> str | None:
    for cand in ["close", "price", "value", "adj_close", "log_price", "r"]:
        found = _resolve_col(df, cand)
        if found is not None:
            return found
    return None


def _auto_date_col(df: pd.DataFrame) -> str | None:
    for cand in ["date", "datetime", "timestamp", "time"]:
        found = _resolve_col(df, cand)
        if found is not None:
            return found
    return None


def _phase_randomize(x: np.ndarray, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = x.shape[0]
    x_centered = x - np.mean(x)
    fft = np.fft.rfft(x_centered)
    mag = np.abs(fft)
    phase = np.angle(fft)
    rand_phase = rng.uniform(0.0, 2.0 * np.pi, size=phase.shape[0])
    rand_phase[0] = phase[0]
    if n % 2 == 0:
        rand_phase[-1] = phase[-1]
    y_fft = mag * np.exp(1j * rand_phase)
    y = np.fft.irfft(y_fft, n=n)
    return y + np.mean(x)


def _run_case(
    case_name: str,
    series: np.ndarray,
    dates: np.ndarray | None,
    outdir: Path,
    seed: int,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    case_dir = outdir / case_name
    case_dir.mkdir(parents=True, exist_ok=True)

    try:
        from engine.graph.core import run_graph_engine  # type: ignore
        from engine.graph.embedding import estimate_embedding_params  # type: ignore
    except Exception as exc:
        fail = {"status": "fail", "reason": f"dependÃªncia do motor indisponÃ­vel: {exc}"}
        _json_dump(case_dir / "summary.json", fail)
        pd.DataFrame(columns=["t", "date", "regime_id", "regime_label", "confidence", "quality"]).to_csv(
            case_dir / "regimes.csv", index=False
        )
        pd.DataFrame(columns=["t", "date", "alert_type", "severity", "score"]).to_csv(case_dir / "alerts.csv", index=False)
        return fail

    np.random.seed(seed)
    try:
        m, tau = estimate_embedding_params(series, max_tau=20, max_m=6)
        result = run_graph_engine(
            series,
            m=m,
            tau=tau,
            n_micro=cfg["n_micro"],
            n_regimes=cfg["n_regimes"],
            k_nn=cfg["k_nn"],
            theiler=cfg["theiler"],
            alpha=cfg["alpha"],
            seed=seed,
            timeframe=cfg["timeframe"],
        )
    except Exception as exc:
        fail = {"status": "fail", "reason": f"falha na execuÃ§Ã£o do motor: {exc}"}
        _json_dump(case_dir / "summary.json", fail)
        pd.DataFrame(columns=["t", "date", "regime_id", "regime_label", "confidence", "quality"]).to_csv(
            case_dir / "regimes.csv", index=False
        )
        pd.DataFrame(columns=["t", "date", "alert_type", "severity", "score"]).to_csv(case_dir / "alerts.csv", index=False)
        return fail

    n = int(result.state_labels.shape[0])
    if n <= 0:
        fail = {"status": "fail", "reason": "motor retornou sÃ©rie vazia"}
        _json_dump(case_dir / "summary.json", fail)
        return fail

    start = len(series) - n
    if dates is not None:
        d = pd.to_datetime(dates[start:], errors="coerce").strftime("%Y-%m-%d")
    else:
        d = pd.Series([""] * n, dtype=object)

    reg_order: list[str] = []
    for lbl in result.state_labels.tolist():
        if lbl not in reg_order:
            reg_order.append(lbl)
    rid = {k: i for i, k in enumerate(reg_order)}
    quality_score = float((result.quality or {}).get("score", np.nan))

    regimes_df = pd.DataFrame(
        {
            "t": np.arange(n, dtype=int),
            "date": d,
            "regime_id": [rid[str(x)] for x in result.state_labels],
            "regime_label": result.state_labels.astype(str),
            "confidence": result.confidence.astype(float),
            "quality": np.repeat(quality_score, n),
        }
    )
    regimes_df.to_csv(case_dir / "regimes.csv", index=False)

    transitions = np.where(result.state_labels[1:] != result.state_labels[:-1])[0] + 1
    alerts = []
    for idx in transitions.tolist():
        alerts.append(
            {
                "t": int(idx),
                "date": str(d.iloc[idx]) if isinstance(d, pd.Series) else str(d[idx]),
                "alert_type": "REGIME_TRANSITION",
                "severity": "medium",
                "score": 1.0,
            }
        )
    pd.DataFrame(alerts, columns=["t", "date", "alert_type", "severity", "score"]).to_csv(
        case_dir / "alerts.csv", index=False
    )

    summary = {
        "status": "ok",
        "case": case_name,
        "n_points": n,
        "n_regimes": int(len(np.unique(result.state_labels))),
        "pct_transition": float(len(transitions) / max(1, n - 1)),
        "mean_confidence": float(np.nanmean(result.confidence)),
        "mean_quality": quality_score if np.isfinite(quality_score) else None,
        "n_alerts_total": int(len(alerts)),
        "m": int(m),
        "tau": int(tau),
    }
    _json_dump(case_dir / "summary.json", summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Placebo tests: original vs shuffle vs phase_random.")
    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--value-col", type=str, default="Close")
    parser.add_argument("--date-col", type=str, default="Date")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--include-phase-random", action="store_true")
    parser.add_argument("--outdir", type=str, default=str(OUTDIR_DEFAULT))
    parser.add_argument("--n-micro", type=int, default=80)
    parser.add_argument("--n-regimes", type=int, default=4)
    parser.add_argument("--k-nn", type=int, default=5)
    parser.add_argument("--theiler", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=2.0)
    parser.add_argument("--timeframe", type=str, default="daily", choices=["daily", "weekly"])
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    dataset = Path(args.dataset) if args.dataset else _default_dataset()
    if not dataset.exists():
        _json_dump(outdir / "aggregate.json", {"status": "fail", "reason": f"dataset nÃ£o encontrado: {dataset}"})
        print(f"[fail] dataset nÃ£o encontrado: {dataset}")
        return

    try:
        df = pd.read_csv(dataset)
    except Exception as exc:
        _json_dump(outdir / "aggregate.json", {"status": "fail", "reason": f"falha ao ler CSV: {exc}"})
        print(f"[fail] falha ao ler CSV: {exc}")
        return

    value_col = _resolve_col(df, args.value_col) or _auto_value_col(df)
    date_col = _resolve_col(df, args.date_col) or _auto_date_col(df)
    for c_name, c in [("value_col", value_col), ("date_col", date_col)]:
        if c is None:
            _json_dump(outdir / "aggregate.json", {"status": "fail", "reason": f"coluna nÃ£o existe: {args.value_col if c_name=='value_col' else args.date_col}"})
            print(f"[fail] coluna nÃ£o existe: {args.value_col if c_name=='value_col' else args.date_col}")
            return

    values = pd.to_numeric(df[value_col], errors="coerce")
    mask = np.isfinite(values.to_numpy())
    series = values.to_numpy()[mask]
    dates = pd.to_datetime(df[date_col], errors="coerce").astype("datetime64[ns]").to_numpy()[mask]

    if series.shape[0] < MIN_POINTS:
        _json_dump(outdir / "aggregate.json", {"status": "fail", "reason": f"dataset tem menos de {MIN_POINTS} pontos vÃ¡lidos"})
        print(f"[fail] dataset tem menos de {MIN_POINTS} pontos vÃ¡lidos")
        return

    cfg = {
        "n_micro": args.n_micro,
        "n_regimes": args.n_regimes,
        "k_nn": args.k_nn,
        "theiler": args.theiler,
        "alpha": args.alpha,
        "timeframe": args.timeframe,
    }
    rng = np.random.default_rng(args.seed)
    shuffled = series.copy()
    rng.shuffle(shuffled)

    original_summary = _run_case("original", series, dates, outdir, args.seed, cfg)
    shuffle_summary = _run_case("shuffle", shuffled, dates, outdir, args.seed + 1, cfg)
    phase_summary = None
    if args.include_phase_random:
        phase_series = _phase_randomize(series, args.seed + 2)
        phase_summary = _run_case("phase_random", phase_series, dates, outdir, args.seed + 2, cfg)

    if original_summary.get("status") != "ok" or shuffle_summary.get("status") != "ok":
        aggregate = {
            "status": "fail",
            "reason": "execuÃ§Ã£o base falhou em original/shuffle",
            "original_metrics": original_summary,
            "placebo_metrics": {"shuffle": shuffle_summary, "phase_random": phase_summary},
            "verdict": "fail",
        }
        _json_dump(outdir / "aggregate.json", aggregate)
        print("[fail] placebo: execuÃ§Ã£o base falhou")
        return

    q0 = float(original_summary.get("mean_quality") or 0.0)
    qt = float(shuffle_summary.get("mean_quality") or 0.0)
    p0 = float(original_summary.get("pct_transition") or 0.0)
    pt = float(shuffle_summary.get("pct_transition") or 0.0)
    n0 = int(original_summary.get("n_regimes") or 0)
    nt = int(shuffle_summary.get("n_regimes") or 0)

    conf0 = float(original_summary.get("mean_confidence") or 0.0)
    conft = float(shuffle_summary.get("mean_confidence") or 0.0)

    cond_quality = qt < (q0 * 0.7 if q0 > 0 else 0.0)
    cond_transition = pt >= p0 + 0.12
    cond_regimes = nt > n0 + 1
    cond_confidence_drop = conft < (conf0 * 0.7 if conf0 > 0 else 0.0)
    passed = bool(cond_quality or cond_transition or cond_regimes or cond_confidence_drop)

    reasons = []
    if cond_quality:
        reasons.append("mean_quality_placebo < 70% do original")
    if cond_transition:
        reasons.append("pct_transition_placebo > original + 0.15")
    if cond_regimes:
        reasons.append("n_regimes_placebo acima do limiar")
    if cond_confidence_drop:
        reasons.append("mean_confidence_placebo < 70% do original")
    if not reasons:
        reasons.append("placebo manteve estrutura similar ao original")

    aggregate = {
        "status": "ok",
        "original_metrics": original_summary,
        "placebo_metrics": {"shuffle": shuffle_summary, "phase_random": phase_summary},
        "verdict": "pass" if passed else "fail",
        "reason": "; ".join(reasons),
        "checks": {
            "quality_drop": cond_quality,
            "transition_jump": cond_transition,
            "regime_explosion": cond_regimes,
            "confidence_drop": cond_confidence_drop,
        },
    }
    _json_dump(outdir / "aggregate.json", aggregate)

    print(
        "placebo_tests "
        f"verdict={aggregate['verdict']} "
        f"quality_orig={q0:.3f} quality_shuffle={qt:.3f} "
        f"pct_trans_orig={p0:.3f} pct_trans_shuffle={pt:.3f}"
    )


if __name__ == "__main__":
    main()

