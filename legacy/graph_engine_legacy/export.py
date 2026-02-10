from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Iterable, Optional, Sequence, Mapping, Any

from .schema import GraphAsset


def ensure_dirs(base: Path) -> Path:
    assets_dir = base / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir


def write_asset_bundle(
    asset: GraphAsset,
    outdir: Path,
    embedding: Optional[Sequence[Sequence[float]]] = None,
    regimes: Optional[Sequence[Mapping[str, Any]]] = None,
    micrograph: Optional[dict] = None,
    transitions: Optional[dict] = None,
) -> None:
    assets_dir = ensure_dirs(outdir)
    base = f"{asset.asset}_{asset.timeframe}"

    asset_path = assets_dir / f"{base}.json"
    asset_path.write_text(json.dumps(asset.to_dict(), indent=2), encoding="utf-8")

    if embedding is not None:
        emb_path = assets_dir / f"{base}_embedding.csv"
        rows = embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
        with emb_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if len(rows) > 0 and len(rows[0]) > 0:
                writer.writerow([f"c{i+1}" for i in range(len(rows[0]))])
            writer.writerows(rows)

    if regimes is not None:
        regimes_path = assets_dir / f"{base}_regimes.csv"
        if len(regimes) == 0:
            regimes_path.write_text("", encoding="utf-8")
        else:
            keys = list(regimes[0].keys())
            with regimes_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(regimes)

    if micrograph is not None:
        micro_path = assets_dir / f"{base}_micrograph.json"
        micro_path.write_text(json.dumps(micrograph, indent=2), encoding="utf-8")

    if transitions is not None:
        trans_path = assets_dir / f"{base}_transitions.json"
        trans_path.write_text(json.dumps(transitions, indent=2), encoding="utf-8")


def write_universe(universe: Iterable[GraphAsset], out_path: Path) -> None:
    data = [u.to_dict() for u in universe]
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
