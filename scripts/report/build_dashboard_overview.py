#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


def load_asset_groups(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["asset", "group"])
    df = pd.read_csv(path)
    if "asset" not in df.columns or "group" not in df.columns:
        return pd.DataFrame(columns=["asset", "group"])
    return df


def parse_risk_report(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["ticker", "model", "roc_auc", "f1", "bal_acc"])
    text = path.read_text(encoding="utf-8")
    rows = []
    in_table = False
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("| ticker | model |"):
            in_table = True
            continue
        if not in_table or not line.startswith("|"):
            continue
        if line.startswith("| ---"):
            continue
        parts = [p.strip() for p in line.strip("|").split("|")]
        if len(parts) < 5:
            continue
        rows.append(
            {
                "ticker": parts[0],
                "model": parts[1],
                "roc_auc": float(parts[2]),
                "f1": float(parts[3]),
                "bal_acc": float(parts[4]),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build dashboard overview artifacts.")
    parser.add_argument("--walkforward", default="results/finance_walkforward_all/walkforward_results.csv")
    parser.add_argument("--risk-report", default="results/finance_risk_all/report.md")
    parser.add_argument("--asset-groups", default="data/asset_groups.csv")
    parser.add_argument("--outdir", default="results/dashboard")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    walk_path = Path(args.walkforward)
    wf = pd.read_csv(walk_path) if walk_path.exists() else pd.DataFrame()
    groups = load_asset_groups(Path(args.asset_groups))
    risk = parse_risk_report(Path(args.risk_report))

    if not wf.empty:
        wf["warnings"] = wf["warnings"].fillna("")
        wf["has_regime_instavel"] = wf["warnings"].str.contains("REGIME_INSTAVEL")
        wf["has_dir_fraca"] = wf["warnings"].str.contains("DIRECAO_FRACA")

    # Per-asset aggregates
    asset_stats = (
        wf.groupby("ticker").agg(
            mean_mase=("mase", "mean"),
            mean_dir_acc=("dir_acc", "mean"),
            pct_dir_acc_gt_052=("dir_acc", lambda x: float(np.mean(x > 0.52))),
            pct_mase_lt_1=("mase", lambda x: float(np.mean(x < 1))),
            mean_confidence=("confidence_score", "mean"),
            pct_operar=("action", lambda x: float(np.mean(x == "OPERAR"))),
        )
        if not wf.empty
        else pd.DataFrame()
    )
    asset_stats = asset_stats.reset_index().rename(columns={"ticker": "asset"})

    # Join groups
    if not asset_stats.empty:
        asset_stats = asset_stats.merge(groups, on="asset", how="left")

    # Risk metrics per asset (best model by roc_auc)
    risk_best = pd.DataFrame()
    if not risk.empty:
        risk_best = (
            risk.sort_values("roc_auc", ascending=False)
            .groupby("ticker")
            .first()
            .reset_index()
            .rename(columns={"ticker": "asset"})
        )
        risk_best = risk_best[["asset", "model", "roc_auc", "f1", "bal_acc"]]

    # Group ranking table
    group_rank = pd.DataFrame()
    if not asset_stats.empty:
        group_rank = (
            asset_stats.groupby("group").agg(
                mean_mase=("mean_mase", "mean"),
                mean_dir_acc=("mean_dir_acc", "mean"),
                pct_dir_acc_gt_052=("pct_dir_acc_gt_052", "mean"),
                pct_mase_lt_1=("pct_mase_lt_1", "mean"),
                mean_confidence=("mean_confidence", "mean"),
                n_assets=("asset", "count"),
            )
            .reset_index()
        )
        if not risk_best.empty:
            risk_join = risk_best.merge(groups, on="asset", how="left")
            risk_group = (
                risk_join.groupby("group")
                .agg(mean_risk_auc=("roc_auc", "mean"))
                .reset_index()
            )
            group_rank = group_rank.merge(risk_group, on="group", how="left")

    # Top/bottom assets
    top_bottom = pd.DataFrame()
    if not asset_stats.empty:
        top_mase = asset_stats.sort_values("mean_mase").head(10)
        bottom_mase = asset_stats.sort_values("mean_mase", ascending=False).head(10)
        top_dir = asset_stats.sort_values("mean_dir_acc", ascending=False).head(10)
        bottom_dir = asset_stats.sort_values("mean_dir_acc").head(10)
        top_bottom = pd.concat(
            [
                top_mase.assign(rank_type="best_mase"),
                bottom_mase.assign(rank_type="worst_mase"),
                top_dir.assign(rank_type="best_diracc"),
                bottom_dir.assign(rank_type="worst_diracc"),
            ],
            ignore_index=True,
        )

    # Summary cards
    summary_cards = {}
    if not wf.empty:
        summary_cards = {
            "n_rows": int(len(wf)),
            "n_assets": int(wf["ticker"].nunique()),
            "pct_rows_regime_instavel": float(wf["has_regime_instavel"].mean()),
            "pct_rows_direcao_fraca": float(wf["has_dir_fraca"].mean()),
            "pct_assets_dir_acc_gt_052": float(asset_stats["pct_dir_acc_gt_052"].mean()) if not asset_stats.empty else 0.0,
            "pct_assets_mase_lt_1": float(asset_stats["pct_mase_lt_1"].mean()) if not asset_stats.empty else 0.0,
        }

    # Write outputs
    if not asset_stats.empty:
        asset_stats.to_csv(outdir / "assets_summary.csv", index=False)
    if not group_rank.empty:
        group_rank.to_csv(outdir / "group_rankings.csv", index=False)
    if not top_bottom.empty:
        top_bottom.to_csv(outdir / "assets_top_bottom.csv", index=False)
    if not risk_best.empty:
        risk_best.to_csv(outdir / "risk_best_models.csv", index=False)

    overview = {
        "summary_cards": summary_cards,
        "groups": group_rank.to_dict(orient="records") if not group_rank.empty else [],
        "assets": asset_stats.to_dict(orient="records") if not asset_stats.empty else [],
        "risk_best_models": risk_best.to_dict(orient="records") if not risk_best.empty else [],
    }
    (outdir / "overview.json").write_text(json.dumps(overview, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
