#!/usr/bin/env bash
set -euo pipefail

REMOTE="${1:-origin}"
BRANCH="${2:-main}"

echo "[sync] canonical remote: ${REMOTE}/${BRANCH}"
git fetch "${REMOTE}" --prune
git reset --hard "${REMOTE}/${BRANCH}"
git clean -fd

echo "[sync] local now matches ${REMOTE}/${BRANCH}"
git status -sb
git rev-parse --short HEAD
