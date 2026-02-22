#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
MOTOR_ROOT = ROOT / "results" / "motor_470_program"
OUT_ROOT = ROOT / "results" / "followup_123"


@dataclass
class AlertMetrics:
    recall: float
    precision: float
    false_alarm_per_year: float
    mean_lead_days: float
    n_events: int
    n_alert_episodes: int


def _ts_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _latest_dir(root: Path) -> Path:
    dirs = sorted([p for p in root.iterdir() if p.is_dir()])
    if not dirs:
        raise FileNotFoundError(f"No folders under {root}")
    return dirs[-1]


def _safe_float(x: Any, default: float = float("nan")) -> float:
    try:
        y = float(x)
    except (TypeError, ValueError):
        return default
    return y if np.isfinite(y) else default


def _zscore(s: pd.Series) -> pd.Series:
    x = pd.to_numeric(s, errors="coerce")
    mu = float(x.mean(skipna=True))
    sd = float(x.std(ddof=0, skipna=True))
    if (not np.isfinite(sd)) or sd <= 1e-12:
        return pd.Series(np.zeros(len(x), dtype=float), index=x.index)
    return ((x - mu) / sd).replace([np.inf, -np.inf], np.nan).fillna(0.0)


def _apply_hysteresis(labels: list[str], min_persist: int) -> list[str]:
    if not labels:
        return []
    k = int(max(1, min_persist))
    current = labels[0]
    pending = ""
    cnt = 0
    out = [current]
    for raw in labels[1:]:
        if raw == current:
            pending = ""
            cnt = 0
            out.append(current)
            continue
        if raw == pending:
            cnt += 1
        else:
            pending = raw
            cnt = 1
        if cnt >= k:
            current = pending
            pending = ""
            cnt = 0
        out.append(current)
    return out


def _build_market_events(
    returns_wide_core: pd.DataFrame,
    dd_threshold: float = -0.08,
    cooldown_days: int = 20,
) -> tuple[pd.Series, list[pd.Timestamp]]:
    d = returns_wide_core.copy()
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d = d.dropna(subset=["date"]).sort_values("date")
    cols = [c for c in d.columns if c != "date"]
    mkt_ret = d[cols].apply(pd.to_numeric, errors="coerce").mean(axis=1, skipna=True)
    price = 100.0 * np.exp(mkt_ret.fillna(0.0).cumsum())
    dd20 = price / price.rolling(20, min_periods=20).max() - 1.0
    d["mkt_ret"] = mkt_ret
    d["dd20"] = dd20
    mask = d["dd20"] <= float(dd_threshold)
    idx = d.index[mask].to_list()
    dates = d.loc[mask, "date"].to_list()
    deduped: list[pd.Timestamp] = []
    last_i: int | None = None
    for dt, i in zip(dates, idx):
        if last_i is None or (int(i) - int(last_i)) > int(cooldown_days):
            deduped.append(pd.Timestamp(dt))
            last_i = int(i)
    return d.set_index("date")["mkt_ret"], deduped


def _eval_alerts(
    dates: pd.Series,
    alert: pd.Series,
    event_dates: list[pd.Timestamp],
    lookback_days: int,
    assoc_horizon_days: int = 20,
) -> AlertMetrics:
    dts = pd.to_datetime(pd.Series(dates)).reset_index(drop=True)
    s_alert = pd.Series(alert.to_numpy(dtype=bool)).reset_index(drop=True)
    d2i = {d: i for i, d in enumerate(dts)}
    ev_idx = sorted([d2i[d] for d in pd.to_datetime(pd.Series(event_dates)).to_list() if d in d2i])

    detected = 0
    lead_days: list[int] = []
    for e in ev_idx:
        lo = max(0, e - int(lookback_days))
        hi = e - 1
        if hi >= lo:
            w = s_alert.iloc[lo : hi + 1]
            if bool(w.any()):
                detected += 1
                first_rel = int(np.argmax(w.to_numpy(dtype=bool)))
                first_idx = lo + first_rel
                lead_days.append(int(e - first_idx))

    starts = s_alert.to_numpy(dtype=bool) & (~s_alert.shift(1, fill_value=False).to_numpy(dtype=bool))
    ep_idx = np.where(starts)[0]
    good = 0
    for a in ep_idx:
        has_future_event = any((ev >= a + 1) and (ev <= a + int(assoc_horizon_days)) for ev in ev_idx)
        if has_future_event:
            good += 1
    n_ep = int(len(ep_idx))
    n_false = int(max(0, n_ep - good))
    years = max(1e-9, len(dts) / 252.0)
    return AlertMetrics(
        recall=float(detected / len(ev_idx)) if ev_idx else float("nan"),
        precision=float(good / n_ep) if n_ep > 0 else float("nan"),
        false_alarm_per_year=float(n_false / years),
        mean_lead_days=float(np.mean(lead_days)) if lead_days else float("nan"),
        n_events=int(len(ev_idx)),
        n_alert_episodes=n_ep,
    )


def _classify_with_params(
    ts: pd.DataFrame,
    *,
    p_lo_q: float,
    p_hi_q: float,
    d_lo_q: float,
    d_hi_q: float,
    trans_q: float,
    hysteresis_days: int,
    w_dp1: float,
    w_ddeff: float,
    w_overlap: float,
) -> pd.DataFrame:
    d = ts.copy().sort_values("date")
    d["dp1_5"] = d["p1"].diff(5)
    d["ddeff_5"] = d["deff"].diff(5)
    d["ov_instability"] = 1.0 - pd.to_numeric(d.get("eigvec_overlap_1d"), errors="coerce")
    z_dp1 = _zscore(d["dp1_5"].abs())
    z_ddeff = _zscore(d["ddeff_5"].abs())
    z_ov = _zscore(d["ov_instability"])
    d["transition_score"] = float(w_dp1) * z_dp1 + float(w_ddeff) * z_ddeff + float(w_overlap) * z_ov

    p_lo = float(d["p1"].quantile(float(p_lo_q)))
    p_hi = float(d["p1"].quantile(float(p_hi_q)))
    de_lo = float(d["deff"].quantile(float(d_lo_q)))
    de_hi = float(d["deff"].quantile(float(d_hi_q)))
    tr_thr = float(d["transition_score"].quantile(float(trans_q)))

    raw: list[str] = []
    for _, r in d.iterrows():
        p1 = float(r["p1"])
        de = float(r["deff"])
        tr = float(r["transition_score"])
        if (p1 >= p_hi) and (de <= de_lo):
            raw.append("stress")
        elif (p1 <= p_lo) and (de >= de_hi):
            raw.append("dispersion")
        elif tr >= tr_thr:
            raw.append("transition")
        else:
            raw.append("stable")
    d["regime_raw"] = raw
    d["regime"] = _apply_hysteresis(raw, int(max(1, hysteresis_days)))
    d["alert"] = d["regime"].isin(["stress", "transition"])
    return d


def _run_lengths(labels: pd.Series) -> pd.Series:
    s = labels.astype(str).reset_index(drop=True)
    if s.empty:
        return pd.Series(dtype=float)
    grp = (s != s.shift(1)).cumsum()
    return grp.groupby(grp).size()


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    motor_dir = _latest_dir(MOTOR_ROOT)
    outdir = OUT_ROOT / _ts_id()
    outdir.mkdir(parents=True, exist_ok=True)

    status = json.loads((motor_dir / "status.json").read_text(encoding="utf-8"))
    policy = json.loads((motor_dir / "motor_policy_final.json").read_text(encoding="utf-8"))
    lab_run = Path(status["lab_run"])
    uni_dir = Path(status["universe_dir"])

    # 1) Continuous conservative policy test
    ts_raw = pd.read_csv(lab_run / "macro_timeseries_T120.csv")
    ts_raw["date"] = pd.to_datetime(ts_raw["date"], errors="coerce")
    ts_raw = ts_raw.dropna(subset=["date"]).sort_values("date")
    valid_mask = ~ts_raw["insufficient_universe"].astype(bool)
    ts = ts_raw[valid_mask].copy()

    ov = pd.read_csv(motor_dir / "motor_eigvec_overlap.csv")
    ov = ov[ov["window"] == 120][["date", "eigvec_overlap_1d"]].copy()
    ov["date"] = pd.to_datetime(ov["date"], errors="coerce")
    ts = ts.merge(ov, on="date", how="left")
    ts["eigvec_overlap_1d"] = ts["eigvec_overlap_1d"].fillna(ts["eigvec_overlap_1d"].median())

    returns_wide = pd.read_csv(lab_run / "returns_wide_core.csv")
    mkt_ret, event_dates = _build_market_events(returns_wide)
    ts = ts.merge(mkt_ret.rename("mkt_ret").reset_index().rename(columns={"index": "date"}), on="date", how="left")

    p = policy["recommended_params"]
    pol = _classify_with_params(
        ts,
        p_lo_q=float(p["q_lo"]),
        p_hi_q=float(p["q_hi"]),
        d_lo_q=float(p["q_lo"]),
        d_hi_q=float(p["q_hi"]),
        trans_q=float(p["q_transition"]),
        hysteresis_days=int(p["hysteresis_days"]),
        w_dp1=float(p["w_dp1"]),
        w_ddeff=float(p["w_ddeff"]),
        w_overlap=float(p["w_overlap"]),
    )
    pol["event_dd20"] = pol["date"].isin(set(pd.to_datetime(pd.Series(event_dates))))
    pol["month"] = pol["date"].dt.to_period("M").astype(str)
    pol.to_csv(outdir / "policy_conservative_continuous_daily.csv", index=False)

    metrics = {}
    for l in [5, 10, 20]:
        ev = _eval_alerts(pol["date"], pol["alert"], event_dates, lookback_days=l, assoc_horizon_days=20)
        metrics[f"l{l}"] = {
            "recall": ev.recall,
            "precision": ev.precision,
            "false_alarm_per_year": ev.false_alarm_per_year,
            "mean_lead_days": ev.mean_lead_days,
            "events": ev.n_events,
            "alert_episodes": ev.n_alert_episodes,
        }

    regime_shares = pol["regime"].value_counts(normalize=True).to_dict()
    recent = {}
    for days in [30, 60, 90]:
        tail = pol.tail(days)
        recent[str(days)] = {
            "alert_share": float(tail["alert"].mean()) if len(tail) else float("nan"),
            "regime_mode": str(tail["regime"].mode().iloc[0]) if len(tail) else "",
        }
    run_lengths = _run_lengths(pol["regime"])
    monthly = (
        pol.groupby("month", as_index=False)
        .agg(alert_share=("alert", "mean"), stress_days=("regime", lambda x: int((x == "stress").sum())), transition_days=("regime", lambda x: int((x == "transition").sum())))
        .sort_values("month")
    )
    monthly.to_csv(outdir / "policy_conservative_monthly_stability.csv", index=False)

    stability = {
        "source_motor_run": str(motor_dir),
        "lab_run": str(lab_run),
        "policy_mode": policy.get("recommended_mode", "conservative"),
        "macro_total_days": int(len(ts_raw)),
        "macro_valid_days": int(valid_mask.sum()),
        "macro_invalid_days": int((~valid_mask).sum()),
        "macro_valid_end_date": ts["date"].max().date().isoformat(),
        "macro_last_date_in_file": ts_raw["date"].max().date().isoformat(),
        "sample_days": int(len(pol)),
        "first_date": pol["date"].min().date().isoformat(),
        "last_date": pol["date"].max().date().isoformat(),
        "regime_shares": {k: float(v) for k, v in regime_shares.items()},
        "total_alert_days": int(pol["alert"].sum()),
        "alert_share_total": float(pol["alert"].mean()),
        "regime_switches": int((pol["regime"] != pol["regime"].shift(1)).sum() - 1),
        "avg_regime_run_days": float(run_lengths.mean()) if len(run_lengths) else float("nan"),
        "recent_windows": recent,
        "event_metrics": metrics,
    }
    _save_json(outdir / "policy_conservative_stability_summary.json", stability)

    lines = []
    lines.append("Teste continuo da politica conservadora")
    lines.append(f"Amostra: {stability['first_date']} ate {stability['last_date']} ({stability['sample_days']} dias)")
    lines.append(
        f"Cobertura macro valida: {stability['macro_valid_days']}/{stability['macro_total_days']} dias | "
        f"ultimo dia valido={stability['macro_valid_end_date']} | ultimo dia em arquivo={stability['macro_last_date_in_file']}"
    )
    lines.append(f"Alertas: {stability['total_alert_days']} dias ({stability['alert_share_total']:.3f})")
    lines.append(f"Trocas de estado: {stability['regime_switches']} | corrida media por estado: {stability['avg_regime_run_days']:.2f} dias")
    lines.append(
        "Regimes: "
        + ", ".join([f"{k}={float(v):.3f}" for k, v in sorted(stability["regime_shares"].items())])
    )
    for k in ["l5", "l10", "l20"]:
        m = stability["event_metrics"][k]
        lines.append(
            f"{k}: recall={m['recall']:.3f} | precision={m['precision']:.3f} | falso_alarme_ano={m['false_alarm_per_year']:.3f} | antecedencia={m['mean_lead_days']:.2f}"
        )
    lines.append("Recentes:")
    for w in ["30", "60", "90"]:
        r = stability["recent_windows"][w]
        lines.append(f"- {w} dias: alerta={r['alert_share']:.3f} | estado dominante={r['regime_mode']}")
    (outdir / "report_step1_policy_continuous.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 2) Weak signal triage
    weak = pd.read_csv(motor_dir / "universe_weak_signal_assets.csv")
    enriched = pd.read_csv(motor_dir / "universe_asset_diagnostics_enriched.csv")
    consistency = pd.read_csv(motor_dir / "universe_series_consistency.csv")
    has_issue = set(consistency.loc[consistency["has_data_issue"] > 0, "asset"].astype(str).tolist())

    triage = weak.copy()
    triage["asset"] = triage["asset"].astype(str)
    triage["has_data_issue"] = triage["asset"].isin(has_issue)

    def classify_reason(r: pd.Series) -> str:
        if bool(r["has_data_issue"]):
            return "dados"
        regime = str(r.get("regime", "")).upper()
        risk = _safe_float(r.get("risk_score"), 0.0)
        conf = _safe_float(r.get("confidence"), 0.0)
        sw90 = int(_safe_float(r.get("switches_90d"), 0))
        if (risk >= 0.78) and (regime in {"UNSTABLE", "NOISY", "TRANSITION"}):
            return "mercado_estrutural_forte"
        if (risk >= 0.65) and (sw90 >= 5):
            return "mercado_estrutural_moderado"
        if (conf < 0.25) and (risk < 0.65):
            return "sinal_fraco_modelo"
        return "misto_revisar"

    triage["reason"] = triage.apply(classify_reason, axis=1)
    triage["priority_score"] = (
        0.50 * pd.to_numeric(triage["risk_score"], errors="coerce").fillna(0.0)
        + 0.30 * (1.0 - pd.to_numeric(triage["confidence"], errors="coerce").fillna(0.0))
        + 0.20 * np.minimum(1.0, pd.to_numeric(triage["switches_90d"], errors="coerce").fillna(0.0) / 12.0)
    )

    action_map = {
        "dados": "revisar arquivo e pipeline de serie",
        "mercado_estrutural_forte": "manter em monitoramento diario e reduzir exposicao",
        "mercado_estrutural_moderado": "monitorar semanal e validar sensibilidade",
        "sinal_fraco_modelo": "recalibrar pesos e limiares locais",
        "misto_revisar": "revisao manual curta com time",
    }
    triage["recommended_action"] = triage["reason"].map(action_map).fillna("revisar")
    triage = triage.sort_values(["priority_score", "risk_score"], ascending=[False, False]).reset_index(drop=True)
    triage.to_csv(outdir / "weak_signal_triage.csv", index=False)

    reason_counts = triage["reason"].value_counts().to_dict()
    weak_sector = triage["sector"].fillna("unknown").value_counts().to_dict()
    top_20 = triage.head(20)[["asset", "sector", "regime", "risk_score", "confidence", "switches_90d", "reason"]]
    top_20.to_csv(outdir / "weak_signal_top20_priority.csv", index=False)

    weak_summary = {
        "weak_total": int(len(triage)),
        "reason_counts": {k: int(v) for k, v in reason_counts.items()},
        "sector_counts": {k: int(v) for k, v in weak_sector.items()},
        "data_issue_assets": int(triage["has_data_issue"].sum()),
    }
    _save_json(outdir / "weak_signal_summary.json", weak_summary)

    lines = []
    lines.append("Triagem dos 123 sinais fracos")
    lines.append(f"Total: {weak_summary['weak_total']}")
    lines.append(f"Com problema de dados: {weak_summary['data_issue_assets']}")
    lines.append("Quebras por motivo:")
    for k, v in weak_summary["reason_counts"].items():
        lines.append(f"- {k}: {v}")
    lines.append("Top 10 setores com mais sinal fraco:")
    for k, v in list(weak_summary["sector_counts"].items())[:10]:
        lines.append(f"- {k}: {v}")
    (outdir / "report_step2_weak_signal.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # 3) Sector diagnosis + commercial summary
    triage_assets = set(triage["asset"].astype(str).tolist())
    sector = enriched.copy()
    sector["asset"] = sector["asset"].astype(str)
    sector["is_weak_signal"] = sector["asset"].isin(triage_assets)
    sector["is_unstable"] = sector["regime"].isin(["UNSTABLE", "NOISY"])
    sector["is_transition"] = sector["regime"] == "TRANSITION"
    sector["is_stable"] = sector["regime"] == "STABLE"

    sec = (
        sector.groupby("sector", as_index=False)
        .agg(
            assets=("asset", "count"),
            weak_signal_assets=("is_weak_signal", "sum"),
            stable_assets=("is_stable", "sum"),
            transition_assets=("is_transition", "sum"),
            unstable_assets=("is_unstable", "sum"),
            confidence_mean=("confidence", "mean"),
            risk_mean=("risk_score", "mean"),
            switches90_mean=("switches_90d", "mean"),
            unstable_share90_mean=("unstable_share_90d", "mean"),
            sensitivity_mean=("sensitivity_score", "mean"),
            stability_mean=("stability_score", "mean"),
        )
        .sort_values(["risk_mean", "weak_signal_assets"], ascending=[False, False])
    )
    sec["transition_share"] = sec["transition_assets"] / sec["assets"]
    sec["unstable_share"] = sec["unstable_assets"] / sec["assets"]
    sec["weak_share"] = sec["weak_signal_assets"] / sec["assets"]

    def sector_bucket(r: pd.Series) -> str:
        if (float(r["unstable_share"]) >= 0.15) or (float(r["risk_mean"]) >= 0.65):
            return "instavel"
        if (float(r["transition_share"]) >= 0.25) or (float(r["risk_mean"]) >= 0.50):
            return "transicao"
        return "estavel"

    def sector_color(b: str) -> str:
        if b == "instavel":
            return "vermelho"
        if b == "transicao":
            return "amarelo"
        return "verde"

    sec["sector_regime"] = sec.apply(sector_bucket, axis=1)
    sec["status_cor"] = sec["sector_regime"].apply(sector_color)
    sec.to_csv(outdir / "sector_diagnostic_table.csv", index=False)

    sec_main = sec[sec["assets"] >= 10].copy()
    if sec_main.empty:
        sec_main = sec.copy()
    sec_niche = sec[sec["assets"] < 10].copy()

    top_risk_sector = sec_main.sort_values(["risk_mean", "weak_share"], ascending=[False, False]).head(5)
    top_stable_sector = sec_main.sort_values(["stability_mean", "confidence_mean"], ascending=[False, False]).head(5)
    top_risk_sector.to_csv(outdir / "sector_top5_risk.csv", index=False)
    top_stable_sector.to_csv(outdir / "sector_top5_stable.csv", index=False)
    if not sec_niche.empty:
        sec_niche.sort_values(["risk_mean", "weak_share"], ascending=[False, False]).to_csv(outdir / "sector_niche_assets_lt10.csv", index=False)

    lines = []
    lines.append("Diagnostico final por setor")
    lines.append(f"Setores avaliados: {int(len(sec))}")
    lines.append("")
    lines.append("Setores mais fragilizados:")
    for _, r in top_risk_sector.iterrows():
        lines.append(
            f"- {r['sector']}: cor={r['status_cor']} | risco={float(r['risk_mean']):.3f} | weak={int(r['weak_signal_assets'])}/{int(r['assets'])} | transicao={float(r['transition_share']):.2f} | instavel={float(r['unstable_share']):.2f}"
        )
    lines.append("")
    lines.append("Setores mais estaveis:")
    for _, r in top_stable_sector.iterrows():
        lines.append(
            f"- {r['sector']}: cor={r['status_cor']} | estabilidade={float(r['stability_mean']):.3f} | confianca={float(r['confidence_mean']):.3f} | weak={int(r['weak_signal_assets'])}/{int(r['assets'])}"
        )
    if not sec_niche.empty:
        lines.append("")
        lines.append("Setores de nicho (menos de 10 ativos):")
        for _, r in sec_niche.sort_values(["risk_mean"], ascending=[False]).iterrows():
            lines.append(
                f"- {r['sector']}: ativos={int(r['assets'])} | cor={r['status_cor']} | risco={float(r['risk_mean']):.3f}"
            )
    lines.append("")
    lines.append("Leitura comercial simples:")
    lines.append("- Util para priorizar revisao de risco por setor antes de stress claro.")
    lines.append("- Nao e previsao de dia exato, e sim mudanca estrutural em andamento.")
    lines.append("- Melhora pratica: menos ruido no modo conservador sem perder taxa de acerto base.")
    (outdir / "report_step3_sector_diagnosis.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Master summary
    summary = {
        "status": "ok",
        "source_motor_run": str(motor_dir),
        "outdir": str(outdir),
        "step1_policy": {
            "event_metrics_l10": stability["event_metrics"]["l10"],
            "alert_share_total": stability["alert_share_total"],
            "regime_switches": stability["regime_switches"],
        },
        "step2_weak_signal": weak_summary,
        "step3_sector": {
            "sectors_total": int(len(sec)),
            "top_risk_sectors": top_risk_sector["sector"].tolist(),
            "top_stable_sectors": top_stable_sector["sector"].tolist(),
        },
    }
    _save_json(outdir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
