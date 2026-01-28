"""Executa um comando exibindo barra de progresso/ETA aproximada."""

from __future__ import annotations

import argparse
import subprocess
import time
import sys

try:
    from tqdm import tqdm
except Exception:  # pragma: no cover
    tqdm = None


def run_with_progress(
    command: list[str],
    label: str,
    expected_seconds: int,
    log_path: str | None = None,
) -> int:
    log_handle = None
    if log_path:
        log_handle = open(log_path, "w", encoding="utf-8")
        log_handle.write(f"[command] {' '.join(command)}\n")
        log_handle.flush()

    if tqdm is None:
        print(f"[start] {label}: {' '.join(command)}")
        result = subprocess.run(command, stdout=log_handle, stderr=log_handle)
        print(f"[done] {label} (exit={result.returncode})")
        if log_handle:
            log_handle.close()
        return result.returncode

    bar = tqdm(total=1.0, desc=label, unit="task")
    start = time.time()
    process = subprocess.Popen(command, stdout=log_handle, stderr=log_handle)
    try:
        while process.poll() is None:
            elapsed = time.time() - start
            progress = min(elapsed / max(expected_seconds, 1), 0.98)
            bar.n = progress
            bar.refresh()
            time.sleep(1.0)
        bar.n = 1.0
        bar.refresh()
    finally:
        bar.close()
        if log_handle:
            log_handle.close()
    return process.returncode or 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run command with progress bar.")
    parser.add_argument("--label", type=str, default="task")
    parser.add_argument("--expected", type=int, default=60)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if not args.command:
        print("Nenhum comando fornecido.")
        sys.exit(1)
    code = run_with_progress(args.command, args.label, args.expected)
    sys.exit(code)


if __name__ == "__main__":
    main()
