"""Gera relatório final do mapa do universo (global multivariado)."""

from __future__ import annotations

import argparse
from pathlib import Path
import json

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Relatorio do mapa do universo.")
    parser.add_argument("--global-dir", type=str, default="results/global_multivariate")
    parser.add_argument("--eval-report", type=str, default="results/auto_regime_eval/report.md")
    parser.add_argument("--out", type=str, default="results/universe_report.md")
    args = parser.parse_args()

    global_dir = Path(args.global_dir)
    summary_path = global_dir / "summary_global.csv"
    novelty_path = global_dir / "novelty_timeseries.csv"
    config_path = global_dir / "config.json"

    if not summary_path.exists():
        raise SystemExit("summary_global.csv não encontrado. Rode o mapa global antes.")

    summary = pd.read_csv(summary_path)
    novelty = pd.read_csv(novelty_path) if novelty_path.exists() else None
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}

    lines = [
        "# Mapa do Universo – Relatório Final",
        "",
        "## Configuração",
        f"- Ativos: {config.get('n_assets', 'n/a')}",
        f"- Período: {config.get('start', 'n/a')} → {config.get('end', 'n/a')}",
        f"- Embedding: m={config.get('m', 'n/a')}, tau={config.get('tau', 'n/a')}",
        f"- PCA: {config.get('pca_components', 'n/a')} componentes",
        f"- Método: {config.get('method', 'n/a')}",
        "",
        "## Resumo de clusters globais",
    ]

    if not summary.empty:
        lines.append("| cluster | count | percent | novelty_mean |")
        lines.append("| --- | --- | --- | --- |")
        for _, row in summary.sort_values("percent", ascending=False).iterrows():
            lines.append(
                f"| {int(row['cluster'])} | {int(row['count'])} | {row['percent']:.2f} | {row.get('novelty_mean', 0.0):.3f} |"
            )
        lines.append("")

    if novelty is not None and not novelty.empty:
        lines.extend(
            [
                "## Novidade (novelty) – Estatísticas",
                f"- Média: {novelty['novelty'].mean():.3f}",
                f"- Mediana: {novelty['novelty'].median():.3f}",
                f"- P95: {novelty['novelty'].quantile(0.95):.3f}",
                f"- P99: {novelty['novelty'].quantile(0.99):.3f}",
                "",
            ]
        )

    eval_report = Path(args.eval_report)
    if eval_report.exists():
        lines.extend(
            [
                "## Qualidade do motor (última avaliação)",
                eval_report.read_text(encoding="utf-8"),
                "",
            ]
        )

    Path(args.out).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
