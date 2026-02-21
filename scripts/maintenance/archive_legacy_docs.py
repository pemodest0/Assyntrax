#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser(description="Archive selected legacy docs into docs/historico.")
    ap.add_argument(
        "--files",
        type=str,
        default="docs/graph_engine_plan.md,docs/graph_engine_deps.md,docs/graph_engine_universe_40.md,docs/graph_engine_frontend_contract.md",
    )
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    target_root = ROOT / "docs" / "historico" / f"arquivo_{stamp}"
    files = [x.strip() for x in str(args.files).split(",") if x.strip()]
    copied: list[str] = []
    missing: list[str] = []

    for rel in files:
        src = ROOT / rel
        if not src.exists():
            missing.append(rel)
            continue
        dst = target_root / src.name
        copied.append(f"{rel} -> {dst.relative_to(ROOT)}")
        if args.apply:
            target_root.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    report = ROOT / "docs" / "historico" / "ARQUIVO_MATERIAL_ANTIGO.md"
    lines = []
    lines.append("# Arquivo de Material Antigo")
    lines.append("")
    lines.append(f"Data UTC: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Modo: {'apply' if args.apply else 'dry-run'}")
    lines.append("")
    lines.append("## Copias")
    if copied:
        lines.extend([f"- {x}" for x in copied])
    else:
        lines.append("- nenhuma")
    lines.append("")
    lines.append("## Ausentes")
    if missing:
        lines.extend([f"- {x}" for x in missing])
    else:
        lines.append("- nenhum")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print({"status": "ok", "mode": "apply" if args.apply else "dry-run", "copied": len(copied), "missing": len(missing)})


if __name__ == "__main__":
    main()
