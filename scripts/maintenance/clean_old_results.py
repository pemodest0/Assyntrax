#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _is_timestamp_dir(name: str) -> bool:
    # examples: 20260220T171218Z or 20260220T171218
    n = name.strip()
    if len(n) < 15:
        return False
    if not n.startswith("20"):
        return False
    if "T" not in n:
        return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Archive old timestamped result runs with retention.")
    ap.add_argument("--results-root", type=str, default="results")
    ap.add_argument("--keep-days", type=int, default=14)
    ap.add_argument(
        "--targets",
        type=str,
        default="sector_crisis_suite,followup_123,motor_470_program,event_study,event_study_sectors,event_study_sectors_tune,hyper_sector_search,dual_mode_compare,monthly_revalidation",
    )
    ap.add_argument("--apply", action="store_true", help="Execute moves. Default is dry-run.")
    args = ap.parse_args()

    results_root = ROOT / args.results_root
    archive_root = results_root / "_archive"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_archive = archive_root / f"cleanup_{stamp}"
    keep_after = datetime.now(timezone.utc) - timedelta(days=max(1, int(args.keep_days)))

    targets = [x.strip() for x in str(args.targets).split(",") if x.strip()]
    moves: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []

    for folder in targets:
        base = results_root / folder
        if not base.exists() or not base.is_dir():
            skipped.append({"path": str(base), "reason": "missing"})
            continue
        dirs = sorted([d for d in base.iterdir() if d.is_dir()])
        for d in dirs:
            if not _is_timestamp_dir(d.name):
                continue
            mtime = datetime.fromtimestamp(d.stat().st_mtime, tz=timezone.utc)
            if mtime >= keep_after:
                continue
            dst = run_archive / folder / d.name
            moves.append({"src": str(d), "dst": str(dst), "mtime_utc": mtime.isoformat()})

    manifest = {
        "status": "dry_run" if not args.apply else "applied",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "keep_days": int(args.keep_days),
        "targets": targets,
        "planned_moves": moves,
        "skipped": skipped,
    }

    run_archive.mkdir(parents=True, exist_ok=True)
    (run_archive / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.apply:
        for row in moves:
            src = Path(row["src"])
            dst = Path(row["dst"])
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        (archive_root / "LATEST_CLEANUP.json").write_text(
            json.dumps({"path": str(run_archive), "generated_at_utc": manifest["generated_at_utc"]}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "status": manifest["status"],
                "archive_run": str(run_archive),
                "n_moves": len(moves),
                "n_skipped": len(skipped),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
