"""Compara duas avaliacoes do modelo automatico."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_report(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Comparar dois reports de avaliacao.")
    parser.add_argument("--before", required=True, help="JSON antigo (holdout).")
    parser.add_argument("--after", required=True, help="JSON novo (holdout).")
    parser.add_argument("--out", default="results/auto_regime_eval/compare_report.md")
    args = parser.parse_args()

    before = load_report(Path(args.before))
    after = load_report(Path(args.after))

    def get_metric(rep: dict, key: str) -> float:
        return float(rep.get(key, {}).get("f1-score", rep.get(key, 0.0)))

    before_f1 = get_metric(before, "weighted avg")
    after_f1 = get_metric(after, "weighted avg")
    before_acc = float(before.get("accuracy", 0.0))
    after_acc = float(after.get("accuracy", 0.0))

    lines = [
        "# Comparacao de avaliacao (holdout)",
        "",
        f"- Before weighted F1: {before_f1:.4f}",
        f"- After  weighted F1: {after_f1:.4f}",
        f"- Delta: {after_f1 - before_f1:+.4f}",
        "",
        f"- Before accuracy: {before_acc:.4f}",
        f"- After  accuracy: {after_acc:.4f}",
        f"- Delta: {after_acc - before_acc:+.4f}",
        "",
    ]
    Path(args.out).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
