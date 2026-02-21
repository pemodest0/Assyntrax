#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def _ts_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _safe_float(x: Any, default: float = float("nan")) -> float:
    try:
        y = float(x)
    except (TypeError, ValueError):
        return default
    return y if np.isfinite(y) else default


def _sector_canon(s: str) -> str:
    raw = str(s or "").strip().lower()
    raw = raw.replace("&", "and").replace("/", "_").replace("-", "_").replace(" ", "_")
    while "__" in raw:
        raw = raw.replace("__", "_")
    alias = {
        "healthcare": "health_care",
        "health_care": "health_care",
        "consumerstaples": "consumer_staples",
        "consumer_staples": "consumer_staples",
        "consumerdiscretionary": "consumer_discretionary",
        "consumer_discretionary": "consumer_discretionary",
        "realestate": "real_estate",
        "real_estate": "real_estate",
        "bond": "bonds_rates",
        "bonds": "bonds_rates",
        "bonds_rates": "bonds_rates",
        "financial": "financials",
        "finance": "financials",
        "tech": "technology",
        "material": "materials",
        "industrial": "industrials",
        "utility": "utilities",
    }
    if not raw:
        return "unknown"
    return alias.get(raw, raw)


def _safe_name(text: str) -> str:
    out = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in str(text).strip().lower())
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_") or "unknown"


def _load_asset_history(asset: str, assets_dir: Path, prices_dir: Path, sector: str) -> pd.DataFrame:
    rg_path = assets_dir / f"{asset}_daily_regimes.csv"
    px_path = prices_dir / f"{asset}.csv"
    if not rg_path.exists() or not px_path.exists():
        return pd.DataFrame()

    try:
        rg = pd.read_csv(rg_path)
        px = pd.read_csv(px_path)
    except (FileNotFoundError, pd.errors.EmptyDataError, pd.errors.ParserError, OSError, UnicodeDecodeError):
        return pd.DataFrame()

    if rg.empty or "regime" not in rg.columns or "confidence" not in rg.columns:
        return pd.DataFrame()
    if "date" not in px.columns:
        return pd.DataFrame()

    px["date"] = pd.to_datetime(px["date"], errors="coerce")
    px = px.dropna(subset=["date"]).sort_values("date")
    if px.empty:
        return pd.DataFrame()

    n_rg = int(len(rg))
    if n_rg <= 0 or len(px) < n_rg:
        return pd.DataFrame()

    dates = px["date"].iloc[-n_rg:].to_numpy()
    out = pd.DataFrame(
        {
            "date": dates,
            "asset": asset,
            "sector": sector,
            "regime": rg["regime"].astype(str).str.upper().to_numpy(),
            "confidence": pd.to_numeric(rg["confidence"], errors="coerce").clip(0.0, 1.0).to_numpy(),
        }
    )
    out = out.dropna(subset=["date", "confidence"])
    out["is_transition"] = (out["regime"] == "TRANSITION").astype(float)
    out["is_unstable"] = out["regime"].isin(["UNSTABLE", "NOISY"]).astype(float)
    out["is_alert"] = out["regime"].isin(["TRANSITION", "UNSTABLE", "NOISY"]).astype(float)
    return out


def _state_from_shares(share_transition: float, share_unstable: float, alert_share: float) -> str:
    if (share_unstable >= 0.15) or (alert_share >= 0.45):
        return "vermelho"
    if (share_transition >= 0.25) or (alert_share >= 0.30):
        return "amarelo"
    return "verde"


def _action_plan(level: str) -> str:
    if level == "vermelho":
        return "reduzir risco agora, revisar exposicao e hedge no mesmo dia"
    if level == "amarelo":
        return "modo cautela, reduzir concentracao e monitorar diario"
    return "manter plano normal e monitoramento semanal"


def run_sector_block(
    diagnostics_csv: Path,
    assets_dir: Path,
    prices_dir: Path,
    outdir: Path,
) -> dict[str, Any]:
    df = pd.read_csv(diagnostics_csv)
    df = df[df["in_target_470"].astype(bool)].copy()
    df = df.sort_values(["asset", "asof"]).drop_duplicates(subset=["asset"], keep="last").reset_index(drop=True)

    raw_sector = df["sector"].astype(str)
    empty_mask = raw_sector.fillna("").str.strip().eq("")
    df["sector_clean"] = raw_sector.apply(_sector_canon)
    rename_mask = (~empty_mask) & (df["sector_clean"] != raw_sector.str.strip().str.lower())

    audit = {
        "assets": int(len(df)),
        "unique_assets": int(df["asset"].nunique()),
        "empty_or_blank_sector_fixed": int(empty_mask.sum()),
        "renamed_sector_labels": int(rename_mask.sum()),
        "sectors_before": int(raw_sector.nunique()),
        "sectors_after": int(df["sector_clean"].nunique()),
    }
    (outdir / "sector_audit_summary.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")

    # Sector aggregate with core metrics
    for col in ["risk_score", "confidence", "quality"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["is_unstable_now"] = df["regime"].astype(str).str.upper().isin(["UNSTABLE", "NOISY"]).astype(float)

    base = (
        df.groupby("sector_clean", as_index=False)
        .agg(
            assets=("asset", "count"),
            risk_mean=("risk_score", "mean"),
            confidence_mean=("confidence", "mean"),
            unstable_pct=("is_unstable_now", "mean"),
            quality_mean=("quality", "mean"),
        )
        .sort_values(["risk_mean", "assets"], ascending=[False, False])
        .reset_index(drop=True)
    )

    # Historical weekly change by sector state
    panel_parts: list[pd.DataFrame] = []
    for _, row in df[["asset", "sector_clean"]].iterrows():
        part = _load_asset_history(str(row["asset"]), assets_dir=assets_dir, prices_dir=prices_dir, sector=str(row["sector_clean"]))
        if not part.empty:
            panel_parts.append(part)
    panel = pd.concat(panel_parts, ignore_index=True) if panel_parts else pd.DataFrame()
    panel.to_csv(outdir / "sector_asset_panel_daily.csv", index=False)

    if panel.empty:
        weekly = pd.DataFrame(columns=["sector_clean"])
        sector_daily = pd.DataFrame(columns=["date", "sector_clean"])
    else:
        sector_daily = (
            panel.groupby(["date", "sector"], as_index=False)
            .agg(
                assets=("asset", "count"),
                share_transition=("is_transition", "mean"),
                share_unstable=("is_unstable", "mean"),
                alert_share=("is_alert", "mean"),
                confidence_mean_day=("confidence", "mean"),
            )
            .rename(columns={"sector": "sector_clean"})
            .sort_values(["sector_clean", "date"])
            .reset_index(drop=True)
        )
        sector_daily["state"] = sector_daily.apply(
            lambda r: _state_from_shares(float(r["share_transition"]), float(r["share_unstable"]), float(r["alert_share"])),
            axis=1,
        )
        sector_daily["state_prev_5d"] = sector_daily.groupby("sector_clean")["state"].shift(5)
        sector_daily["alert_share_prev_5d"] = sector_daily.groupby("sector_clean")["alert_share"].shift(5)
        sector_daily["share_unstable_prev_5d"] = sector_daily.groupby("sector_clean")["share_unstable"].shift(5)
        sector_daily["delta_alert_share_5d"] = sector_daily["alert_share"] - sector_daily["alert_share_prev_5d"]
        sector_daily["delta_unstable_share_5d"] = sector_daily["share_unstable"] - sector_daily["share_unstable_prev_5d"]

        last_daily = (
            sector_daily.sort_values("date").groupby("sector_clean", as_index=False).tail(1)[
                [
                    "sector_clean",
                    "date",
                    "state",
                    "state_prev_5d",
                    "delta_alert_share_5d",
                    "delta_unstable_share_5d",
                    "alert_share",
                    "share_unstable",
                ]
            ]
            .copy()
        )
        last_daily["weekly_state_changed"] = (
            last_daily["state_prev_5d"].notna() & (last_daily["state"] != last_daily["state_prev_5d"])
        )
        weekly = last_daily.sort_values(["weekly_state_changed", "delta_alert_share_5d"], ascending=[False, False]).reset_index(drop=True)
        sector_daily.to_csv(outdir / "sector_state_daily.csv", index=False)

    reprocessed = base.merge(
        weekly[
            [
                "sector_clean",
                "date",
                "state",
                "state_prev_5d",
                "weekly_state_changed",
                "delta_alert_share_5d",
                "delta_unstable_share_5d",
                "alert_share",
                "share_unstable",
            ]
        ]
        if not weekly.empty
        else pd.DataFrame(columns=["sector_clean"]),
        on="sector_clean",
        how="left",
    )
    reprocessed["action_score"] = (
        0.45 * reprocessed["risk_mean"].fillna(0.0)
        + 0.30 * reprocessed["unstable_pct"].fillna(0.0)
        + 0.15 * reprocessed["delta_alert_share_5d"].fillna(0.0).clip(lower=0.0)
        + 0.10 * (1.0 - reprocessed["confidence_mean"].fillna(0.0))
    )
    reprocessed = reprocessed.sort_values(["action_score", "risk_mean"], ascending=[False, False]).reset_index(drop=True)
    reprocessed["alert_level"] = reprocessed["state"].fillna("verde")
    reprocessed["action_plan"] = reprocessed["alert_level"].apply(_action_plan)

    reprocessed.to_csv(outdir / "diagnostics_sectors_reprocessed.csv", index=False)
    if not weekly.empty:
        weekly.to_csv(outdir / "sector_weekly_state_change.csv", index=False)
    ranking = reprocessed[
        [
            "sector_clean",
            "assets",
            "alert_level",
            "action_score",
            "risk_mean",
            "confidence_mean",
            "unstable_pct",
            "weekly_state_changed",
            "delta_alert_share_5d",
            "action_plan",
        ]
    ].copy()
    ranking.to_csv(outdir / "sector_action_ranking.csv", index=False)
    ranking_main = ranking[ranking["assets"] >= 10].copy()
    ranking_niche = ranking[ranking["assets"] < 10].copy()
    if ranking_main.empty:
        ranking_main = ranking.copy()
    ranking_main.to_csv(outdir / "sector_action_ranking_main.csv", index=False)
    if not ranking_niche.empty:
        ranking_niche.to_csv(outdir / "sector_action_ranking_niche.csv", index=False)

    lines = []
    lines.append("Plano de acao por nivel de alerta de setor")
    lines.append("")
    lines.append("Vermelho:")
    lines.append("- reduzir risco no mesmo dia")
    lines.append("- revisar concentracao, beta e hedge")
    lines.append("- monitoramento intraday + fechamento")
    lines.append("")
    lines.append("Amarelo:")
    lines.append("- entrar em cautela")
    lines.append("- reduzir tamanho nas pontas mais frageis")
    lines.append("- monitoramento diario")
    lines.append("")
    lines.append("Verde:")
    lines.append("- manter risco base")
    lines.append("- monitoramento semanal")
    lines.append("")
    lines.append("Ranking setorial para acao (top 10, setores principais com >=10 ativos):")
    for _, r in ranking_main.head(10).iterrows():
        lines.append(
            f"- {r['sector_clean']}: nivel={r['alert_level']} | score={float(r['action_score']):.3f} | "
            f"risco={float(r['risk_mean']):.3f} | confianca={float(r['confidence_mean']):.3f} | "
            f"instaveis={float(r['unstable_pct']):.2f} | delta_semana={float(_safe_float(r['delta_alert_share_5d'],0.0)):.3f}"
        )
    if not ranking_niche.empty:
        lines.append("")
        lines.append("Setores de nicho (<10 ativos), tratar com cautela por baixa amostra:")
        for _, r in ranking_niche.iterrows():
            lines.append(
                f"- {r['sector_clean']}: ativos={int(r['assets'])} | nivel={r['alert_level']} | score={float(r['action_score']):.3f}"
            )
    (outdir / "sector_action_plan.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "audit": audit,
        "sectors": int(reprocessed.shape[0]),
        "top3_action": ranking_main["sector_clean"].head(3).tolist(),
        "out_files": {
            "reprocessed": str(outdir / "diagnostics_sectors_reprocessed.csv"),
            "weekly_change": str(outdir / "sector_weekly_state_change.csv"),
            "ranking": str(outdir / "sector_action_ranking.csv"),
            "ranking_main": str(outdir / "sector_action_ranking_main.csv"),
            "plan": str(outdir / "sector_action_plan.txt"),
        },
    }


def run_event_study_block(
    outdir: Path,
    tickers_file: Path,
    assets_dir: Path,
    prices_dir: Path,
    alert_policy: str,
    n_random: int,
) -> dict[str, Any]:
    event_root = outdir / "event_study"
    event_root.mkdir(parents=True, exist_ok=True)

    cmd = [
        "python3",
        "scripts/bench/event_study_validate.py",
        "--tickers-file",
        str(tickers_file.relative_to(ROOT)),
        "--assets-dir",
        str(assets_dir.relative_to(ROOT)),
        "--prices-dir",
        str(prices_dir.relative_to(ROOT)),
        "--lookbacks",
        "1,5,10,20",
        "--alert-policy",
        alert_policy,
        "--n-random",
        str(int(n_random)),
        "--skip-plots",
        "--out-root",
        str(event_root.relative_to(ROOT)),
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    event_out = Path(payload["outdir"])

    metrics = pd.read_csv(event_out / "metrics_summary.csv")
    event_defs = ["ret_tail", "drawdown20"]
    lookbacks = [1, 5, 10, 20]

    rows = []
    verdict_lines = []
    for ev in event_defs:
        for L in lookbacks:
            m = metrics[(metrics["event_def"] == ev) & (metrics["lookback_days"] == L) & (metrics["model"] == "motor")]
            b1 = metrics[(metrics["event_def"] == ev) & (metrics["lookback_days"] == L) & (metrics["model"] == "baseline_vol95")]
            b2 = metrics[(metrics["event_def"] == ev) & (metrics["lookback_days"] == L) & (metrics["model"] == "baseline_ret1")]
            if m.empty or b1.empty or b2.empty:
                continue
            rm = m.iloc[0]
            r1 = b1.iloc[0]
            r2 = b2.iloc[0]
            better_than_simple = (float(rm["recall"]) > float(r1["recall"])) and (float(rm["recall"]) > float(r2["recall"]))
            better_random = float(rm["p_vs_random_recall"]) < 0.05 if np.isfinite(float(rm["p_vs_random_recall"])) else False
            rows.append(
                {
                    "event_def": ev,
                    "lookback_days": int(L),
                    "motor_recall": float(rm["recall"]),
                    "motor_precision": float(rm["precision"]),
                    "motor_false_alarm_per_year": float(rm["false_alarm_per_year"]),
                    "motor_mean_lead_days": float(rm["mean_lead_days"]),
                    "motor_p_vs_random_recall": float(rm["p_vs_random_recall"]),
                    "baseline_vol95_recall": float(r1["recall"]),
                    "baseline_ret1_recall": float(r2["recall"]),
                    "better_than_simple_baselines": bool(better_than_simple),
                    "beats_random_p_lt_0_05": bool(better_random),
                }
            )

        # Verdict per event type using L=10 and L=20
        m10 = next((r for r in rows if r["event_def"] == ev and r["lookback_days"] == 10), None)
        m20 = next((r for r in rows if r["event_def"] == ev and r["lookback_days"] == 20), None)
        if m10 is None or m20 is None:
            verdict_lines.append(f"- {ev}: sem dados suficientes para conclusao.")
            continue
        cond_recall = (m10["motor_recall"] >= max(m10["baseline_vol95_recall"], m10["baseline_ret1_recall"])) and (
            m20["motor_recall"] >= max(m20["baseline_vol95_recall"], m20["baseline_ret1_recall"])
        )
        cond_false = (m10["motor_false_alarm_per_year"] <= 30.0) and (m20["motor_false_alarm_per_year"] <= 30.0)
        cond_random = m10["motor_p_vs_random_recall"] < 0.05 or m20["motor_p_vs_random_recall"] < 0.05
        min_recall_floor = (m10["motor_recall"] >= 0.10) or (m20["motor_recall"] >= 0.10)
        better_10 = m10["motor_recall"] > max(m10["baseline_vol95_recall"], m10["baseline_ret1_recall"])
        better_20 = m20["motor_recall"] > max(m20["baseline_vol95_recall"], m20["baseline_ret1_recall"])
        cond_recall = better_10 and better_20 and min_recall_floor
        cond_false = (m10["motor_false_alarm_per_year"] <= 30.0) and (m20["motor_false_alarm_per_year"] <= 30.0)
        cond_random = (m10["motor_p_vs_random_recall"] < 0.05) or (m20["motor_p_vs_random_recall"] < 0.05)
        cond_moderate = (
            (m10["motor_recall"] >= max(m10["baseline_vol95_recall"], m10["baseline_ret1_recall"]))
            and (m20["motor_recall"] >= max(m20["baseline_vol95_recall"], m20["baseline_ret1_recall"]))
            and min_recall_floor
            and cond_false
            and ((m10["motor_p_vs_random_recall"] < 0.20) or (m20["motor_p_vs_random_recall"] < 0.20))
        )
        if cond_recall and cond_false and cond_random:
            verdict_lines.append(f"- {ev}: ANTECIPA (evidencia forte no protocolo atual).")
        elif cond_moderate:
            verdict_lines.append(f"- {ev}: tem sinal operacional de antecipacao, mas SEM evidencia estatistica forte.")
        else:
            verdict_lines.append(f"- {ev}: NAO ANTECIPA com evidencia forte neste protocolo.")

    summary = pd.DataFrame(rows).sort_values(["event_def", "lookback_days"]).reset_index(drop=True)
    summary.to_csv(outdir / "crisis_event_metrics_summary.csv", index=False)

    lines = []
    lines.append("Teste de crises historicas - conclusao final")
    lines.append(f"out_event_study: {event_out}")
    lines.append("janelas: 1, 5, 10, 20 dias")
    lines.append("eventos: retorno extremo (ret_tail) e queda acumulada (drawdown20)")
    lines.append("comparacoes: baseline_vol95, baseline_ret1, baseline aleatorio")
    lines.append("")
    lines.append("Resumo por evento:")
    lines.extend(verdict_lines)
    lines.append("")
    lines.append("Tabela resumida:")
    for _, r in summary.iterrows():
        lines.append(
            f"- {r['event_def']} L{int(r['lookback_days'])}: recall={r['motor_recall']:.3f} | "
            f"precisao={r['motor_precision']:.3f} | falso_alarme/ano={r['motor_false_alarm_per_year']:.3f} | "
            f"lead={r['motor_mean_lead_days']:.2f} | p_random={r['motor_p_vs_random_recall']:.4f}"
        )
    (outdir / "report_crisis_antecipa_ou_nao.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return {
        "event_outdir": str(event_out),
        "summary_csv": str(outdir / "crisis_event_metrics_summary.csv"),
        "final_report": str(outdir / "report_crisis_antecipa_ou_nao.txt"),
        "n_rows_summary": int(summary.shape[0]),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Setor audit + crise event study suite.")
    ap.add_argument("--diagnostics-csv", type=str, default="results/latest_graph_universe470_batch/diagnostics_assets_daily.csv")
    ap.add_argument("--assets-dir", type=str, default="results/latest_graph_universe470_batch/assets")
    ap.add_argument("--prices-dir", type=str, default="data/raw/finance/yfinance_daily")
    ap.add_argument("--tickers-file", type=str, default="results/universe_470/tickers_470.txt")
    ap.add_argument("--alert-policy", type=str, default="regime_guarded")
    ap.add_argument("--n-random", type=int, default=1000)
    ap.add_argument("--out-root", type=str, default="results/sector_crisis_suite")
    args = ap.parse_args()

    outdir = ROOT / args.out_root / _ts_id()
    outdir.mkdir(parents=True, exist_ok=True)

    sector_info = run_sector_block(
        diagnostics_csv=ROOT / args.diagnostics_csv,
        assets_dir=ROOT / args.assets_dir,
        prices_dir=ROOT / args.prices_dir,
        outdir=outdir,
    )
    crisis_info = run_event_study_block(
        outdir=outdir,
        tickers_file=ROOT / args.tickers_file,
        assets_dir=ROOT / args.assets_dir,
        prices_dir=ROOT / args.prices_dir,
        alert_policy=str(args.alert_policy),
        n_random=int(args.n_random),
    )

    status = {
        "status": "ok",
        "outdir": str(outdir),
        "sector": sector_info,
        "crisis": crisis_info,
    }
    (outdir / "status.json").write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(status, ensure_ascii=False))


if __name__ == "__main__":
    main()
