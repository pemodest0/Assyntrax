#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    from hmmlearn.hmm import GaussianHMM  # type: ignore
except Exception:
    GaussianHMM = None
try:
    from sklearn.mixture import GaussianMixture  # type: ignore
except Exception:
    GaussianMixture = None

ROOT = Path(__file__).resolve().parents[3]


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _discover(max_per_sector: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    finance = sorted((ROOT / "data" / "raw" / "finance" / "yfinance_daily").glob("*.csv"))[:max_per_sector]
    for p in finance:
        rows.append({"sector": "finance", "asset": p.stem, "path": p, "date_col": "date", "value_col": "price"})

    energy = sorted((ROOT / "data" / "raw" / "ONS" / "ons_carga_diaria").glob("*.csv"))[:max_per_sector]
    for p in energy:
        rows.append(
            {
                "sector": "energy",
                "asset": p.stem,
                "path": p,
                "date_col": "din_instante",
                "value_col": "val_cargaenergiamwmed",
            }
        )

    real_estate = sorted((ROOT / "data" / "realestate" / "normalized").glob("*.csv"))[:max_per_sector]
    for p in real_estate:
        rows.append({"sector": "real_estate", "asset": p.stem, "path": p, "date_col": "date", "value_col": "value"})
    return rows


def _load_xy(path: Path, date_col: str, value_col: str, min_samples: int) -> tuple[pd.Series, np.ndarray] | None:
    df = pd.read_csv(path)
    if df.shape[1] == 1 and ";" in str(df.columns[0]):
        df = pd.read_csv(path, sep=";")
    cols = {c.lower(): c for c in df.columns}
    dcol = cols.get(date_col.lower())
    vcol = cols.get(value_col.lower())
    if dcol is None or vcol is None:
        return None

    dt = pd.to_datetime(df[dcol], errors="coerce")
    vv = pd.to_numeric(df[vcol], errors="coerce")
    dff = pd.DataFrame({"date": dt, "value": vv}).dropna().sort_values("date")
    if dff.shape[0] < min_samples:
        return None

    ret = dff["value"].pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    if ret.shape[0] < min_samples - 2:
        return None
    vol = ret.rolling(6).std().fillna(0.0)
    x = np.column_stack([ret.values.astype(float), vol.values.astype(float)])
    mask = np.isfinite(x).all(axis=1)
    if int(mask.sum()) < min_samples - 2:
        return None
    x = x[mask]
    idx = ret.index[mask]
    return dff.loc[idx, "date"].reset_index(drop=True), x


def _fallback_markov(x: np.ndarray, n_states: int) -> tuple[np.ndarray, np.ndarray]:
    ret_s = pd.Series(x[:, 0])
    vol_s = pd.Series(x[:, 1])
    z = (ret_s - ret_s.median()) / (ret_s.std(ddof=0) + 1e-9)
    zv = (vol_s - vol_s.median()) / (vol_s.std(ddof=0) + 1e-9)
    risk = (zv - z).to_numpy(dtype=float)
    qs = np.quantile(risk, np.linspace(0, 1, n_states + 1))
    states = np.digitize(risk, qs[1:-1], right=False).astype(int)
    probs = np.zeros((len(states), n_states), dtype=float)
    probs[np.arange(len(states)), states] = 1.0
    return states, probs


def _hmm_states(x: np.ndarray, n_states: int, seed: int) -> tuple[np.ndarray, np.ndarray] | None:
    if GaussianHMM is None:
        return None
    model = GaussianHMM(
        n_components=n_states,
        covariance_type="diag",
        n_iter=200,
        random_state=seed,
        min_covar=1e-6,
    )
    model.fit(x)
    return model.predict(x), model.predict_proba(x)


def _proxy_hmm_states(x: np.ndarray, n_states: int, seed: int) -> tuple[np.ndarray, np.ndarray] | None:
    if GaussianMixture is None:
        return None
    gmm = GaussianMixture(n_components=n_states, covariance_type="diag", random_state=seed, reg_covar=1e-6)
    gmm.fit(x)
    emit = np.clip(gmm.predict_proba(x), 1e-12, 1.0)
    hard = np.argmax(emit, axis=1)

    trans = np.ones((n_states, n_states), dtype=float) * 1e-3
    for i in range(1, len(hard)):
        trans[hard[i - 1], hard[i]] += 1.0
    trans = trans / np.clip(trans.sum(axis=1, keepdims=True), 1e-12, None)
    log_t = np.log(np.clip(trans, 1e-12, 1.0))
    log_e = np.log(emit)
    n = x.shape[0]
    dp = np.full((n, n_states), -np.inf, dtype=float)
    ptr = np.zeros((n, n_states), dtype=int)
    dp[0, :] = log_e[0, :] - np.log(float(n_states))
    for t in range(1, n):
        prev = dp[t - 1, :][:, None] + log_t
        ptr[t, :] = np.argmax(prev, axis=0)
        dp[t, :] = np.max(prev, axis=0) + log_e[t, :]
    states = np.zeros(n, dtype=int)
    states[-1] = int(np.argmax(dp[-1, :]))
    for t in range(n - 2, -1, -1):
        states[t] = int(ptr[t + 1, states[t + 1]])
    return states, emit


def _macro_from_states(x: np.ndarray, states: np.ndarray, n_states: int) -> np.ndarray:
    # Rank by risk proxy so labels are comparable across methods.
    risk = x[:, 1] - x[:, 0]
    order_vals = []
    for s in range(n_states):
        mask = states == s
        if mask.any():
            order_vals.append((s, float(np.nanmean(risk[mask]))))
        else:
            order_vals.append((s, -1e9))
    order_vals.sort(key=lambda z: z[1])
    rank = {state: i for i, (state, _) in enumerate(order_vals)}
    mapped = np.array([rank[int(s)] for s in states], dtype=int)
    # 0,1 -> stable ; 2 -> transition ; 3+ -> unstable
    macro = np.where(mapped <= 1, 0, np.where(mapped == 2, 1, 2))
    return macro


def main() -> None:
    parser = argparse.ArgumentParser(description="Compara HMM vs fallback por setor.")
    parser.add_argument("--outdir", default=str(ROOT / "results" / "validation" / "hmm_sector_check"))
    parser.add_argument("--max-per-sector", type=int, default=20)
    parser.add_argument("--min-samples", type=int, default=120)
    parser.add_argument("--states", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    assets = _discover(args.max_per_sector)
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for a in assets:
        loaded = _load_xy(Path(a["path"]), str(a["date_col"]), str(a["value_col"]), args.min_samples)
        if loaded is None:
            failures.append({"sector": a["sector"], "asset": a["asset"], "reason": "data_unavailable_or_short"})
            continue
        _, x = loaded
        states_f, _ = _fallback_markov(x, args.states)
        macro_f = _macro_from_states(x, states_f, args.states)
        trans_f = float(np.mean(macro_f[1:] != macro_f[:-1])) if macro_f.shape[0] > 1 else 0.0

        model_used = "hmmlearn"
        hmm = _hmm_states(x, args.states, args.seed)
        if hmm is None:
            hmm = _proxy_hmm_states(x, args.states, args.seed)
            model_used = "proxy_hmm"
        if hmm is None:
            rows.append(
                {
                    "sector": a["sector"],
                    "asset": a["asset"],
                    "n": int(x.shape[0]),
                    "hmm_available": False,
                    "comparison_model": "none",
                    "agreement_macro": None,
                    "delta_transition_rate": None,
                    "transition_rate_fallback": trans_f,
                    "transition_rate_hmm": None,
                    "status": "fallback_only",
                }
            )
            continue

        states_h, _ = hmm
        macro_h = _macro_from_states(x, states_h, args.states)
        trans_h = float(np.mean(macro_h[1:] != macro_h[:-1])) if macro_h.shape[0] > 1 else 0.0
        agreement = float(np.mean(macro_h == macro_f))
        rows.append(
            {
                "sector": a["sector"],
                "asset": a["asset"],
                "n": int(x.shape[0]),
                "hmm_available": True,
                "comparison_model": model_used,
                "agreement_macro": agreement,
                "delta_transition_rate": abs(trans_h - trans_f),
                "transition_rate_fallback": trans_f,
                "transition_rate_hmm": trans_h,
                "status": "ok",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(outdir / "asset_comparison.csv", index=False)
    _save_json(outdir / "failures.json", {"failures": failures, "count": len(failures)})

    if df.empty:
        summary = {"status": "fail", "reason": "no_assets_evaluated", "hmm_available": bool(GaussianHMM is not None)}
        _save_json(outdir / "summary.json", summary)
        print("[hmm_sector_check] status=fail no assets")
        return

    ok_df = df[df["status"] == "ok"].copy()
    by_sector = {}
    for sector in sorted(df["sector"].unique()):
        d = df[df["sector"] == sector]
        ok = d[d["status"] == "ok"]
        by_sector[sector] = {
            "assets_total": int(d.shape[0]),
            "assets_ok": int(ok.shape[0]),
            "assets_fallback_only": int((d["status"] == "fallback_only").sum()),
            "models_used": sorted(set(d["comparison_model"].dropna().astype(str).tolist()))
            if "comparison_model" in d.columns
            else [],
            "mean_agreement_macro": float(ok["agreement_macro"].mean()) if not ok.empty else None,
            "mean_delta_transition_rate": float(ok["delta_transition_rate"].mean()) if not ok.empty else None,
        }

    summary = {
        "status": "ok",
        "hmmlearn_available": bool(GaussianHMM is not None),
        "proxy_hmm_available": bool(GaussianMixture is not None),
        "assets_total": int(df.shape[0]),
        "assets_ok": int(ok_df.shape[0]),
        "assets_fallback_only": int((df["status"] == "fallback_only").sum()),
        "mean_agreement_macro": float(ok_df["agreement_macro"].mean()) if not ok_df.empty else None,
        "mean_delta_transition_rate": float(ok_df["delta_transition_rate"].mean()) if not ok_df.empty else None,
        "by_sector": by_sector,
        "interpretation": {
            "agreement_macro_high_if": ">=0.70",
            "delta_transition_low_if": "<=0.10",
            "recommendation": "Se acordo alto e delta baixo, fallback e HMM convergem; pode operar com fallback quando hmmlearn indisponivel.",
        },
    }
    _save_json(outdir / "summary.json", summary)
    print(
        f"[hmm_sector_check] status=ok assets={summary['assets_total']} "
        f"hmmlearn_available={summary['hmmlearn_available']} "
        f"agreement={summary['mean_agreement_macro']}"
    )


if __name__ == "__main__":
    main()
