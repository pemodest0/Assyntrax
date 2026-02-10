#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MIN_POINTS = 200
OUTDIR_DEFAULT = ROOT / "results" / "validation" / "robustness"


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


def _regime_id_map(labels: np.ndarray) -> dict[str, int]:
    ordered: list[str] = []
    for lbl in labels.tolist():
        if lbl not in ordered:
            ordered.append(lbl)
    return {lbl: i for i, lbl in enumerate(ordered)}


def _agreement(a: list[str], b: list[str]) -> float:
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    xa = a[-n:]
    xb = b[-n:]
    return float(np.mean([u == v for u, v in zip(xa, xb)]))


def _fail_run(run_dir: Path, reason: str, meta: dict[str, Any]) -> None:
    _json_dump(run_dir / "run_meta.json", meta)
    _json_dump(run_dir / "summary.json", {"status": "fail", "reason": reason, **meta})
    pd.DataFrame(columns=["t", "date", "regime_id", "regime_label", "confidence", "quality"]).to_csv(
        run_dir / "regimes.csv", index=False
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Robustez leve: 6 execuÃ§Ãµes no mesmo dataset.")
    parser.add_argument("--dataset", type=str, default=None)
    parser.add_argument("--value-col", type=str, default="Close")
    parser.add_argument("--date-col", type=str, default="Date")
    parser.add_argument("--outdir", type=str, default=str(OUTDIR_DEFAULT))
    parser.add_argument("--n-micro", type=int, default=80)
    parser.add_argument("--n-regimes", type=int, default=4)
    parser.add_argument("--k-nn", type=int, default=5)
    parser.add_argument("--theiler", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=2.0)
    parser.add_argument("--timeframe", type=str, default="daily", choices=["daily", "weekly"])
    args = parser.parse_args()

    outdir = Path(args.outdir)
    runs_root = outdir / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)

    dataset = Path(args.dataset) if args.dataset else _default_dataset()
    if not dataset.exists():
        _json_dump(outdir / "aggregate.json", {"status": "fail", "reason": f"dataset nÃ£o encontrado: {dataset}"})
        print(f"[fail] dataset nÃ£o encontrado: {dataset}")
        return

    engine_available = True
    engine_reason = ""
    try:
        from engine.graph.core import run_graph_engine  # type: ignore
        from engine.graph.embedding import estimate_embedding_params  # type: ignore
    except Exception as exc:
        engine_available = False
        engine_reason = f"dependÃªncia do motor indisponÃ­vel: {exc}"

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
    date_values = pd.to_datetime(df[date_col], errors="coerce").astype("datetime64[ns]").to_numpy()[mask]
    if series.shape[0] < MIN_POINTS:
        _json_dump(outdir / "aggregate.json", {"status": "fail", "reason": f"dataset tem menos de {MIN_POINTS} pontos vÃ¡lidos"})
        print(f"[fail] dataset tem menos de {MIN_POINTS} pontos vÃ¡lidos")
        return

    # Grade fixa com 6 runs.
    grid: list[dict[str, Any]] = [
        {"window": 30, "tau_mode": "auto", "seed": 0},
        {"window": 30, "tau_mode": "auto", "seed": 1},
        {"window": 30, "tau_mode": 2, "seed": 2},
        {"window": 50, "tau_mode": "auto", "seed": 0},
        {"window": 50, "tau_mode": 2, "seed": 1},
        {"window": 50, "tau_mode": 2, "seed": 2},
    ]

    label_runs: list[list[str]] = []
    run_status: list[dict[str, Any]] = []

    for i, cfg in enumerate(grid):
        run_id = f"run_{i+1:02d}"
        run_dir = runs_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        window = int(cfg["window"])
        tau_mode = cfg["tau_mode"]
        seed = int(cfg["seed"])
        np.random.seed(seed)

        run_meta = {
            "run_id": run_id,
            "dataset": str(dataset),
            "value_col": args.value_col,
            "date_col": args.date_col,
            "window": window,
            "tau": tau_mode,
            "seed": seed,
            "n_micro": args.n_micro,
            "n_regimes": args.n_regimes,
            "k": args.k_nn,
            "theiler": args.theiler,
            "alpha": args.alpha,
            "timeframe": args.timeframe,
        }

        if not engine_available:
            _fail_run(run_dir, engine_reason, run_meta)
            run_status.append({"run_id": run_id, "status": "fail", "reason": engine_reason})
            continue

        # Janela leve via suavizaÃ§Ã£o rolling para testar sensibilidade.
        smoothed = pd.Series(series).rolling(window=window, min_periods=1).mean().to_numpy()

        try:
            m, tau_auto = estimate_embedding_params(smoothed, max_tau=20, max_m=6)
            tau = int(tau_auto if tau_mode == "auto" else tau_mode)
            result = run_graph_engine(
                smoothed,
                m=m,
                tau=tau,
                n_micro=args.n_micro,
                n_regimes=args.n_regimes,
                k_nn=args.k_nn,
                theiler=args.theiler,
                alpha=args.alpha,
                seed=seed,
                timeframe=args.timeframe,
            )
        except Exception as exc:
            _fail_run(run_dir, f"falha na execuÃ§Ã£o do motor: {exc}", run_meta)
            run_status.append({"run_id": run_id, "status": "fail", "reason": str(exc)})
            continue

        n = int(result.state_labels.shape[0])
        if n <= 0:
            _fail_run(run_dir, "motor retornou sÃ©rie vazia", run_meta)
            run_status.append({"run_id": run_id, "status": "fail", "reason": "empty_result"})
            continue

        start_idx = len(smoothed) - n
        dates = pd.to_datetime(date_values[start_idx:], errors="coerce").strftime("%Y-%m-%d")
        rid = _regime_id_map(result.state_labels)
        quality_score = float((result.quality or {}).get("score", np.nan))
        regimes_df = pd.DataFrame(
            {
                "t": np.arange(n, dtype=int),
                "date": dates,
                "regime_id": [rid[str(x)] for x in result.state_labels],
                "regime_label": result.state_labels.astype(str),
                "confidence": result.confidence.astype(float),
                "quality": np.repeat(quality_score, n),
            }
        )
        regimes_df.to_csv(run_dir / "regimes.csv", index=False)

        transitions = int((result.state_labels[1:] != result.state_labels[:-1]).sum()) if n > 1 else 0
        summary = {
            "status": "ok",
            "n_regimes": int(len(np.unique(result.state_labels))),
            "pct_transition": float(transitions / max(1, n - 1)),
            "mean_confidence": float(np.nanmean(result.confidence)),
            "mean_quality": quality_score if np.isfinite(quality_score) else None,
            "n_points": n,
        }

        run_meta["m"] = int(m)
        run_meta["tau_effective"] = int(tau)
        _json_dump(run_dir / "run_meta.json", run_meta)
        _json_dump(run_dir / "summary.json", summary)
        label_runs.append(result.state_labels.astype(str).tolist())
        run_status.append({"run_id": run_id, "status": "ok"})

    n_runs = len(grid)
    matrix = [[0.0 for _ in range(n_runs)] for _ in range(n_runs)]
    for i in range(n_runs):
        matrix[i][i] = 1.0
    for i, j in combinations(range(n_runs), 2):
        if i < len(label_runs) and j < len(label_runs) and run_status[i]["status"] == "ok" and run_status[j]["status"] == "ok":
            a = _agreement(label_runs[i], label_runs[j])
        else:
            a = 0.0
        matrix[i][j] = a
        matrix[j][i] = a

    off_diag = [matrix[i][j] for i in range(n_runs) for j in range(n_runs) if i != j]
    stability_score = float(np.mean(off_diag)) if off_diag else 0.0

    aggregate = {
        "status": "ok" if any(r["status"] == "ok" for r in run_status) else "fail",
        "runs": run_status,
        "pairwise_agreement": {
            "run_ids": [f"run_{i+1:02d}" for i in range(n_runs)],
            "matrix": matrix,
        },
        "stability_score": stability_score,
        "flags": ["unstable_if_score_below_0.55"],
    }
    _json_dump(outdir / "aggregate.json", aggregate)

    print(
        "robustness_sweep "
        f"status={aggregate['status']} stability_score={stability_score:.3f} "
        f"ok_runs={sum(1 for r in run_status if r['status'] == 'ok')}/{n_runs}"
    )


if __name__ == "__main__":
    main()

