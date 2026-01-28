#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import pandas as pd


def load_predictions(path: Path, mode: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df = df[df["split"] == "test"].copy()
    quantum_col = f"{mode}_price_pred"
    if quantum_col not in df.columns:
        raise ValueError(f"Coluna {quantum_col} não encontrada em {path}.")
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df, quantum_col


def compute_mae(series_true: pd.Series, series_pred: pd.Series) -> float:
    return float((series_true - series_pred).abs().mean())


def plot_asset_mode(df: pd.DataFrame, quantum_col: str, asset: str, mode: str, output_path: Path) -> None:
    title_mode = "Hadamard" if "hadamard" in mode else "Grover"
    true = df["price_real"]
    classical = df["price_pred"]
    quantum_pred = df[quantum_col]
    blend = df["blend_price_pred"]

    mae_classical = compute_mae(true, classical)
    mae_quantum = compute_mae(true, quantum_pred)
    mae_blend = compute_mae(true, blend)

    error_classical = (true - classical).abs()
    error_quantum = (true - quantum_pred).abs()
    error_blend = (true - blend).abs()

    fig, (ax_price, ax_error) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    ax_price.plot(df["date"], true, color="black", linewidth=1.5, label="Preço real")
    ax_price.plot(df["date"], classical, linestyle="--", linewidth=1.1, label="Clássico")
    ax_price.plot(df["date"], quantum_pred, linestyle=":", linewidth=1.1, label="Quântico")
    ax_price.plot(df["date"], blend, linewidth=1.2, label="Blend dinâmico")
    ax_price.set_title(f"{asset} • Moeda {title_mode}")
    ax_price.set_ylabel("Preço")
    ax_price.grid(True, linestyle="--", alpha=0.3)
    ax_price.legend(ncol=4, loc="upper left")

    ax_error.plot(df["date"], error_classical, linestyle="--", linewidth=1.1, label=f"Erro clássico (MAE={mae_classical:.2f})")
    ax_error.plot(df["date"], error_quantum, linestyle=":", linewidth=1.1, label=f"Erro quântico (MAE={mae_quantum:.2f})")
    ax_error.plot(df["date"], error_blend, linewidth=1.2, label=f"Erro blend (MAE={mae_blend:.2f})")
    ax_error.set_ylabel("Erro absoluto")
    ax_error.set_xlabel("Data")
    ax_error.grid(True, linestyle="--", alpha=0.3)
    ax_error.legend(ncol=1)

    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera gráficos comparando previsões clássicas, quânticas e blendadas.")
    parser.add_argument("--assets", nargs="+", default=["BTC-USD", "ETH-USD", "SOL-USD"], help="Ativos para processar.")
    parser.add_argument("--modes", nargs="+", default=["quantum_hadamard", "quantum_grover"], help="Modos quânticos.")
    parser.add_argument("--pred-dir", default="results/crypto_blend", help="Diretório com arquivos *_dynamic_blend_predictions.csv.")
    parser.add_argument("--output-dir", default="results/crypto_blend/plots", help="Diretório para salvar gráficos.")
    args = parser.parse_args()

    pred_dir = Path(args.pred_dir)
    output_dir = Path(args.output_dir)

    summary_rows: List[dict] = []
    for asset in args.assets:
        asset_clean = asset.replace("^", "")
        for mode in args.modes:
            filename = f"{asset_clean}_{mode}_dynamic_blend_predictions.csv"
            path = pred_dir / filename
            if not path.exists():
                print(f"[WARN] Arquivo {path} não encontrado; pulando.")
                continue
            df, quantum_col = load_predictions(path, mode)
            if df.empty:
                print(f"[WARN] Dados vazios em {path}; pulando.")
                continue
            out_path = output_dir / f"{asset_clean}_{mode}_comparison.png"
            plot_asset_mode(df, quantum_col, asset, mode, out_path)

            summary_rows.append(
                {
                    "asset": asset,
                    "mode": mode,
                    "records": df.shape[0],
                    "mae_classical": compute_mae(df["price_real"], df["price_pred"]),
                    "mae_quantum": compute_mae(df["price_real"], df[quantum_col]),
                    "mae_blend": compute_mae(df["price_real"], df["blend_price_pred"]),
                }
            )

    if summary_rows:
        summary = pd.DataFrame(summary_rows)
        summary["gain_vs_classical_pct"] = (summary["mae_classical"] - summary["mae_blend"]) / summary["mae_classical"] * 100
        summary["gain_vs_quantum_pct"] = (summary["mae_quantum"] - summary["mae_blend"]) / summary["mae_quantum"] * 100
        summary.sort_values(["asset", "mode"], inplace=True)
        summary_path = output_dir / "blend_comparison_summary.csv"
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(summary_path, index=False)
        print(f"Resumo salvo em {summary_path}")
    else:
        print("Nenhum gráfico gerado (verifique assets/modes informados).")


if __name__ == "__main__":
    main()
