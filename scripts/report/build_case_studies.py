import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def _pick_assets(assets_dir: Path, preferred: list[str]) -> list[str]:
    available = set()
    for p in assets_dir.glob("*_plots"):
        name = p.name
        if name.endswith("_plots"):
            available.add(name[: -len("_plots")])
    ordered = [a for a in preferred if a in available]
    ordered.extend(sorted(available - set(ordered)))
    return ordered


def _case_from_asset(assets_dir: Path, asset: str, tf: str) -> dict | None:
    plots_dir = assets_dir / f"{asset}_{tf}_plots"
    if not plots_dir.exists():
        return None
    timeline = plots_dir / "timeline_regime.png"
    embedding = plots_dir / "embedding_2d.png"
    transitions = plots_dir / "transition_matrix.png"
    if not (timeline.exists() and embedding.exists() and transitions.exists()):
        return None

    meta_path = assets_dir / f"{asset}_{tf}.json"
    report_path = assets_dir / f"{asset}_{tf}_report.md"
    regimes_path = assets_dir / f"{asset}_{tf}_regimes.csv"
    micrograph_path = assets_dir / f"{asset}_{tf}_micrograph.json"

    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())

    case = {
        "asset": asset,
        "timeframe": tf,
        "title": f"{asset} • {tf}",
        "summary": {
            "state": meta.get("state"),
            "quality": meta.get("quality"),
            "metrics": meta.get("metrics"),
            "risk": meta.get("risk"),
            "alerts": meta.get("alerts"),
            "recommendation": meta.get("recommendation"),
            "scores": meta.get("scores"),
            "badges": meta.get("badges"),
        },
        "files": {
            "timeline_regime": str(timeline),
            "embedding_2d": str(embedding),
            "transition_matrix": str(transitions),
        },
        "data": {
            "report": str(report_path) if report_path.exists() else None,
            "regimes_csv": str(regimes_path) if regimes_path.exists() else None,
            "micrograph_json": str(micrograph_path) if micrograph_path.exists() else None,
            "asset_json": str(meta_path) if meta_path.exists() else None,
        },
    }
    return case


def main() -> None:
    parser = argparse.ArgumentParser(description="Build case studies JSON for dashboard.")
    parser.add_argument("--assets-dir", default="results/latest_graph/assets")
    parser.add_argument("--outdir", default="results/case_studies")
    parser.add_argument("--timeframes", default="daily,weekly")
    parser.add_argument("--assets", default="")
    parser.add_argument("--max-cases", type=int, default=12)
    args = parser.parse_args()

    assets_dir = Path(args.assets_dir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    preferred = [
        "SPY",
        "QQQ",
        "GLD",
        "TLT",
        "HYG",
        "VIX",
        "^VIX",
        "BTC-USD",
        "ETH-USD",
        "XLE",
        "XLF",
        "XLK",
        "XLV",
        "XLU",
        "XLRE",
        "EEM",
        "EFA",
        "EWJ",
        "EWZ",
    ]
    if args.assets:
        preferred = [a.strip() for a in args.assets.split(",") if a.strip()]

    assets = _pick_assets(assets_dir, preferred)
    timeframes = [t.strip() for t in args.timeframes.split(",") if t.strip()]

    cases = []
    for asset in assets:
        for tf in timeframes:
            case = _case_from_asset(assets_dir, asset, tf)
            if case is None:
                continue
            cases.append(case)
            if len(cases) >= args.max_cases:
                break
        if len(cases) >= args.max_cases:
            break

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "assets_dir": str(assets_dir),
        "timeframes": timeframes,
        "cases": cases,
    }

    out_path = outdir / "cases.json"
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"[ok] wrote {out_path}")


if __name__ == "__main__":
    main()
