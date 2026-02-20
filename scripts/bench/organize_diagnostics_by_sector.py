#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def _safe_name(text: str) -> str:
    out = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in str(text).strip().lower())
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_") or "unknown"


def main() -> None:
    ap = argparse.ArgumentParser(description="Organize diagnostics by sector into per-sector files.")
    ap.add_argument("--diagnostics-csv", type=str, default="results/latest_graph_universe470_batch/diagnostics_assets_daily.csv")
    ap.add_argument("--outdir", type=str, default="results/latest_graph_universe470_batch/sector_pack")
    args = ap.parse_args()

    diagnostics_csv = ROOT / args.diagnostics_csv
    outdir = ROOT / args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    if not diagnostics_csv.exists():
        raise SystemExit(f"missing diagnostics csv: {diagnostics_csv}")

    df = pd.read_csv(diagnostics_csv)
    if df.empty:
        raise SystemExit("diagnostics csv is empty")

    for col in ["confidence", "quality", "risk_score", "stay_prob", "escape_prob", "alerts_n"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df["sector"] = df["sector"].astype(str).fillna("unknown")
    df["regime"] = df["regime"].astype(str).fillna("UNKNOWN")
    df["behavior"] = df["behavior"].astype(str).fillna("unknown")

    summary = (
        df.groupby("sector", as_index=False)
        .agg(
            n_assets=("asset", "count"),
            confidence_mean=("confidence", "mean"),
            quality_mean=("quality", "mean"),
            risk_score_mean=("risk_score", "mean"),
            stay_prob_mean=("stay_prob", "mean"),
            escape_prob_mean=("escape_prob", "mean"),
            alerts_mean=("alerts_n", "mean"),
        )
    )
    for label in ["STABLE", "TRANSITION", "UNSTABLE", "NOISY"]:
        by = df.groupby("sector")["regime"].apply(lambda x: float((x == label).mean())).rename(f"share_{label.lower()}")
        summary = summary.merge(by, on="sector", how="left")
    for b in ["estavel", "transicao", "fragil"]:
        by = df.groupby("sector")["behavior"].apply(lambda x: float((x == b).mean())).rename(f"share_behavior_{b}")
        summary = summary.merge(by, on="sector", how="left")
    summary = summary.sort_values(["risk_score_mean", "n_assets"], ascending=[False, False]).reset_index(drop=True)
    summary.to_csv(outdir / "sector_overview.csv", index=False)

    report_lines: list[str] = []
    report_lines.append("Pacote Setorial - Diagnostico de Ativos")
    report_lines.append(f"total_ativos: {int(df.shape[0])}")
    report_lines.append(f"setores: {int(summary.shape[0])}")
    report_lines.append("")
    report_lines.append("Setores por risco medio:")
    for _, r in summary.iterrows():
        report_lines.append(
            f"- {r['sector']}: n={int(r['n_assets'])}, risk={float(r['risk_score_mean']):.3f}, "
            f"conf={float(r['confidence_mean']):.3f}, stable={float(r.get('share_stable', 0.0)):.2f}, "
            f"transition={float(r.get('share_transition', 0.0)):.2f}, unstable={float(r.get('share_unstable', 0.0)):.2f}"
        )
    report_lines.append("")

    per_sector_dir = outdir / "sectors"
    per_sector_dir.mkdir(parents=True, exist_ok=True)
    for old in per_sector_dir.glob("*_assets.csv"):
        old.unlink(missing_ok=True)
    for sector, sdf in df.groupby("sector"):
        sname = _safe_name(sector)
        sorted_sector = sdf.sort_values(["risk_score", "confidence"], ascending=[False, True]).reset_index(drop=True)
        sorted_sector.to_csv(per_sector_dir / f"{sname}_assets.csv", index=False)

        top_fragil = sorted_sector.head(5)
        top_estavel = (
            sdf.sort_values(["risk_score", "confidence"], ascending=[True, False]).head(5).reset_index(drop=True)
        )
        report_lines.append(f"Setor: {sector}")
        report_lines.append("Top frageis:")
        for _, r in top_fragil.iterrows():
            report_lines.append(
                f"- {r['asset']}: regime={r['regime']}, risk={float(r['risk_score']):.3f}, conf={float(r['confidence']):.3f}"
            )
        report_lines.append("Top estaveis:")
        for _, r in top_estavel.iterrows():
            report_lines.append(
                f"- {r['asset']}: regime={r['regime']}, risk={float(r['risk_score']):.3f}, conf={float(r['confidence']):.3f}"
            )
        report_lines.append("")

    (outdir / "sector_report.txt").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(
        {
            "status": "ok",
            "assets": int(df.shape[0]),
            "sectors": int(summary.shape[0]),
            "overview_csv": str(outdir / "sector_overview.csv"),
            "sector_report": str(outdir / "sector_report.txt"),
            "sectors_dir": str(per_sector_dir),
        }
    )


if __name__ == "__main__":
    main()
