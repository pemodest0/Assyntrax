from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def _load_series(path: Path) -> pd.Series:
    df = pd.read_csv(path)
    if "date" not in df.columns or "value" not in df.columns:
        raise ValueError(f"missing columns in {path.name} (need date,value)")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "value"]).sort_values("date")
    return pd.Series(df["value"].values, index=df["date"])


def _discretize(values: np.ndarray, bins: int) -> np.ndarray:
    qs = np.linspace(0.0, 1.0, bins + 1)
    edges = np.quantile(values, qs)
    if np.unique(edges).size < bins + 1:
        edges = np.linspace(float(values.min()), float(values.max()), bins + 1)
    return np.digitize(values, edges[1:-1], right=True)


def transfer_entropy(x: np.ndarray, y: np.ndarray, bins: int = 8) -> float:
    if len(x) != len(y) or len(x) < 5:
        return float("nan")
    xs = _discretize(x, bins)
    ys = _discretize(y, bins)
    y1 = ys[1:]
    y0 = ys[:-1]
    x0 = xs[:-1]

    # counts
    joint = {}
    cond_y = {}
    cond_yx = {}
    total = len(y1)
    for a, b, c in zip(y1, y0, x0):
        joint[(a, b, c)] = joint.get((a, b, c), 0) + 1
        cond_y[(a, b)] = cond_y.get((a, b), 0) + 1
        cond_yx[(b, c)] = cond_yx.get((b, c), 0) + 1

    te = 0.0
    for (a, b, c), n in joint.items():
        p_abc = n / total
        p_ab = cond_y.get((a, b), 1) / total
        p_bc = cond_yx.get((b, c), 1) / total
        p_b = sum(v for (yy, bb), v in cond_y.items() if bb == b) / total
        # p(a|b,c) / p(a|b)
        p_a_bc = p_abc / max(p_bc, 1e-12)
        p_a_b = p_ab / max(p_b, 1e-12)
        te += p_abc * np.log(max(p_a_bc, 1e-12) / max(p_a_b, 1e-12))
    return float(te)


def vnge_from_adjacency(a: np.ndarray) -> float:
    if a.size == 0:
        return float("nan")
    # symmetrize for VNGE
    a = np.asarray(a, dtype=float)
    a = np.nan_to_num(a, nan=0.0, posinf=0.0, neginf=0.0)
    a = 0.5 * (a + a.T)
    d = np.diag(a.sum(axis=1))
    l = d - a
    tr = np.trace(l)
    if tr <= 0:
        return 0.0
    rho = l / tr
    rho = rho + np.eye(rho.shape[0]) * 1e-12
    eig = np.linalg.eigvalsh(rho)
    eig = eig[eig > 1e-12]
    return float(-np.sum(eig * np.log(eig)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Transfer entropy graph + VNGE (realestate).")
    parser.add_argument("--input-dir", default="data/realestate/normalized")
    parser.add_argument("--bins", type=int, default=8)
    parser.add_argument("--threshold", type=float, default=0.0, help="Threshold de TE para arestas.")
    parser.add_argument("--outdir", default="results/realestate/te")
    args = parser.parse_args()

    series = {}
    for f in sorted(Path(args.input_dir).glob("*.csv")):
        s = _load_series(f)
        series[f.stem.upper()] = s
    if len(series) < 2:
        raise ValueError("need at least 2 series")

    # align common index
    df = pd.DataFrame(series).dropna()
    names = list(df.columns)
    n = len(names)
    te_mat = np.zeros((n, n), dtype=float)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            te_mat[i, j] = transfer_entropy(df[names[i]].values, df[names[j]].values, bins=args.bins)

    adj = (te_mat >= args.threshold).astype(float) * te_mat
    vnge = vnge_from_adjacency(adj)

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "te_matrix.json").write_text(
        json.dumps({"names": names, "te": te_mat.tolist()}, indent=2), encoding="utf-8"
    )
    (outdir / "adjacency.json").write_text(
        json.dumps({"names": names, "adjacency": adj.tolist(), "vnge": vnge}, indent=2), encoding="utf-8"
    )
    print(f"[ok] wrote {outdir}/te_matrix.json and adjacency.json")


if __name__ == "__main__":
    main()
