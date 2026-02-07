from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from graph_engine.core import run_graph_engine
from graph_engine.embedding import estimate_embedding_params, takens_embed
from graph_engine.diagnostics import estimate_tau_adaptive, estimate_embedding_dim, estimate_lle_rosenstein, _rqa_metrics
from graph_engine.export import write_asset_bundle
from graph_engine.schema import GraphAsset, GraphConfig, GraphLinks, GraphMetrics, GraphState, iso_now


def _load_series(path: Path) -> pd.Series:
    df = pd.read_csv(path)
    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError(f"missing columns in {path.name} (need date,value)")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "value"]).sort_values("date")
    return pd.Series(df["value"].values, index=df["date"])


def _build_regimes(index: pd.DatetimeIndex, labels: np.ndarray, conf: np.ndarray) -> list[dict]:
    n = min(len(index), len(labels))
    aligned_dates = index[-n:]
    out = []
    for i in range(n):
        out.append(
            {
                "date": aligned_dates[i].date().isoformat(),
                "regime": str(labels[i]),
                "confidence": float(conf[i]),
            }
        )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline imobiliario (realestate) com Assyntrax.")
    parser.add_argument("--input-dir", default="data/realestate/normalized", help="Pasta com CSVs normalizados.")
    parser.add_argument("--outdir", default="results/realestate", help="Pasta de saida.")
    parser.add_argument("--timeframe", default="monthly", choices=["monthly", "weekly", "daily"])
    parser.add_argument("--auto-embed", action="store_true")
    parser.add_argument("--tau-method", default="ami", choices=["ami", "acf"])
    parser.add_argument("--m-method", default="cao", choices=["cao", "fnn"])
    parser.add_argument("--m", type=int, default=3)
    parser.add_argument("--tau", type=int, default=1)
    parser.add_argument("--n-micro", type=int, default=200)
    parser.add_argument("--n-regimes", type=int, default=4)
    parser.add_argument("--k-nn", type=int, default=10)
    parser.add_argument("--theiler", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=2.0)
    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    assets = []
    for csv in sorted(input_dir.glob("*.csv")):
        asset = csv.stem.upper()
        series = _load_series(csv)
        values = series.values.astype(float)

        if args.auto_embed:
            m_use, tau_use = estimate_embedding_params(values, tau_method=args.tau_method, m_method=args.m_method)
        else:
            m_use, tau_use = args.m, args.tau

        emb = takens_embed(values, m=m_use, tau=tau_use)
        n_micro_eff = min(args.n_micro, max(5, emb.shape[0] // 4))
        n_reg_eff = min(args.n_regimes, max(2, n_micro_eff // 4))
        result = run_graph_engine(
            values,
            m=m_use,
            tau=tau_use,
            n_micro=n_micro_eff,
            n_regimes=n_reg_eff,
            k_nn=args.k_nn,
            theiler=args.theiler,
            alpha=args.alpha,
            timeframe=args.timeframe,
        )
        rqa = _rqa_metrics(emb)
        lle = estimate_lle_rosenstein(emb, theiler=args.theiler)
        tau_info = estimate_tau_adaptive(values, max_lag=min(20, max(5, len(values) // 4)))
        cao_info = estimate_embedding_dim(values, tau=tau_use, max_dim=min(10, max(3, m_use + 3)))

        regimes = _build_regimes(series.index, result.state_labels, result.confidence)

        base = f"{asset}_{args.timeframe}"
        links = GraphLinks(
            regimes_csv=f"assets/{base}_regimes.csv",
            embedding_csv=f"assets/{base}_embedding.csv",
            micrograph_json=f"assets/{base}_micrograph.json",
            transitions_json=f"assets/{base}_transitions.json",
        )
        asset_obj = GraphAsset(
            asset=asset,
            timeframe=args.timeframe,
            asof=iso_now(),
            group="realestate",
            state=GraphState(label=str(result.state_labels[-1]), confidence=float(result.confidence[-1])),
            graph=GraphConfig(n_micro=n_micro_eff, k_nn=args.k_nn, theiler=args.theiler, alpha=args.alpha, method="spectral"),
            metrics=GraphMetrics(
                stay_prob=float(result.confidence[-1]),
                escape_prob=float(1.0 - result.confidence[-1]),
                stretch_mu=float(result.stretch_mu[-1]),
                stretch_frac_pos=float(result.stretch_frac_pos[-1]),
            ),
            alerts=[],
            links=links,
            diagnostics={
                "tau_info": tau_info[1],
                "cao": cao_info,
                "rqa_det": rqa.get("det"),
                "rqa_lam": rqa.get("lam"),
                "rqa_tt": rqa.get("tt"),
                "lle": lle.get("lle"),
                "ftle_recent": lle.get("ftle_recent"),
            },
        )

        write_asset_bundle(
            asset_obj,
            outdir,
            embedding=emb,
            regimes=regimes,
            micrograph=result.micrograph,
            transitions={"p_matrix": result.p_matrix.tolist()},
        )
        assets.append(asset_obj.to_dict())

    (outdir / "realestate_universe.json").write_text(json.dumps(assets, indent=2), encoding="utf-8")
    print(f"[ok] wrote {outdir}/realestate_universe.json")


if __name__ == "__main__":
    main()
