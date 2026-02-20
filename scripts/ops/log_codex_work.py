#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _split_csv(s: str) -> list[str]:
    vals = [x.strip() for x in str(s).split(",")]
    return [x for x in vals if x]


def main() -> None:
    ap = argparse.ArgumentParser(description="Append Codex work entry to persistent log.")
    ap.add_argument("--kind", type=str, default="note", help="entry type: note|run|result|decision|todo")
    ap.add_argument("--title", type=str, required=True)
    ap.add_argument("--summary", type=str, default="")
    ap.add_argument("--artifacts", type=str, default="", help="comma-separated file paths")
    ap.add_argument("--tags", type=str, default="", help="comma-separated tags")
    ap.add_argument("--metrics-json", type=str, default="", help="raw JSON object string")
    ap.add_argument("--out-jsonl", type=str, default="results/codex/worklog.jsonl")
    ap.add_argument("--out-latest", type=str, default="results/codex/worklog_latest.json")
    args = ap.parse_args()

    metrics: dict[str, object] = {}
    if str(args.metrics_json).strip():
        try:
            raw = json.loads(str(args.metrics_json))
            if isinstance(raw, dict):
                metrics = raw
        except Exception:
            metrics = {"raw_metrics_text": str(args.metrics_json)}

    payload = {
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "kind": str(args.kind).strip().lower(),
        "title": str(args.title).strip(),
        "summary": str(args.summary).strip(),
        "artifacts": _split_csv(args.artifacts),
        "tags": _split_csv(args.tags),
        "metrics": metrics,
    }

    out_jsonl = ROOT / str(args.out_jsonl)
    out_latest = ROOT / str(args.out_latest)
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    out_latest.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    out_latest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": "ok",
                "out_jsonl": str(out_jsonl),
                "out_latest": str(out_latest),
                "title": payload["title"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
