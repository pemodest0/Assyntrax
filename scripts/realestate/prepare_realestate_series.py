from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

DATE_COLS = ["date", "datetime", "mes", "month", "data"]
VALUE_COLS = ["price", "preco", "valor", "value", "index", "fipezap", "ivar"]


def _pick_col(cols: list[str], candidates: list[str]) -> str | None:
    lower = {c.lower(): c for c in cols}
    for c in candidates:
        if c in lower:
            return lower[c]
    return None


def prepare_file(src: Path, out_dir: Path) -> Path:
    df = pd.read_csv(src)
    date_col = _pick_col(list(df.columns), DATE_COLS)
    value_col = _pick_col(list(df.columns), VALUE_COLS)
    if date_col is None or value_col is None:
        raise ValueError(f"cols not found in {src.name}: date={date_col} value={value_col}")
    out = df[[date_col, value_col]].copy()
    out.columns = ["date", "value"]
    out["date"] = pd.to_datetime(out["date"], errors="coerce")
    out = out.dropna(subset=["date", "value"]).sort_values("date")
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / src.name
    out.to_csv(dest, index=False)
    return dest


def main() -> None:
    parser = argparse.ArgumentParser(description="Normaliza series imobiliarias locais.")
    parser.add_argument("--input", required=True, help="Arquivo CSV de entrada.")
    parser.add_argument("--outdir", default="data/realestate/normalized", help="Saida normalizada.")
    args = parser.parse_args()

    src = Path(args.input)
    dest = prepare_file(src, Path(args.outdir))
    print(f"[ok] wrote {dest}")


if __name__ == "__main__":
    main()
