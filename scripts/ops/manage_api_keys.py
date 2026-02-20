#!/usr/bin/env python3
from __future__ import annotations

import argparse
import secrets
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def parse_env(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def write_env(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _mask_key(value: str) -> str:
    s = str(value)
    if len(s) <= 10:
        return "***"
    return f"{s[:4]}...{s[-4:]}"


def set_var(lines: list[str], key: str, value: str) -> list[str]:
    out: list[str] = []
    found = False
    prefix = f"{key}="
    for line in lines:
        if line.startswith(prefix):
            out.append(f"{key}={value}")
            found = True
        else:
            out.append(line)
    if not found:
        out.append(f"{key}={value}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate/update Assyntrax API keys in env file.")
    ap.add_argument("--env-file", type=str, default="website-ui/.env.local")
    ap.add_argument("--create", type=int, default=1, help="How many keys to create.")
    ap.add_argument("--show-current", action="store_true")
    args = ap.parse_args()

    env_path = ROOT / str(args.env_file)
    lines = parse_env(env_path)
    current = ""
    for line in lines:
        if line.startswith("ASSYNTRAX_API_KEYS="):
            current = line.split("=", 1)[1].strip()
            break
    current_keys = [x.strip() for x in current.split(",") if x.strip()]

    new_keys = [secrets.token_urlsafe(24) for _ in range(max(1, int(args.create)))]
    merged = current_keys + new_keys

    lines = set_var(lines, "ASSYNTRAX_API_KEYS", ",".join(merged))
    write_env(env_path, lines)

    print(
        {
            "status": "ok",
            "env_file": str(env_path),
            "n_total_keys": len(merged),
            "n_new_keys": len(new_keys),
        }
    )
    if args.show_current:
        print({"current_keys_masked": [_mask_key(k) for k in merged]})


if __name__ == "__main__":
    main()
