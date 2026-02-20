#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-$HOME/A-firma}"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

mkdir -p "$SYSTEMD_USER_DIR"
mkdir -p "$REPO/results/event_study_sectors/logs"

cp "$REPO/scripts/ops/systemd/assyntrax-sector-alerts.service" "$SYSTEMD_USER_DIR/"
cp "$REPO/scripts/ops/systemd/assyntrax-sector-alerts.timer" "$SYSTEMD_USER_DIR/"

systemctl --user daemon-reload
systemctl --user enable assyntrax-sector-alerts.timer
systemctl --user restart assyntrax-sector-alerts.timer

echo "[ok] systemd timer enabled: assyntrax-sector-alerts.timer"
echo "check status: systemctl --user status assyntrax-sector-alerts.timer"
echo "check logs:   tail -f $REPO/results/event_study_sectors/logs/systemd.log"

