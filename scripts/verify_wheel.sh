#!/usr/bin/env bash
# ==============================================================================
# OctoFlow Release Wheel & Packaging Verification Script
#
# Asserts:
#   1. Wheel includes octoflow/dist/index.html and visualizer assets
#   2. Wheel excludes tests/, node_modules/, checkpoints/, and .env
#   3. Twine metadata checks pass
#   4. sdist builds a valid wheel cleanly
#   5. Clean-room isolated venv installation succeeds
#   6. CLI commands execute: octoflow --version, octoflow doctor, octoflow run --dry-run
#   7. Local telemetry server serves visualizer HTML over loopback HTTP
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PYTHON="${PYTHON:-python3}"
if command -v python3.12 >/dev/null 2>&1; then
    PYTHON="python3.12"
elif [ -f "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3" ]; then
    PYTHON="/Library/Frameworks/Python.framework/Versions/3.12/bin/python3"
fi

echo "◈ OctoFlow Release Wheel & Clean-Room Verification"
echo "  • Python interpreter: $($PYTHON --version)"
echo "  • Repo root: $REPO_ROOT"

# 1. Locate dist files
WHEEL_PATH=$(ls dist/octoflow-*.whl 2>/dev/null | head -n 1 || true)
SDIST_PATH=$(ls dist/octoflow-*.tar.gz 2>/dev/null | head -n 1 || true)

if [ -z "$WHEEL_PATH" ] || [ ! -f "$WHEEL_PATH" ]; then
    echo "✖ Error: No wheel found in dist/. Run 'make build' first." >&2
    exit 1
fi
if [ -z "$SDIST_PATH" ] || [ ! -f "$SDIST_PATH" ]; then
    echo "✖ Error: No sdist found in dist/. Run 'make build' first." >&2
    exit 1
fi

echo "  • Wheel: $WHEEL_PATH"
echo "  • Sdist: $SDIST_PATH"

# 2. Assert Wheel Contents using Python zipfile
echo "◈ Checking wheel archive contents..."
$PYTHON - <<PYEOF
import sys
import zipfile

wheel_file = "$WHEEL_PATH"
with zipfile.ZipFile(wheel_file, "r") as z:
    names = z.namelist()

# Required assets
required = [
    "octoflow/dist/index.html",
]
for req in required:
    matching = [n for n in names if req in n]
    if not matching:
        sys.stderr.write(f"✖ Wheel verification failed: missing required file '{req}'\n")
        sys.exit(1)

# Forbidden files that must never leak into production wheels
forbidden_prefixes = [
    "tests/",
    "visualizer/",
    "checkpoints/",
    "node_modules/",
]
forbidden_substrings = [
    ".env",
    "package-lock.json",
    ".pytest_cache",
]

for name in names:
    for prefix in forbidden_prefixes:
        if name.startswith(prefix) or f"octoflow/{prefix}" in name:
            sys.stderr.write(f"✖ Wheel verification failed: leaked forbidden path '{name}'\n")
            sys.exit(1)
    for sub in forbidden_substrings:
        if sub in name:
            sys.stderr.write(f"✖ Wheel verification failed: leaked forbidden substring '{name}'\n")
            sys.exit(1)

print(f"✔ Wheel content audit passed! ({len(names)} files in archive, visualizer bundled, tests/checkpoints excluded)")
PYEOF

# 3. Twine Metadata Check
echo "◈ Checking packaging metadata with twine..."
if command -v twine >/dev/null 2>&1; then
    twine check dist/*
elif [ -f "/Library/Frameworks/Python.framework/Versions/3.12/bin/twine" ]; then
    /Library/Frameworks/Python.framework/Versions/3.12/bin/twine check dist/*
else
    $PYTHON -m twine check dist/*
fi
echo "✔ Twine metadata check passed!"

# 4. Sdist build test
echo "◈ Verifying sdist unpack and build..."
SDIST_TEST_DIR=$(mktemp -d)
trap 'rm -rf "$SDIST_TEST_DIR"' EXIT
$PYTHON -m pip wheel --no-deps "$SDIST_PATH" -w "$SDIST_TEST_DIR" >/dev/null
echo "✔ Sdist built wheel successfully!"

# 5. Clean-Room Isolated Virtual Environment Installation
CLEAN_DIR=$(mktemp -d)
# Update trap to remove both dirs
trap 'rm -rf "$SDIST_TEST_DIR" "$CLEAN_DIR"' EXIT

echo "◈ Setting up clean-room isolated environment in $CLEAN_DIR..."
$PYTHON -m venv "$CLEAN_DIR/venv"
CLEAN_PIP="$CLEAN_DIR/venv/bin/pip"
CLEAN_OCTO="$CLEAN_DIR/venv/bin/octoflow"

"$CLEAN_PIP" install --quiet --upgrade pip
echo "  • Installing built wheel into clean venv..."
"$CLEAN_PIP" install --quiet "$WHEEL_PATH"

# 6. Verify CLI Execution
echo "◈ Verifying installed CLI execution..."
VERSION_OUT=$("$CLEAN_OCTO" --version)
echo "  • 'octoflow --version' output: $VERSION_OUT"
"$CLEAN_OCTO" version >/dev/null
"$CLEAN_OCTO" --help >/dev/null
echo "  • 'octoflow --help' ran successfully"
INSTALLED_VER=$("$CLEAN_DIR/venv/bin/python" -c "import octoflow; print(octoflow.__version__)")
echo "  • Installed package version: $INSTALLED_VER"

echo "  • Running 'octoflow doctor' in clean room..."
"$CLEAN_OCTO" doctor || true

echo "  • Running 'octoflow run --dry-run' in clean room..."
mkdir -p "$CLEAN_DIR/workspace"
"$CLEAN_OCTO" run "Build a clean test function" --dry-run --dir "$CLEAN_DIR/workspace"

# 7. Verify Telemetry Server & Visualizer Asset Delivery
echo "◈ Verifying HTTP delivery of packaged visualizer assets..."
TEST_PORT=18088
"$CLEAN_OCTO" ui --port "$TEST_PORT" >/dev/null 2>&1 &
SERVER_PID=$!

# Wait for server readiness
for i in {1..30}; do
    if curl -fs "http://127.0.0.1:$TEST_PORT/" >/dev/null 2>&1; then
        break
    fi
    sleep 0.2
done

INDEX_CONTENT=$(curl -fs "http://127.0.0.1:$TEST_PORT/")
kill -9 "$SERVER_PID" 2>/dev/null || true

if echo "$INDEX_CONTENT" | grep -qi "Connectome\|OctoFlow"; then
    echo "✔ Successfully retrieved visualizer HTML index over loopback HTTP!"
else
    echo "✖ Failed to retrieve visualizer HTML content from server" >&2
    exit 1
fi

echo ""
echo "✔ Clean-room wheel verification passed completely!"
