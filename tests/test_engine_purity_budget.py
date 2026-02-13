from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_engine_legacy_import_budget() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    baseline_path = repo_root / "config" / "engine_purity_baseline.json"
    audit_script = repo_root / "tools" / "engine_purity_audit.py"

    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    output = subprocess.check_output([sys.executable, str(audit_script), "--json"], cwd=repo_root, text=True)
    current = json.loads(output)

    assert current["total_legacy_imports"] <= baseline["max_total_legacy_imports"]

    expected = {row["path"]: row["max_count"] for row in baseline["files"]}
    actual = {row["path"]: row["count"] for row in current["files"]}

    unexpected_files = sorted(set(actual) - set(expected))
    assert not unexpected_files, f"New legacy-import files introduced in engine/: {unexpected_files}"

    regressions = {
        path: {"actual": actual[path], "max": expected[path]}
        for path in sorted(set(actual) & set(expected))
        if actual[path] > expected[path]
    }
    assert not regressions, f"Legacy-import counts increased: {regressions}"
