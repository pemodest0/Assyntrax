#!/usr/bin/env python3
import json
from pathlib import Path
import pandas as pd

root = Path("results/forecast_suite")
map_path = Path("data/asset_groups.csv")

if not root.exists():
    print("results/forecast_suite not found")
    raise SystemExit(1)
if not map_path.exists():
    print("data/asset_groups.csv not found")
    raise SystemExit(1)

asset_groups = pd.read_csv(map_path)
asset_to_group = dict(zip(asset_groups["asset"], asset_groups["group"]))

rows = []

for asset_dir in root.iterdir():
    if not asset_dir.is_dir():
        continue
    asset = asset_dir.name
    group = asset_to_group.get(asset, "unknown")
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
                rows.append([group, asset, tf, h, reg, model, mase])

if not rows:
    print("No forecast regime results found.")
    raise SystemExit(0)

df = pd.DataFrame(rows, columns=["group","asset","tf","horizon","regime","best_model","mase"])
# aggregate per group: pick model with lowest mean mase by regime/horizon/tf
agg = (
    df.groupby(["group","tf","horizon","regime","best_model"], as_index=False)["mase"]
      .mean()
)
# choose best model per group/tf/horizon/regime
best_rows = []
for (group, tf, horizon, regime), gdf in agg.groupby(["group","tf","horizon","regime"]):
    gdf = gdf.sort_values("mase")
    best_rows.append(gdf.iloc[0])

best_df = pd.DataFrame(best_rows).reset_index(drop=True)

outdir = Path("results/forecast_suite")
(outdir / "sector_best_models.csv").write_text(best_df.to_csv(index=False), encoding="utf-8")

print(best_df.sort_values(["group","tf","horizon","regime"]).to_string(index=False))
