#!/bin/bash
# Open-Imagebox start script (manual + service)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
WEB_PORT="${OPEN_IMAGEBOX_WEB_PORT:-8080}"

cd "$PROJECT_DIR"
source "$PROJECT_DIR/venv/bin/activate"

# Start Chromium kiosk in background (if available and GUI session exists)
if [ -n "${DISPLAY:-}" ]; then
    CHROMIUM_BIN="$(command -v chromium-browser || command -v chromium || true)"
    if [ -n "$CHROMIUM_BIN" ]; then
        (
            sleep 8
            "$CHROMIUM_BIN" \
                --kiosk \
                --new-window \
                --noerrdialogs \
                --disable-session-crashed-bubble \
                --disable-infobars \
                "http://127.0.0.1:${WEB_PORT}" >/dev/null 2>&1 || true
        ) &
    fi
fi

exec python -m src.main "$@"
