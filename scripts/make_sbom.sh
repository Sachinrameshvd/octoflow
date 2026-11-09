#!/usr/bin/env bash
# Software Bill of Materials (SBOM) Generation Script for OctoFlow
# Generates CycloneDX v1.5 JSON for Python and NPM into dist-artifacts/ (untracked)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ARTIFACTS_DIR="${WORKSPACE_ROOT}/dist-artifacts"

echo "◈ Generating OctoFlow CycloneDX v1.5 Software Bill of Materials..."
mkdir -p "${ARTIFACTS_DIR}"

PYTHON_BIN=""
if [ -f "${WORKSPACE_ROOT}/.venv/bin/python" ]; then
    PYTHON_BIN="${WORKSPACE_ROOT}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "Error: Python 3 not found." >&2
    exit 1
fi

"${PYTHON_BIN}" "${SCRIPT_DIR}/generate_sbom.py"

if [ ! -f "${ARTIFACTS_DIR}/bom-python.json" ]; then
    echo "Error: Failed to generate Python SBOM at ${ARTIFACTS_DIR}/bom-python.json" >&2
    exit 1
fi

if [ ! -f "${ARTIFACTS_DIR}/bom-npm.json" ]; then
    echo "Error: Failed to generate NPM SBOM at ${ARTIFACTS_DIR}/bom-npm.json" >&2
    exit 1
fi

echo "✔ Successfully generated CycloneDX SBOMs in dist-artifacts/:"
ls -lh "${ARTIFACTS_DIR}"/*.json
