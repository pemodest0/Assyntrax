#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute top2 models per asset/regime from forecast_suite.")
    parser.add_argument("--root", default="results/forecast_suite", help="Forecast suite root dir.")
    parser.add_argument(
        "--out",
        default="results/forecast_suite/best_models_by_regime_top2.csv",
        help="Output CSV path.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    rows = []
    if not root.exists():
        raise SystemExit(f"[error] missing {root}")

    for asset_dir in root.iterdir():
        if not asset_dir.is_dir():
            continue
        asset = asset_dir.name
        for tf_dir in asset_dir.iterdir():
            if not tf_dir.is_dir():
                continue
            tf = tf_dir.name
            for f in tf_dir.glob(f"{asset}_{tf}_log_return_h*.json"):
                data = json.loads(f.read_text())
                by_year = data.get("by_year", {})
                if not by_year:
                    continue

                reg_scores = {}
                reg_counts = {}
                for _, yd in by_year.items():
                    by_reg = yd.get("by_regime", {})
                    for model, regs in by_reg.items():
                        for reg, met in regs.items():
                            if not met or "mase" not in met:
                                continue
                            key = (reg, model)
                            reg_scores[key] = reg_scores.get(key, 0.0) + float(met["mase"])
                            reg_counts[key] = reg_counts.get(key, 0) + 1

                h = f.name.split("_h")[-1].replace(".json", "")
                by_regime = {}
                for (reg, model), s in reg_scores.items():
                    c = max(1, reg_counts[(reg, model)])
                    mase = s / c
                    by_regime.setdefault(reg, []).append((model, mase))

                for reg, items in by_regime.items():
                    items = sorted(items, key=lambda x: x[1])
                    best_model, best_mase = items[0]
                    second_model, second_mase = (items[1] if len(items) > 1 else items[0])
                    rows.append(
                        [
                            asset,
                            tf,
                            h,
                            reg,
                            best_model,
                            second_model,
                            best_mase,
                            second_mase,
                        ]
                    )

    df = pd.DataFrame(
        rows,
        columns=[
            "asset",
            "tf",
            "horizon",
            "regime",
            "best_model",
            "second_model",
            "best_mase",
            "second_mase",
        ],
    )
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    out_json = out_path.with_suffix(".json")
    out_json.write_text(df.to_json(orient="records", indent=2), encoding="utf-8")
    print(f"[ok] wrote {out_path}")


if __name__ == "__main__":
    main()
