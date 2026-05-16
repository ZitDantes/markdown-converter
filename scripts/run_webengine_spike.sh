#!/usr/bin/env bash
# Lance le spike PLO-44 (WebEngine + QWebChannel).
# Usage : ./scripts/run_webengine_spike.sh [file|qrc]
set -euo pipefail
cd "$(dirname "$0")/.."
LOADER="${1:-file}"
export MARKDOWN_CONVERTER_UI=web-spike
export MARKDOWN_CONVERTER_SPIKE_LOADER="$LOADER"
exec python3 main.py
