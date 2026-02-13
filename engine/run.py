from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from engine.forecast import forecast_series
from engine.io import load_dataset
from engine.preprocess import preprocess

matplotlib.use("Agg")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PSRE minimal runner")
    parser.add_argument("--input", type=str, required=True)
    parser.add_argument("--time-col", type=str, required=True)
    parser.add_argument("--value-col", type=str, required=True)
    parser.add_argument("--outdir", type=str, required=True)
    parser.add_argument("--source", type=str, default=None)
    parser.add_argument("--ons-mode", type=str, default="sum", choices=["sum", "select"])
    parser.add_argument("--prever", type=int, default=0)
    parser.add_argument("--metodo_previsao", type=str, default="media_recente", choices=["media_recente", "tendencia_curta"])
    parser.add_argument("--pdf", action="store_true")
    return parser.parse_args()


def _simple_summary(df, value_col: str, meta: dict, forecast_note: str) -> dict:
    values = df[value_col].to_numpy(dtype=float)
    last = float(values[-1])
    avg = float(np.mean(values))
    std = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
    return {
        "status": "ok",
        "n_points": int(values.size),
        "value_last": last,
        "mean": avg,
        "std": std,
        "dt_seconds": float(meta.get("dt_seconds", float("nan"))),
        "rows_in": int(meta.get("rows_in", values.size)),
        "rows_out": int(meta.get("rows_out", values.size)),
        "confianca": str(meta.get("confianca", "media")),
        "forecast_note": forecast_note,
    }


def _write_pdf(outdir: Path, df, time_col: str, value_col: str, forecast_df) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df[time_col], df[value_col], label="observado", linewidth=1.2)
    if forecast_df is not None and not forecast_df.empty:
        ax.plot(forecast_df["time"], forecast_df["value_previsto"], label="previsao", linestyle="--", linewidth=1.0)
    ax.set_title("PSRE - Série processada")
    ax.set_ylabel("valor")
    ax.legend()
    fig.tight_layout()
    fig.savefig(outdir / "report.pdf", dpi=160)
    plt.close(fig)


def run() -> None:
    args = _parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df, time_col, value_col = load_dataset(Path(args.input), args.time_col, args.value_col)
    processed, meta, time_col, value_col = preprocess(
        df=df,
        time_col=time_col,
        value_col=value_col,
        source=args.source,
        ons_mode=args.ons_mode,
    )
    processed.to_csv(outdir / "processed.csv", index=False)

    forecast_df, note = forecast_series(
        df=processed,
        time_col=time_col,
        value_col=value_col,
        horizon=args.prever,
        method=args.metodo_previsao,
        dt_seconds=float(meta.get("dt_seconds", float("nan"))),
    )
    if args.prever > 0 and not forecast_df.empty:
        forecast_df.to_csv(outdir / "forecast.csv", index=False)

    summary = _simple_summary(processed, value_col=value_col, meta=meta, forecast_note=note)
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.pdf:
        _write_pdf(outdir, processed, time_col=time_col, value_col=value_col, forecast_df=forecast_df)


if __name__ == "__main__":
    run()
