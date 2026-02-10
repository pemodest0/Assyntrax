#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
OUTDIR_DEFAULT = ROOT / "results" / "validation"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def main() -> None:
    parser = argparse.ArgumentParser(description="Veredito automático lendo results/validation.")
    parser.add_argument("--root", type=str, default=str(OUTDIR_DEFAULT))
    args = parser.parse_args()

    root = Path(args.root)
    sanity = _read_json(root / "sanity" / "summary.json")
    robustness = _read_json(root / "robustness" / "aggregate.json")
    placebo = _read_json(root / "placebo" / "aggregate.json")
    universe = _read_json(root / "universe_mini" / "universe_report.json")
    synthetic_stress = _read_json(root / "synthetic_false_alarm_stress" / "summary.json")
    ablation = _read_json(root / "ablation" / "ablation_report.json")
    adaptive = _read_json(root / "adaptive_gates" / "summary.json")
    risk_utility = _read_json(root / "risk_utility" / "summary.json")

    sanity_ok = sanity.get("status") == "ok"
    stability_score = _safe_float(robustness.get("stability_score"))
    robustness_ok = robustness.get("status") == "ok" and stability_score >= 0.55
    placebo_ok = placebo.get("status") == "ok" and placebo.get("verdict") == "pass"

    counts = universe.get("counts") or {}
    ok_n = int(counts.get("ok") or 0)
    total_n = int(counts.get("total") or 0)
    universe_success_rate = (ok_n / total_n) if total_n > 0 else 0.0
    universe_ok = universe.get("status") == "ok" and universe_success_rate >= 0.80
    stress_ok = synthetic_stress.get("status") == "pass"
    ablation_ok = str(ablation.get("status", "")).lower() == "ok"
    adaptive_ok = str(adaptive.get("status", "")).lower() == "ok"
    risk_utility_ok = str(risk_utility.get("status", "")).lower() == "ok"

    original = placebo.get("original_metrics") or {}
    placebo_metrics = placebo.get("placebo_metrics") or {}
    shuffle = placebo_metrics.get("shuffle") or {}
    placebo_gap_quality = _safe_float(original.get("mean_quality")) - _safe_float(shuffle.get("mean_quality"))

    gate_checks = {
        "sanity_ok": bool(sanity_ok),
        "robustness_ok": bool(robustness_ok),
        "placebo_ok": bool(placebo_ok),
        "universe_ok": bool(universe_ok),
        "synthetic_stress_ok": bool(stress_ok),
        "ablation_ok": bool(ablation_ok),
        "adaptive_gates_ok": bool(adaptive_ok),
        "risk_utility_ok": bool(risk_utility_ok),
    }

    status = "pass" if all(gate_checks.values()) else "fail"

    notes: list[str] = []
    if not sanity_ok:
        notes.append(f"sanity falhou: {sanity.get('reason', 'sem detalhe')}")
    if not robustness_ok:
        notes.append(f"robustness abaixo do gate (stability_score={stability_score:.3f}, min=0.55)")
    if not placebo_ok:
        notes.append(f"placebo sem rejeição robusta: {placebo.get('reason', 'sem detalhe')}")
    if not universe_ok:
        notes.append(f"universe success rate baixo ({universe_success_rate:.2%}, min=80%)")
    if not stress_ok:
        fa = _safe_float(synthetic_stress.get("false_alarm_rate_no_shift"), default=-1.0)
        dr = _safe_float(synthetic_stress.get("detection_rate_has_shift"), default=-1.0)
        notes.append(f"synthetic stress falhou (fa_no_shift={fa:.3f}, detect_shift={dr:.3f})")
    if not ablation_ok:
        notes.append("ablation formal sem evidencia minima de ganho dinamico")
    if not adaptive_ok:
        notes.append("gates adaptativos/histerese indisponiveis")
    if not risk_utility_ok:
        notes.append("painel de utilidade de risco indisponivel")
    if not notes:
        notes.append("todos os gates passaram no estado atual")

    next_actions = [
        "fixar ambiente (scikit-learn e dependências do motor) para evitar fail por import",
        "aumentar estabilidade de segmentação para elevar stability_score acima de 0.55",
        "endurecer regra de recusa em placebo quando estrutura não é detectável",
        "elevar cobertura de datasets válidos no universe_mini para aumentar taxa de sucesso",
        "automatizar execução sequencial 01..04 em CI e bloquear merge quando status=fail",
    ]

    verdict = {
        "status": status,
        "gate_checks": gate_checks,
        "scores": {
            "stability_score": stability_score,
            "placebo_gap_quality": float(placebo_gap_quality),
            "universe_success_rate": float(universe_success_rate),
            "risk_utility_mean_dd_avoidance": _safe_float(risk_utility.get("mean_drawdown_avoidance"), default=0.0),
        },
        "notes": notes[:5],
        "next_actions": next_actions[:5],
    }

    out_path = root / "VERDICT.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(verdict, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        "verdict "
        f"status={verdict['status']} "
        f"sanity={gate_checks['sanity_ok']} robustness={gate_checks['robustness_ok']} "
        f"placebo={gate_checks['placebo_ok']} universe={gate_checks['universe_ok']}"
    )


if __name__ == "__main__":
    main()
