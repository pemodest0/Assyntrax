#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
OUTDIR_DEFAULT = ROOT / "results" / "validation" / "calibration"


def _json_dump(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def _infer_domain(asset: str) -> str:
    a = asset.upper()
    if a.startswith("RE_"):
        return "realestate"
    if "ONS_" in a:
        return "energy"
    return "finance"


def _apply_hysteresis(labels: np.ndarray, min_run: int) -> np.ndarray:
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
            run_len = j - i
            if run_len < min_run:
                left = out[i - 1] if i > 0 else None
                right = out[j] if j < n else None
                repl = left if left is not None else right
                if repl is not None and repl != out[i]:
                    out[i:j] = repl
                    changed = True
            i = j
    return out


def _transition_block_rate(labels: np.ndarray, years: float) -> float:
    if labels.size <= 1 or years <= 0:
        return 0.0
    # Count contiguous blocks where label includes "trans".
    is_trans = np.array(["trans" in str(x).lower() for x in labels], dtype=bool)
    starts = np.where((is_trans[1:] == 1) & (is_trans[:-1] == 0))[0] + 1
    n_blocks = int(starts.size + (1 if is_trans[0] else 0))
    return float(n_blocks / years)


def _load_regimes(universe_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for p in sorted(universe_dir.glob("*/regimes.csv")):
        asset = p.parent.name
        try:
            df = pd.read_csv(p)
        except Exception:
            continue
        if "regime_label" not in df.columns:
            continue
        if "date" in df.columns:
            d = pd.to_datetime(df["date"], errors="coerce")
        else:
            d = pd.Series([pd.NaT] * len(df))
        for i, lbl in enumerate(df["regime_label"].astype(str).tolist()):
            rows.append(
                {
                    "asset": asset,
                    "domain": _infer_domain(asset),
                    "t": i,
                    "date": d.iloc[i] if i < len(d) else pd.NaT,
                    "label": lbl,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibracao por taxa-alvo de switch/transition por dominio.")
    parser.add_argument("--universe-dir", type=str, default=str(ROOT / "results" / "validation" / "universe_mini"))
    parser.add_argument("--outdir", type=str, default=str(OUTDIR_DEFAULT))
    parser.add_argument("--targets", type=str, default="finance:30:80:2:10,realestate:4:24:1:6,energy:10:40:1:8")
    parser.add_argument("--min-run-grid", type=str, default="1,2,3,4,5,6,8,10")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    regimes = _load_regimes(Path(args.universe_dir))
    if regimes.empty:
        _json_dump(outdir / "summary.json", {"status": "fail", "reason": "no_regimes_found"})
        print("[calibration] fail no_regimes_found")
        return

    target_cfg: dict[str, dict[str, float]] = {}
    for part in args.targets.split(","):
        dom, s_lo, s_hi, b_lo, b_hi = part.split(":")
        target_cfg[dom.strip()] = {
            "switch_lo": float(s_lo),
            "switch_hi": float(s_hi),
            "block_lo": float(b_lo),
            "block_hi": float(b_hi),
        }
    min_run_grid = [int(x.strip()) for x in args.min_run_grid.split(",") if x.strip()]

    details: list[dict[str, Any]] = []
    for domain, dg in regimes.groupby("domain"):
        for asset, ag in dg.groupby("asset"):
            labels_raw = ag.sort_values("t")["label"].to_numpy(dtype=str)
            dates = pd.to_datetime(ag.sort_values("t")["date"], errors="coerce")
            if dates.notna().sum() >= 2:
                years = max(1.0 / 365.0, float((dates.max() - dates.min()).days / 365.25))
            else:
                years = max(1.0, len(labels_raw) / 252.0)
            for mr in min_run_grid:
                labels = _apply_hysteresis(labels_raw, mr)
                switches = int(np.sum(labels[1:] != labels[:-1])) if labels.size > 1 else 0
                switch_rate = float(switches / years)
                block_rate = _transition_block_rate(labels, years)
                details.append(
                    {
                        "domain": domain,
                        "asset": asset,
                        "min_run": mr,
                        "years": years,
                        "switch_rate_per_year": switch_rate,
                        "transition_block_rate_per_year": block_rate,
                    }
                )

    detail_df = pd.DataFrame(details)
    detail_df.to_csv(outdir / "switch_rate_grid.csv", index=False)

    rec_rows: list[dict[str, Any]] = []
    for domain, dg in detail_df.groupby("domain"):
        t = target_cfg.get(domain, {"switch_lo": 30, "switch_hi": 80, "block_lo": 2, "block_hi": 10})
        cand = []
        for mr, gg in dg.groupby("min_run"):
            s_mean = float(gg["switch_rate_per_year"].mean())
            b_mean = float(gg["transition_block_rate_per_year"].mean())
            # Distance to target band (0 inside band).
            s_pen = max(0.0, t["switch_lo"] - s_mean, s_mean - t["switch_hi"])
            b_pen = max(0.0, t["block_lo"] - b_mean, b_mean - t["block_hi"])
            cand.append((mr, s_mean, b_mean, s_pen + b_pen))
        cand.sort(key=lambda x: x[3])
        best = cand[0]
        rec_rows.append(
            {
                "domain": domain,
                "recommended_min_run": int(best[0]),
                "mean_switch_rate_per_year": float(best[1]),
                "mean_transition_block_rate_per_year": float(best[2]),
                "target_switch_lo": t["switch_lo"],
                "target_switch_hi": t["switch_hi"],
                "target_block_lo": t["block_lo"],
                "target_block_hi": t["block_hi"],
                "penalty": float(best[3]),
            }
        )

    rec_df = pd.DataFrame(rec_rows).sort_values("domain")
    rec_df.to_csv(outdir / "recommended_hysteresis_by_domain.csv", index=False)

    summary = {
        "status": "ok",
        "n_assets": int(regimes["asset"].nunique()),
        "domains": sorted(regimes["domain"].unique().tolist()),
        "outputs": {
            "grid": str(outdir / "switch_rate_grid.csv"),
            "recommended": str(outdir / "recommended_hysteresis_by_domain.csv"),
        },
    }
    _json_dump(outdir / "summary.json", summary)
    print(f"[calibration] ok assets={summary['n_assets']} domains={len(summary['domains'])}")


if __name__ == "__main__":
    main()

