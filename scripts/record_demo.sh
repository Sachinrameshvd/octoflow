#!/usr/bin/env bash
# ==============================================================================
# OctoFlow Demo Cast Recorder & Asset Generator
#
# Generates:
#   docs/assets/demo.cast (Asciinema v2 format, <= 90s duration)
#   docs/assets/demo.gif  (via agg if installed)
#   docs/assets/demo.svg  (via svg-term if installed)
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON="${PYTHON:-.venv/bin/python}"
if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

echo "◈ Recording OctoFlow Quickstart Demo Cast..."
"$PYTHON" scripts/record_demo_session.py

CAST_FILE="docs/assets/demo.cast"
GIF_FILE="docs/assets/demo.gif"
SVG_FILE="docs/assets/demo.svg"

# Check for agg (Asciinema GIF generator)
if command -v agg >/dev/null 2>&1; then
    echo "◈ Compiling .cast to .gif with agg..."
    agg --theme monokai --speed 1.2 --font-size 14 "$CAST_FILE" "$GIF_FILE"
    echo "✔ Created GIF demo: $GIF_FILE"
else
    echo "ℹ agg not found. To generate animated GIF from cast:"
    echo "    brew install agg"
    echo "    agg --theme monokai --speed 1.2 --font-size 14 $CAST_FILE $GIF_FILE"
fi

# Check for svg-term
if command -v svg-term >/dev/null 2>&1; then
    echo "◈ Compiling .cast to .svg with svg-term..."
    svg-term --in "$CAST_FILE" --out "$SVG_FILE" --window --width 110 --height 32
    echo "✔ Created SVG demo: $SVG_FILE"
else
    echo "ℹ svg-term not found. To generate animated SVG from cast:"
    echo "    npm install -g svg-term-cli"
    echo "    svg-term --in $CAST_FILE --out $SVG_FILE --window --width 110 --height 32"
fi

echo "✔ Demo recording completed: $CAST_FILE"

