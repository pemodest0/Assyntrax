#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from data_quality import analyze_price_series, summarize_report


def main() -> None:
    parser = argparse.ArgumentParser(description="Verifica qualidade de dados de séries de preços.")
    parser.add_argument("csv", type=str, help="Arquivo CSV com colunas data e preço.")
    parser.add_argument("--date-col", type=str, default="date", help="Nome da coluna de datas.")
    parser.add_argument("--price-col", type=str, default="price", help="Nome da coluna de preço.")
    parser.add_argument(
        "--jump-threshold",
        type=float,
        default=15.0,
        help="Percentual de variação considerado salto anômalo.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Arquivo JSON para salvar o relatório.",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise SystemExit(f"Arquivo não encontrado: {csv_path}")

    df = pd.read_csv(csv_path)
    report = analyze_price_series(
        df,
        date_col=args.date_col,
        price_col=args.price_col,
        jump_threshold_pct=args.jump_threshold,
    )
    print(summarize_report(report))

    if args.output:
        report.to_json(Path(args.output))
        print(f"Relatório salvo em {args.output}")


if __name__ == "__main__":
    main()

