#!/usr/bin/env python3
import json
from pathlib import Path
import pandas as pd

root = Path("results/forecast_suite")
rows = []

if not root.exists():
    print("results/forecast_suite not found")
    raise SystemExit(1)

for asset_dir in root.iterdir():
    if not asset_dir.is_dir():
        continue
    asset = asset_dir.name
    for tf_dir in asset_dir.iterdir():
        if not tf_dir.is_dir():
            continue
        tf = tf_dir.name
        for f in tf_dir.glob(f"{asset}_{tf}_*_h*.json"):
            if "_return_" not in f.name and "_log_return_" not in f.name:
                continue
            data = json.loads(f.read_text())
            by_year = data.get("by_year", {})
            if not by_year:
                continue

            reg_scores = {}
            reg_counts = {}
            for _y, yd in by_year.items():
                by_reg = yd.get("by_regime", {})
                for model, regs in by_reg.items():
                    for reg, met in regs.items():
                        if met is None or "mase" not in met:
                            continue
                        reg_scores[(reg, model)] = reg_scores.get((reg, model), 0.0) + met["mase"]
                        reg_counts[(reg, model)] = reg_counts.get((reg, model), 0) + 1

            best = {}
            for (reg, model), s in reg_scores.items():
                c = max(1, reg_counts[(reg, model)])
                mase = s / c
                if reg not in best or mase < best[reg][1]:
                    best[reg] = (model, mase)

            h = f.name.split("_h")[-1].replace(".json", "")
            for reg, (model, mase) in best.items():
                rows.append([asset, tf, h, reg, model, mase])

if not rows:
    print("No forecast regime results found.")
    raise SystemExit(0)

df = pd.DataFrame(rows, columns=["asset", "tf", "horizon", "regime", "best_model", "mase"])
print(df.sort_values(["asset", "tf", "horizon", "regime"]).to_string(index=False))
