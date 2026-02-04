from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def merge_forecast_risk(
    asset: str,
    timeframe: str,
    outdir: Path,
    base_results: Path = Path("results"),
) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}

    # Try api_records from results/latest/
    api_path = base_results / "latest" / "api_records.jsonl"
    if api_path.exists():
        try:
            lines = api_path.read_text(encoding="utf-8").splitlines()
            for line in reversed(lines):
                rec = json.loads(line)
                if rec.get("asset") == asset and rec.get("timeframe") == timeframe:
                    merged["forecast_diag"] = {
                        "mase": rec.get("mase"),
                        "dir_acc": rec.get("dir_acc"),
                        "alerts": rec.get("alerts", []),
                    }
                    merged["risk"] = rec.get("risk", None)
                    break
        except Exception:
            pass

    # Try dashboard overview if available
    overview_path = base_results / "dashboard" / "overview.json"
    overview = load_json(overview_path) if overview_path.exists() else None
    if overview:
        for a in overview.get("assets", []):
            if a.get("asset") == asset:
                merged.setdefault("forecast_diag", {})
                merged["forecast_diag"]["confidence_score"] = a.get("mean_confidence")
                break

    return merged
