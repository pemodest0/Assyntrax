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
OUTDIR_DEFAULT = ROOT / "results" / "validation" / "sanity"


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _make_fail(outdir: Path, reason: str, extra: dict[str, Any] | None = None) -> None:
    payload: dict[str, Any] = {
        "status": "fail",
        "reason": reason,
    }
    if extra:
        payload.update(extra)
    _json_dump(outdir / "summary.json", payload)
    print(f"[fail] {reason}")


def _infer_freq(date_series: pd.Series | None) -> str | None:
    if date_series is None:
        return None
    dt = pd.to_datetime(date_series, errors="coerce").dropna().sort_values()
    if dt.shape[0] < 3:
        return None
    try:
        out = pd.infer_freq(dt)
        return out
    except Exception:
        return None


def _build_input_profile(
    df: pd.DataFrame,
    value_col: str,
    date_col: str | None,
) -> dict[str, Any]:
    values = pd.to_numeric(df[value_col], errors="coerce")
    finite = values[np.isfinite(values)]
    dt = pd.to_datetime(df[date_col], errors="coerce") if date_col else None
    profile: dict[str, Any] = {
        "n_linhas": int(df.shape[0]),
        "n_nans": int(values.isna().sum()),
        "freq_inferida": _infer_freq(dt),
        "date_min": str(dt.min().date()) if dt is not None and dt.notna().any() else None,
        "date_max": str(dt.max().date()) if dt is not None and dt.notna().any() else None,
        "stats": {
            "min": float(finite.min()) if finite.shape[0] else None,
            "max": float(finite.max()) if finite.shape[0] else None,
            "mean": float(finite.mean()) if finite.shape[0] else None,
            "std": float(finite.std(ddof=0)) if finite.shape[0] else None,
            "q05": float(finite.quantile(0.05)) if finite.shape[0] else None,
            "q50": float(finite.quantile(0.5)) if finite.shape[0] else None,
            "q95": float(finite.quantile(0.95)) if finite.shape[0] else None,
        },
    }
    return profile


def _default_dataset() -> Path:
    candidates = [
        ROOT / "data" / "raw" / "finance" / "yfinance_daily" / "SPY.csv",
        ROOT / "data" / "raw" / "finance" / "yfinance_daily" / "QQQ.csv",
    ]
    for p in candidates:
        if p.exists():
            return p
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Sanity run minimo do motor de regimes (sem plots).")
    parser.add_argument("--dataset", type=str, default=None, help="Caminho do CSV de entrada.")
    parser.add_argument("--value-col", type=str, default="close", help="Coluna numÃ©rica principal.")
    parser.add_argument("--date-col", type=str, default=None, help="Coluna de data (opcional).")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--window", type=int, default=200)
    parser.add_argument("--n-micro", type=int, default=80)
    parser.add_argument("--n-regimes", type=int, default=4)
    parser.add_argument("--k-nn", type=int, default=5)
    parser.add_argument("--theiler", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=2.0)
    parser.add_argument("--timeframe", type=str, default="daily", choices=["daily", "weekly"])
    parser.add_argument("--outdir", type=str, default=str(OUTDIR_DEFAULT))
    args = parser.parse_args()

    np.random.seed(args.seed)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    try:
        from engine.graph.core import run_graph_engine  # type: ignore
        from engine.graph.embedding import estimate_embedding_params  # type: ignore
        from engine.graph.sanity import sanity_alerts  # type: ignore
    except Exception as exc:
        _make_fail(outdir, f"dependÃªncia do motor indisponÃ­vel: {exc}")
        return

    dataset = Path(args.dataset) if args.dataset else _default_dataset()
    if not dataset.exists():
        _make_fail(outdir, f"dataset nÃ£o encontrado: {dataset}")
        return

    try:
        df = pd.read_csv(dataset)
    except Exception as exc:
        _make_fail(outdir, f"falha ao ler CSV: {exc}")
        return

    value_col = _resolve_col(df, args.value_col) or _auto_value_col(df)
    date_col = _resolve_col(df, args.date_col) or _auto_date_col(df)
    if value_col is None:
        _make_fail(outdir, f"coluna de valor nÃ£o existe: {args.value_col}")
        return
    if date_col is None:
        _make_fail(outdir, f"coluna de data nÃ£o existe: {args.date_col}")
        return

    profile = _build_input_profile(df, value_col, date_col)
    _json_dump(outdir / "input_profile.json", profile)

    values = pd.to_numeric(df[value_col], errors="coerce").to_numpy()
    valid_mask = np.isfinite(values)
    if not valid_mask.any():
        _make_fail(outdir, "coluna de valor sem dados numÃ©ricos vÃ¡lidos")
        return

    values = values[valid_mask]
    if values.shape[0] < MIN_POINTS:
        _make_fail(outdir, f"dataset tem menos de {MIN_POINTS} pontos vÃ¡lidos", {"n_valid_points": int(values.shape[0])})
        return

    dates: np.ndarray | None = None
    if date_col:
        d = pd.to_datetime(df[date_col], errors="coerce").astype("datetime64[ns]")
        dates = d.to_numpy()[valid_mask]

    try:
        m, tau = estimate_embedding_params(values, max_tau=20, max_m=6)
        result = run_graph_engine(
            values,
            m=m,
            tau=tau,
            n_micro=args.n_micro,
            n_regimes=args.n_regimes,
            k_nn=args.k_nn,
            theiler=args.theiler,
            alpha=args.alpha,
            seed=args.seed,
            timeframe=args.timeframe,
        )
    except Exception as exc:
        _make_fail(outdir, f"falha na execuÃ§Ã£o do motor: {exc}")
        return

    n_embed = int(result.state_labels.shape[0])
    if n_embed <= 0:
        _make_fail(outdir, "motor retornou sÃ©rie vazia")
        return

    start_idx = int(values.shape[0] - n_embed)
    regime_ids = _regime_id_map(result.state_labels)
    quality_score = float((result.quality or {}).get("score", np.nan))

    if dates is not None and len(dates) >= values.shape[0]:
        aligned_dates = dates[start_idx:]
        out_dates = pd.to_datetime(aligned_dates, errors="coerce").strftime("%Y-%m-%d")
    else:
        out_dates = pd.Series([""] * n_embed, dtype=object)

    regimes_df = pd.DataFrame(
        {
            "t": np.arange(n_embed, dtype=int),
            "date": out_dates,
            "regime_id": [regime_ids[str(x)] for x in result.state_labels],
            "regime_label": result.state_labels.astype(str),
            "confidence": result.confidence.astype(float),
            "quality": np.repeat(quality_score, n_embed),
        }
    )
    regimes_df.to_csv(outdir / "regimes.csv", index=False)

    transition_idx = np.where(result.state_labels[1:] != result.state_labels[:-1])[0] + 1
    alerts_rows: list[dict[str, Any]] = []
    for idx in transition_idx.tolist():
        alerts_rows.append(
            {
                "t": int(idx),
                "date": str(out_dates.iloc[idx]) if isinstance(out_dates, pd.Series) else str(out_dates[idx]),
                "alert_type": "REGIME_TRANSITION",
                "severity": "medium",
                "score": 1.0,
            }
        )

    low_conf_idx = np.where(result.confidence < float(result.thresholds.get("conf_lo", 0.45)))[0]
    for idx in low_conf_idx.tolist():
        alerts_rows.append(
            {
                "t": int(idx),
                "date": str(out_dates.iloc[idx]) if isinstance(out_dates, pd.Series) else str(out_dates[idx]),
                "alert_type": "LOW_CONFIDENCE",
                "severity": "high" if result.confidence[idx] < 0.3 else "medium",
                "score": float(1.0 - result.confidence[idx]),
            }
        )

    extra = sanity_alerts(
        asset=dataset.stem,
        n_micro=args.n_micro,
        n_points=n_embed,
        escape_prob=float(1.0 - np.nanmean(result.confidence)),
        quality_score=quality_score if np.isfinite(quality_score) else 0.0,
        timeframe=args.timeframe,
    )
    for a in extra:
        alerts_rows.append(
            {
                "t": int(n_embed - 1),
                "date": str(out_dates.iloc[-1]) if isinstance(out_dates, pd.Series) and len(out_dates) else "",
                "alert_type": a,
                "severity": "high",
                "score": 1.0,
            }
        )

    alerts_df = pd.DataFrame(alerts_rows, columns=["t", "date", "alert_type", "severity", "score"])
    alerts_df.to_csv(outdir / "alerts.csv", index=False)

    run_meta = {
        "dataset": str(dataset),
        "value_col": value_col,
        "date_col": date_col,
        "seed": args.seed,
        "window": args.window,
        "tau": int(tau),
        "m": int(m),
        "k": int(args.k_nn),
        "n_micro": int(args.n_micro),
        "n_regimes": int(args.n_regimes),
        "theiler": int(args.theiler),
        "alpha": float(args.alpha),
        "timeframe": args.timeframe,
        "thresholds": {k: float(v) for k, v in (result.thresholds or {}).items()},
    }
    _json_dump(outdir / "run_meta.json", run_meta)

    transitions = int((result.state_labels[1:] != result.state_labels[:-1]).sum()) if n_embed > 1 else 0
    summary = {
        "status": "ok",
        "n_regimes": int(len(np.unique(result.state_labels))),
        "pct_transition": float(transitions / max(1, n_embed - 1)),
        "mean_confidence": float(np.nanmean(result.confidence)),
        "mean_quality": quality_score if np.isfinite(quality_score) else None,
        "n_alerts_total": int(alerts_df.shape[0]),
    }
    _json_dump(outdir / "summary.json", summary)

    print(
        "sanity_run ok | "
        f"rows={n_embed} regimes={summary['n_regimes']} "
        f"mean_conf={summary['mean_confidence']:.3f} alerts={summary['n_alerts_total']}"
    )


if __name__ == "__main__":
    main()

