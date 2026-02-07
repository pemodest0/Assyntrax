#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]


def _hash_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _iter_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    for p in path.rglob("*"):
        if p.is_file():
            yield p


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze engine snapshot for auditability.")
    parser.add_argument("--tag", required=True, help="Snapshot tag, e.g. v2026.02.06-sector-risk-v1")
    parser.add_argument("--outdir", default="results/frozen", help="Base output directory")
    parser.add_argument(
        "--include",
        action="append",
        required=True,
        help="File or directory to include (can be used multiple times)",
    )
    args = parser.parse_args()

    outdir = Path(args.outdir).expanduser()
    snapshot_dir = outdir / args.tag
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "tag": args.tag,
        "root": str(ROOT),
        "items": [],
    }

    for item in args.include:
        src = Path(item)
        if not src.is_absolute():
            src = ROOT / src
        if not src.exists():
            print(f"[skip] missing {src}")
            continue
        rel = src.relative_to(ROOT)
        dst = snapshot_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

        for f in _iter_files(src):
            stat = f.stat()
            manifest["items"].append(
                {
                    "path": str(f.relative_to(ROOT)),
                    "size": stat.st_size,
                    "mtime": stat.st_mtime,
                    "sha256": _hash_file(f),
                }
            )

    manifest_path = snapshot_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[ok] snapshot written to {snapshot_dir}")


if __name__ == "__main__":
    main()
