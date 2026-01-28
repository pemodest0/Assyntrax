#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from data_ingestion import NormalizationResult, normalize_price_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Normaliza CSV de preços (date, price).")
    parser.add_argument("input", type=str, help="Arquivo CSV bruto.")
    parser.add_argument("--output", type=str, default=None, help="Arquivo CSV normalizado.")
    parser.add_argument("--date-col", type=str, default=None, help="Nome da coluna de data se quiser definir manualmente.")
    parser.add_argument("--price-col", type=str, default=None, help="Nome da coluna de preço se quiser definir manualmente.")
    parser.add_argument("--sep", type=str, default=None, help="Separador dos campos (separador decimal conflitar com separador de coluna).")
    parser.add_argument("--decimal", type=str, default=None, help="Caractere decimal (ex.: ',' para dados europeus).")
    parser.add_argument("--thousands", type=str, default=None, help="Separador de milhares opcional.")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise SystemExit(f"Arquivo não encontrado: {input_path}")

    output_path = Path(args.output) if args.output else None
    result: NormalizationResult = normalize_price_csv(
        input_path,
        output_path=output_path,
        date_column=args.date_col,
        price_column=args.price_col,
        separator=args.sep,
        decimal=args.decimal,
        thousands=args.thousands,
    )

    print(f"Normalização concluída. Datas: {result.date_column}, Valores: {result.price_column}")
    if output_path:
        print(f"Arquivo salvo em {output_path}")


if __name__ == "__main__":
    main()

