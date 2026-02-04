#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[2]


def _discover_tickers(data_dir: Path) -> List[str]:
    if not data_dir.exists():
        return []
    return sorted(p.stem for p in data_dir.glob("*.csv"))


def _build_configs(args: argparse.Namespace) -> List[Dict[str, str]]:
    configs = []
    methods = ["spectral", "pcca"] if args.methods == "both" else [args.methods]
    embeds = ["manual", "auto_ami_cao", "auto_acf_fnn"] if args.embed_modes == "all" else [args.embed_modes]
    for method in methods:
        for embed in embeds:
            configs.append({"method": method, "embed": embed})
    return configs


def _run_command(cmd: List[str], dry_run: bool) -> int:
    print("[run]", " ".join(cmd))
    if dry_run:
        return 0
    return subprocess.call(cmd)


def _score_asset(asset: dict) -> float:
    quality = (asset.get("quality") or {}).get("score", 0.0)
    escape = (asset.get("metrics") or {}).get("escape_prob", 1.0)
    alerts = asset.get("alerts") or []
    penalty = 0.0
    if "LOW_CONFIDENCE" in alerts:
        penalty += 0.1
    if "REGIME_INSTAVEL" in alerts:
        penalty += 0.1
    if "LOW_QUALITY" in alerts or "LOW_QUALITY_FORCE_NOISY" in alerts:
        penalty += 0.2
    return float(quality * (1.0 - escape) - penalty)


def main() -> None:
    parser = argparse.ArgumentParser(description="Hypertest grid for Graph Regime Engine.")
    parser.add_argument("--data-dir", default="data/raw/finance/yfinance_daily")
    parser.add_argument("--tickers", default="", help="Comma-separated tickers (default: auto-discover)")
    parser.add_argument("--timeframes", default="daily,weekly")
    parser.add_argument("--mode", default="fast", choices=["fast", "heavy"])
    parser.add_argument("--n-micro", type=int, default=200)
    parser.add_argument("--n-regimes", type=int, default=4)
    parser.add_argument("--k-nn", type=int, default=10)
    parser.add_argument("--theiler", type=int, default=10)
    parser.add_argument("--alpha", type=float, default=2.0)
    parser.add_argument("--methods", default="both", choices=["spectral", "pcca", "both"])
    parser.add_argument("--embed-modes", default="all", choices=["manual", "auto_ami_cao", "auto_acf_fnn", "all"])
    parser.add_argument("--outdir", default="results/hypertest")
    parser.add_argument("--max-assets", type=int, default=0, help="Limit number of tickers for test runs")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    tickers = [t.strip() for t in args.tickers.split(",") if t.strip()] or _discover_tickers(data_dir)
    if args.max_assets > 0:
        tickers = tickers[: args.max_assets]
    timeframes = args.timeframes

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    configs = _build_configs(args)
    run_records = []

    for cfg in configs:
        run_id = f"{cfg['method']}_{cfg['embed']}_{args.mode}"
        cmd = [
            "python3",
            "scripts/bench/run_graph_regime_universe.py",
            "--tickers",
            ",".join(tickers),
            "--timeframes",
            timeframes,
            "--mode",
            args.mode,
            "--n-micro",
            str(args.n_micro),
            "--n-regimes",
            str(args.n_regimes),
            "--k-nn",
            str(args.k_nn),
            "--theiler",
            str(args.theiler),
            "--alpha",
            str(args.alpha),
            "--metastable-method",
            cfg["method"],
            "--run-id",
            run_id,
            "--outdir",
            "results/latest_graph",
        ]

        if cfg["embed"] == "manual":
            # manual defaults (m=3, tau=1) already applied in batch script
            pass
        elif cfg["embed"] == "auto_ami_cao":
            cmd += ["--auto-embed", "--tau-method", "ami", "--m-method", "cao"]
        elif cfg["embed"] == "auto_acf_fnn":
            cmd += ["--auto-embed", "--tau-method", "acf", "--m-method", "fnn"]

        code = _run_command(cmd, args.dry_run)
        if code != 0:
            print(f"[warn] run failed: {run_id}")
            continue

        run_path = Path(f"results/latest_graph_{run_id}")
        summary_daily = run_path / "summary_daily.json"
        summary_weekly = run_path / "summary_weekly.json"
        run_records.append(
            {
                "run_id": run_id,
                "path": str(run_path),
                "summary_daily": str(summary_daily) if summary_daily.exists() else None,
                "summary_weekly": str(summary_weekly) if summary_weekly.exists() else None,
            }
        )

    if args.dry_run:
        return

    # Build best-by-asset using aggregate scoring
    best_by_asset: Dict[Tuple[str, str], dict] = {}
    for rec in run_records:
        run_path = Path(rec["path"])
        for tf in ["daily", "weekly"]:
            universe_path = run_path / f"universe_{tf}.json"
            if not universe_path.exists():
                continue
            data = json.loads(universe_path.read_text())
            records = data.get("records", data) if isinstance(data, dict) else data
            for asset in records:
                key = (asset.get("asset"), asset.get("timeframe"))
                score = _score_asset(asset)
                current = best_by_asset.get(key)
                if current is None or score > current["score"]:
                    best_by_asset[key] = {
                        "asset": asset.get("asset"),
                        "timeframe": asset.get("timeframe"),
                        "score": score,
                        "run_id": rec["run_id"],
                        "quality": (asset.get("quality") or {}).get("score"),
                        "escape_prob": (asset.get("metrics") or {}).get("escape_prob"),
                        "state": (asset.get("state") or {}).get("label"),
                        "recommendation": asset.get("recommendation"),
                        "alerts": asset.get("alerts") or [],
                    }

    out = {
        "runs": run_records,
        "best_by_asset": list(best_by_asset.values()),
    }
    (outdir / "hypertest_summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"[ok] wrote {outdir}/hypertest_summary.json")


if __name__ == "__main__":
    main()
