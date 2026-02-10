#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
try:
    from hmmlearn.hmm import GaussianHMM  # type: ignore
except Exception:
    GaussianHMM = None


def _load_series(path: Path) -> pd.Series:
    df = pd.read_csv(path)
    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError(f"missing columns in {path.name} (need date,value)")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "value"]).sort_values("date")
    return pd.Series(df["value"].astype(float).values, index=df["date"])


def main() -> None:
    parser = argparse.ArgumentParser(description="HMM regimes (realestate).")
    parser.add_argument("--input-dir", default="data/realestate/normalized")
    parser.add_argument("--outdir", default="results/realestate/hmm")
    parser.add_argument("--states", type=int, default=4)
    parser.add_argument("--min-samples", type=int, default=60)
    parser.add_argument(
        "--mode",
        choices=["auto", "hmm", "fallback"],
        default="auto",
        help="auto: usa hmmlearn quando disponivel; hmm: exige hmmlearn; fallback: sempre deterministico",
    )
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    for csv in sorted(Path(args.input_dir).glob("*.csv")):
        series = _load_series(csv)
        if len(series) < args.min_samples:
            continue
        vals = series.values.astype(float)
        ret = pd.Series(vals).pct_change().replace([np.inf, -np.inf], np.nan).dropna().values
        if ret.size < args.states * 5:
            continue
        vol = pd.Series(ret).rolling(6).std().fillna(0.0).values
        X = np.column_stack([ret, vol])
        X = X[np.isfinite(X).all(axis=1)]
        if X.shape[0] < args.states * 5:
            continue

        use_hmm = args.mode in ("auto", "hmm") and GaussianHMM is not None
        if args.mode == "hmm" and GaussianHMM is None:
            raise RuntimeError("hmmlearn indisponivel e --mode hmm foi solicitado")

        if use_hmm:
            model = GaussianHMM(
                n_components=args.states,
                covariance_type="diag",
                n_iter=200,
                random_state=42,
                min_covar=1e-6,
            )
            model.fit(X)
            states = model.predict(X)
            probs = model.predict_proba(X)
            transmat = model.transmat_.tolist()
            means = model.means_.tolist()
            covars = model.covars_.tolist()
            model_name = "hmmlearn_gaussian"
        else:
            # Fallback: deterministic latent states from quantiles of composite risk signal.
            ret_s = pd.Series(X[:, 0])
            vol_s = pd.Series(X[:, 1])
            z = (ret_s - ret_s.median()) / (ret_s.std(ddof=0) + 1e-9)
            zv = (vol_s - vol_s.median()) / (vol_s.std(ddof=0) + 1e-9)
            risk = (zv - z).to_numpy(dtype=float)
            qs = np.quantile(risk, np.linspace(0, 1, args.states + 1))
            states = np.digitize(risk, qs[1:-1], right=False).astype(int)
            probs = np.zeros((len(states), args.states), dtype=float)
            probs[np.arange(len(states)), states] = 1.0
            trans = np.zeros((args.states, args.states), dtype=float)
            for i in range(1, len(states)):
                trans[states[i - 1], states[i]] += 1.0
            row_sum = trans.sum(axis=1, keepdims=True)
            row_sum[row_sum == 0] = 1.0
            trans = trans / row_sum
            means = []
            covars = []
            for s in range(args.states):
                mask = states == s
                if mask.any():
                    xs = X[mask]
                    means.append(xs.mean(axis=0).tolist())
                    covars.append(np.var(xs, axis=0).tolist())
                else:
                    means.append([0.0, 0.0])
                    covars.append([1.0, 1.0])
            transmat = trans.tolist()
            model_name = "fallback_quantile_markov"

        out = {
            "asset": csv.stem.upper(),
            "states": int(args.states),
            "model": model_name,
            "mode_requested": args.mode,
            "hmmlearn_available": bool(GaussianHMM is not None),
            "transmat": transmat,
            "means": means,
            "covars": covars,
            "sequence": states.tolist(),
            "probabilities": probs.tolist(),
        }
        dest = outdir / f"{csv.stem.upper()}_hmm.json"
        dest.write_text(json.dumps(out, indent=2))
    print(f"[ok] wrote HMM outputs to {outdir}")


if __name__ == "__main__":
    main()
