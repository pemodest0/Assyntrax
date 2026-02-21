#!/usr/bin/env bash
set -euo pipefail

# Safe organizer:
# - archives smoke outputs under results/_archive
# - archives loose legacy files at results root
# - archives known temporary file in website-ui
#
# Default is dry-run. Use --apply to execute.

apply=0
if [[ "${1:-}" == "--apply" ]]; then
  apply=1
fi

stamp="$(date +%Y%m%d_%H%M%S)"
archive_base="results/_archive/cleanup_${stamp}"
smoke_dst="${archive_base}/smoke_runs"
legacy_dst="${archive_base}/legacy_root_files"
ui_dst="website-ui/_archive"

smoke_dirs=()
while IFS= read -r d; do
  [[ -n "$d" ]] && smoke_dirs+=("$d")
done < <(find results -maxdepth 1 -type d -name '_smoke*' | sort)

legacy_files=()
for f in \
  results/summary_kmeans.csv \
  results/summary_hdbscan.csv \
  results/report_duffing.md \
  results/report_duffing.pdf
do
  [[ -e "$f" ]] && legacy_files+=("$f")
done

ui_tmp=()
[[ -e "website-ui/tmp_fork_child.js" ]] && ui_tmp+=("website-ui/tmp_fork_child.js")

echo "== Workspace Organizer =="
echo "mode: $([[ $apply -eq 1 ]] && echo APPLY || echo DRY-RUN)"
echo "archive base: ${archive_base}"
echo
echo "[smoke dirs]"
printf '%s\n' "${smoke_dirs[@]:-<none>}"
echo
echo "[legacy files]"
printf '%s\n' "${legacy_files[@]:-<none>}"
echo
echo "[ui temp]"
printf '%s\n' "${ui_tmp[@]:-<none>}"

if [[ $apply -ne 1 ]]; then
  echo
  echo "No changes made. Re-run with --apply."
  exit 0
fi

mkdir -p "$smoke_dst" "$legacy_dst" "$ui_dst"

for d in "${smoke_dirs[@]:-}"; do
  [[ -d "$d" ]] && mv "$d" "$smoke_dst/"
done

for f in "${legacy_files[@]:-}"; do
  [[ -e "$f" ]] && mv "$f" "$legacy_dst/"
done

for f in "${ui_tmp[@]:-}"; do
  [[ -e "$f" ]] && mv "$f" "$ui_dst/"
done

{
  echo "cleanup_timestamp=${stamp}"
  echo "archive_base=${archive_base}"
  echo
  echo "[smoke_runs]"
  find "$smoke_dst" -maxdepth 1 -mindepth 1 -type d -print | sed "s#^${smoke_dst}/##" | sort
  echo
  echo "[legacy_root_files]"
  find "$legacy_dst" -maxdepth 1 -mindepth 1 -type f -print | sed "s#^${legacy_dst}/##" | sort
} > "${archive_base}/MANIFEST.txt"

echo "${archive_base}" > "results/_archive/LATEST_CLEANUP.txt"
echo
echo "Done."
echo "Manifest: ${archive_base}/MANIFEST.txt"
