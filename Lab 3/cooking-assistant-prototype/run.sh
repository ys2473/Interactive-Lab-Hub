#!/usr/bin/env bash
set -euo pipefail

PROTOTYPE_DIR="$(cd "$(dirname "$0")" && pwd)"
LAB_DIR="$(cd "$PROTOTYPE_DIR/.." && pwd)"

if systemctl is-active --quiet piscreen.service; then
  echo "The Lab 2 piscreen.service is using the display and buttons."
  echo "Stop it first with: sudo systemctl stop piscreen.service --now"
  exit 1
fi

source "$LAB_DIR/.venv/bin/activate"
cd "$PROTOTYPE_DIR"
exec python3 app.py "$@"
