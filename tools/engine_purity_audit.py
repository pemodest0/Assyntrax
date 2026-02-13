from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

FORBIDDEN_ROOTS = ("spa", "graph_engine")
IMPORT_RE = re.compile(r"^\s*(from|import)\s+([A-Za-z_][\w\.]*)")


@dataclass(frozen=True)
class LegacyImport:
    path: str
    line: int
    module: str
    statement: str


def _is_forbidden(module_name: str) -> bool:
    return any(module_name == root or module_name.startswith(f"{root}.") for root in FORBIDDEN_ROOTS)


def collect_legacy_imports(repo_root: Path) -> list[LegacyImport]:
    engine_root = repo_root / "engine"
    offenders: list[LegacyImport] = []

    for file_path in sorted(engine_root.rglob("*.py")):
        rel_path = file_path.relative_to(repo_root).as_posix()
        for idx, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), start=1):
            match = IMPORT_RE.match(line.lstrip("\ufeff"))
            if not match:
                continue
            module = match.group(2)
            if not _is_forbidden(module):
                continue
            offenders.append(
                LegacyImport(
                    path=rel_path,
                    line=idx,
                    module=module,
                    statement=line.strip(),
                )
            )
    return offenders


def build_report(repo_root: Path) -> dict:
    offenders = collect_legacy_imports(repo_root)
    by_file = Counter(item.path for item in offenders)
    file_rows = [{"path": path, "count": count} for path, count in sorted(by_file.items())]

    return {
        "roots": list(FORBIDDEN_ROOTS),
        "total_legacy_imports": len(offenders),
        "files": file_rows,
        "offenders": [asdict(item) for item in offenders],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit legacy imports inside engine/ for core purity migration.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    report = build_report(repo_root)

    if args.json:
        print(json.dumps(report, indent=2))
        return 0

    print("Engine purity audit")
    print(f"- repo_root: {repo_root}")
    print(f"- total_legacy_imports: {report['total_legacy_imports']}")
    print("- files:")
    for row in report["files"]:
        print(f"  - {row['path']}: {row['count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
