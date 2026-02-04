#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def main() -> None:
    kmeans_path = ROOT / "results" / "summary_kmeans.csv"
    hdbscan_path = ROOT / "results" / "summary_hdbscan.csv"

    km = _load_csv(kmeans_path)
    hd = _load_csv(hdbscan_path)

    report = {
        "kmeans_rows": int(len(km)),
        "hdbscan_rows": int(len(hd)),
        "kmeans_path": str(kmeans_path),
        "hdbscan_path": str(hdbscan_path),
    }

    if not km.empty:
        report["kmeans_regimes"] = km["regime"].value_counts().to_dict() if "regime" in km else {}
    if not hd.empty:
        report["hdbscan_regimes"] = hd["regime"].value_counts().to_dict() if "regime" in hd else {}

    outdir = ROOT / "results" / "compare_old_motor"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    md = [
        "# Old Motor: KMeans vs HDBSCAN",
        "",
        f"- kmeans rows: {report.get('kmeans_rows')}",
        f"- hdbscan rows: {report.get('hdbscan_rows')}",
        "",
        "## Regime counts (kmeans)",
        json.dumps(report.get("kmeans_regimes", {}), indent=2),
        "",
        "## Regime counts (hdbscan)",
        json.dumps(report.get("hdbscan_regimes", {}), indent=2),
    ]
    (outdir / "report.md").write_text("\n".join(md), encoding="utf-8")
    print(f"[ok] wrote {outdir}/summary.json and report.md")


if __name__ == "__main__":
    main()
