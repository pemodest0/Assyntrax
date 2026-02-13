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


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fmt_num(v: Any, nd: int = 3) -> str:
    if v is None:
        return "NA"
    try:
        x = float(v)
    except Exception:
        return str(v)
    if not np.isfinite(x):
        return "NA"
    return f"{x:.{nd}f}"


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    h = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join(["---"] * len(headers)) + " |"
    lines = [h, sep]
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(lines)


def _git_hash() -> str:
    try:
        out = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL)
        return out.strip()
    except Exception:
        return "unknown"


def _find_latest_run_id(base: Path) -> str:
    roots = [
        base / "synthetic_truth",
        base / "real_proxy",
        base / "sanity_ablation",
    ]
    sets: list[set[str]] = []
    for r in roots:
        if not r.exists():
            sets.append(set())
            continue
        sets.append({p.name for p in r.iterdir() if p.is_dir()})
    common = set.intersection(*sets) if sets else set()
    if not common:
        raise FileNotFoundError("No common run_id across synthetic_truth/real_proxy/sanity_ablation")
    return sorted(common)[-1]


def _detector_frame(summary: dict[str, Any]) -> pd.DataFrame:
    rows = summary.get("detectors", []) or []
    if not rows:
        return pd.DataFrame(columns=["model", "tpr", "fpr", "lead_p50", "lead_p90", "alerts_per_month", "switches_per_1000", "balanced_score"])
    return pd.DataFrame(rows)


def _scorecard_rows(synth: dict[str, Any], real: dict[str, Any], sanity: dict[str, Any]) -> list[list[Any]]:
    out: list[list[Any]] = []
    for name, sm in [("synthetic_truth", synth), ("real_proxy", real), ("sanity_ablation", sanity)]:
        sc = sm.get("scorecard", {}) or {}
        out.append(
            [
                name,
                _fmt_num(sc.get("tpr")),
                _fmt_num(sc.get("fpr")),
                _fmt_num(sc.get("lead_p50"), 2),
                _fmt_num(sc.get("lead_p90"), 2),
                _fmt_num(sc.get("alerts_per_month"), 2),
                _fmt_num(sc.get("switches_per_1000"), 2),
            ]
        )
    return out


def _combined_detector_ranking(synth: dict[str, Any], real: dict[str, Any]) -> pd.DataFrame:
    ds = _detector_frame(synth).rename(columns={c: f"{c}_synth" for c in ["tpr", "fpr", "lead_p50", "lead_p90", "alerts_per_month", "switches_per_1000", "balanced_score"]})
    dr = _detector_frame(real).rename(columns={c: f"{c}_real" for c in ["tpr", "fpr", "lead_p50", "lead_p90", "alerts_per_month", "switches_per_1000", "balanced_score"]})
    m = ds.merge(dr, on="model", how="outer")
    for col in ["tpr", "fpr", "lead_p50", "lead_p90", "alerts_per_month", "switches_per_1000", "balanced_score"]:
        a = m.get(f"{col}_synth").to_numpy(dtype=float)
        b = m.get(f"{col}_real").to_numpy(dtype=float)
        vals: list[float] = []
        for i in range(len(m)):
            cands = [a[i], b[i]]
            cands = [float(v) for v in cands if np.isfinite(v)]
            vals.append(float(np.mean(cands)) if cands else np.nan)
        m[col] = vals
    m = m[["model", "tpr", "fpr", "lead_p50", "lead_p90", "alerts_per_month", "switches_per_1000", "balanced_score"]]
    m = m.sort_values("balanced_score", ascending=False, na_position="last").reset_index(drop=True)
    return m


def _build_verdict(synth: dict[str, Any], real: dict[str, Any], sanity: dict[str, Any], rank_df: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    good: list[str] = []
    bad: list[str] = []
    recs: list[str] = []

    sc_s = synth.get("scorecard", {}) or {}
    sc_r = real.get("scorecard", {}) or {}
    sc_n = sanity.get("scorecard", {}) or {}
    checks = (sanity.get("checks", {}) or {})

    tpr_s = sc_s.get("tpr")
    fpr_s = sc_s.get("fpr")
    tpr_r = sc_r.get("tpr")
    fpr_r = sc_r.get("fpr")

    if tpr_s is not None and float(tpr_s) >= 0.60:
        good.append(f"Deteccao sintetica forte: TPR={float(tpr_s):.3f} (alvo >= 0.60).")
    if fpr_s is not None and float(fpr_s) <= 0.25:
        good.append(f"Falso alarme sintetico controlado: FPR={float(fpr_s):.3f} (alvo <= 0.25).")
    if bool(checks.get("scale_invariance_ok")):
        good.append("Sanity de invariancia de escala aprovado.")
    if not good:
        good.append("Pipeline completo executou sem falha fatal.")
    while len(good) < 3:
        good.append("Artefatos completos gerados (summary + per_asset em 3 frentes).")

    if tpr_r is not None and float(tpr_r) < 0.60:
        bad.append(f"TPR em proxy real ainda baixo: {float(tpr_r):.3f}.")
    if fpr_r is not None and float(fpr_r) > 0.25:
        bad.append(f"FPR em proxy real acima do alvo: {float(fpr_r):.3f}.")
    flags = checks.get("flags", []) or []
    if flags:
        bad.extend([str(f) for f in flags[:2]])
    if not bad:
        bad.append("Nao houve queda forte em todos os sanity checks esperados.")
    while len(bad) < 3:
        bad.append("Persistencia/consenso ainda pode ser ajustada para reduzir ruído.")

    if tpr_s is None or float(tpr_s) < 0.60:
        recs.append("Ajustar sensibilidade do eigen (threshold -10%) para atingir TPR>=0.60 em sintético.")
    else:
        recs.append("Manter TPR sintetico >=0.60 e otimizar FPR com histerese +1 barra.")

    if fpr_r is None or float(fpr_r) > 0.25:
        recs.append("Aumentar persistência mínima para reduzir FPR real para <=0.25 mantendo lead_p50>=0.")
    else:
        recs.append("Fixar FPR real <=0.25 como gate de release e monitorar drift mensal.")

    top_model = "eigen"
    if not rank_df.empty and pd.notna(rank_df.iloc[0]["model"]):
        top_model = str(rank_df.iloc[0]["model"])
    recs.append(f"Usar {top_model} como detector primário e rmt_gate como auditor opcional; alvo alerts/month<=6 e switches/1000<=120.")
    return good[:3], bad[:3], recs[:3]


def main() -> None:
    p = argparse.ArgumentParser(description="Print executive motor validation report from benchmark artifacts.")
    p.add_argument("--outdir", type=str, default=str(ROOT / "results" / "benchmarks"))
    p.add_argument("--run_id", type=str, default=None)
    args = p.parse_args()

    base = Path(args.outdir)
    run_id = args.run_id or _find_latest_run_id(base)

    synth_dir = base / "synthetic_truth" / run_id
    real_dir = base / "real_proxy" / run_id
    sanity_dir = base / "sanity_ablation" / run_id

    synth = _read_json(synth_dir / "summary.json")
    real = _read_json(real_dir / "summary.json")
    sanity = _read_json(sanity_dir / "summary.json")

    real_per_asset = pd.read_csv(real_dir / "per_asset.csv")
    rank_df = _combined_detector_ranking(synth, real)
    good, bad, recs = _build_verdict(synth, real, sanity, rank_df)

    now = datetime.now(timezone.utc).isoformat()
    gh = _git_hash()

    print("========== MOTOR VALIDATION REPORT ==========")
    print(f"run_id: {run_id}")
    print(f"git_commit: {gh}")
    print(f"generated_at_utc: {now}")
    print("")

    print("## 1) Scorecard agregado")
    print(
        _md_table(
            ["suite", "TPR", "FPR", "lead_p50", "lead_p90", "alerts/month", "switches/1000"],
            _scorecard_rows(synth, real, sanity),
        )
    )
    print("")

    print("## 2) Tabela por detector/camada (ranking por balanced score)")
    rows_rank: list[list[Any]] = []
    for i, r in rank_df.iterrows():
        rows_rank.append(
            [
                int(i + 1),
                r["model"],
                _fmt_num(r["tpr"]),
                _fmt_num(r["fpr"]),
                _fmt_num(r["lead_p50"], 2),
                _fmt_num(r["lead_p90"], 2),
                _fmt_num(r["balanced_score"]),
            ]
        )
    print(_md_table(["rank", "model", "TPR", "FPR", "lead_p50", "lead_p90", "balanced_score"], rows_rank))
    print("")

    print("## 3) Tabela por ativo (10 ativos)")
    asset_rows: list[list[Any]] = []
    for _, r in real_per_asset.sort_values("asset").iterrows():
        asset_rows.append(
            [
                r.get("asset", ""),
                r.get("regime_final", ""),
                r.get("status_final", ""),
                _fmt_num(r.get("alert_rate"), 3),
                _fmt_num(r.get("switches"), 2),
                r.get("top_3_reasons", ""),
            ]
        )
    print(_md_table(["asset", "regime_final", "status_final", "alert_rate", "switches/1000", "top 3 reasons"], asset_rows))
    print("")

    print("## 4) Sanity checks")
    checks = sanity.get("checks", {}) or {}
    sanity_rows = [
        ["shuffle derruba performance", checks.get("shuffle_performance_drop"), ""],
        ["phase-random derruba performance", checks.get("phase_performance_drop"), ""],
        ["invariancia de escala", checks.get("scale_invariance_ok"), ""],
    ]
    flags = checks.get("flags", []) or []
    for f in flags:
        sanity_rows.append(["FLAG", "true", str(f)])
    print(_md_table(["check", "status", "notes"], sanity_rows))
    print("")

    print("## 5) Veredito do motor")
    print("### O que esta bom")
    for g in good:
        print(f"- {g}")
    print("### O que esta ruim")
    for b in bad:
        print(f"- {b}")
    print("### Mudancas recomendadas")
    for r in recs:
        print(f"- {r}")
    print("")

    print("## Artefatos")
    print(f"- synthetic_truth: {synth_dir}")
    print(f"- real_proxy: {real_dir}")
    print(f"- sanity_ablation: {sanity_dir}")
    print("============================================")


if __name__ == "__main__":
    main()
