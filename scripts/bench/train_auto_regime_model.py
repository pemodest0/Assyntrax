"""Treina o modelo automÃ¡tico de rotulagem de regimes."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.diagnostics.auto_regime_model import train_auto_regime_model


def main() -> None:
    parser = argparse.ArgumentParser(description="Treino do modelo automÃ¡tico de regimes.")
    parser.add_argument("--results", type=str, default="results", help="Pasta de resultados.")
    parser.add_argument("--model-dir", type=str, default="models", help="Pasta para salvar o modelo.")
    parser.add_argument("--no-balance", action="store_true", help="Desativa balanceamento das classes.")
    parser.add_argument("--min-count", type=int, default=2, help="MÃ­nimo de exemplos por regime.")
    parser.add_argument(
        "--balance-mode",
        type=str,
        default="oversample",
        choices=("oversample", "downsample", "none"),
        help="EstratÃ©gia de balanceamento.",
    )
    parser.add_argument(
        "--max-per-class",
        type=int,
        default=None,
        help="Limite mÃ¡ximo de amostras por classe apÃ³s balanceamento.",
    )
    args = parser.parse_args()

    results_root = Path(args.results)
    model_dir = Path(args.model_dir)
    model_path = model_dir / "auto_regime_model.joblib"
    meta_path = model_dir / "auto_regime_model_meta.json"

    model = train_auto_regime_model(
        results_root=results_root,
        model_path=model_path,
        meta_path=meta_path,
        balance=not args.no_balance,
        balance_mode="oversample" if args.balance_mode == "none" else args.balance_mode,
        min_count=args.min_count,
        max_per_class=args.max_per_class,
    )
    print(f"Modelo treinado com features: {model.feature_names}")
    print(f"Salvo em: {model_path}")


if __name__ == "__main__":
    main()

