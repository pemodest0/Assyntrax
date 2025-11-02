#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

SUMMARY_CLASSIC = Path("results/graph_discovery/summary_index.json")
SUMMARY_QUANTUM = Path("results/graph_discovery/quantum_walk_summary.json")
OUTPUT = Path("results/graph_discovery/walk_mode_comparison.json")


def _extract_prob_keys(summary: Dict[str, object]) -> Dict[str, object]:
    metrics: Dict[str, object] = {
        "target_node": summary.get("target_node"),
        "prob_at_target": summary.get("prob_at_target"),
        "entropy_final": summary.get("entropy_final"),
    }
    for key, value in summary.items():
        if "prob_final" in key or "hitting_time" in key:
            metrics[key] = value
    return metrics


def main() -> None:
    if not SUMMARY_CLASSIC.exists() or not SUMMARY_QUANTUM.exists():
        raise SystemExit("Resumo clássico ou quântico ausente. Execute os scripts de descoberta primeiro.")

    classic = json.loads(SUMMARY_CLASSIC.read_text())
    quantum = json.loads(SUMMARY_QUANTUM.read_text())

    comparison: Dict[str, Dict[str, object]] = {}
    for domain in ["finance", "logistics", "health"]:
        classical_summary = classic.get(domain, {}).get("walk_summary")
        quantum_summary = quantum.get(f"{domain}_quantum", {}).get("summary")
        if not classical_summary or not quantum_summary:
            continue
        comparison[domain] = {
            "classical": _extract_prob_keys(classical_summary),
            "quantum": _extract_prob_keys(quantum_summary),
        }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(comparison, indent=2))
    print(f"Comparativo salvo em {OUTPUT}")


if __name__ == "__main__":
    main()
