#!/usr/bin/env bash
# ==============================================================================
# OctoFlow GitHub Labels Synchronization Script
#
# Reads .github/labels.yml and synchronizes repository labels using the GitHub CLI.
# Requires 'gh' to be installed and authenticated ('gh auth status').
# Otherwise, explains what it would do and exits cleanly.
#
# Usage:
#   bash scripts/sync_labels.sh [--dry-run]
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABELS_FILE="${REPO_ROOT}/.github/labels.yml"

DRY_RUN=false
for arg in "$@"; do
    if [ "$arg" == "--dry-run" ]; then
        DRY_RUN=true
    fi
done

echo "◈ OctoFlow Label Synchronization Utility"
echo "  • Labels file: ${LABELS_FILE}"

if [ ! -f "$LABELS_FILE" ]; then
    echo "✖ Error: Labels file not found at ${LABELS_FILE}" >&2
    exit 1
fi

# Check for gh CLI
if ! command -v gh >/dev/null 2>&1; then
    echo "● Notice: GitHub CLI ('gh') is not installed on PATH."
    echo "  To sync labels to your remote repository:"
    echo "    1. Install gh: brew install gh (macOS) or see https://cli.github.com"
    echo "    2. Run 'gh auth login' to authenticate"
    echo "    3. Run 'bash scripts/sync_labels.sh'"
    echo "✔ Dry-run simulated: No remote changes made."
    exit 0
fi

# Check gh authentication
if ! gh auth status >/dev/null 2>&1; then
    echo "● Notice: GitHub CLI ('gh') is installed but not currently authenticated."
    echo "  To authenticate with GitHub:"
    echo "    gh auth login"
    echo "✔ Dry-run simulated: No remote changes made."
    exit 0
fi

echo "✔ Authenticated with GitHub CLI."

# Parse labels.yml using python and sync
python3 - << 'PYEOF'
import os
import subprocess
import sys
import yaml

labels_path = os.environ.get("LABELS_FILE", ".github/labels.yml")
dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

with open(labels_path, "r", encoding="utf-8") as f:
    labels = yaml.safe_load(f)

print(f"◈ Synchronizing {len(labels)} repository labels...")

for label in labels:
    name = label.get("name")
    color = str(label.get("color", "cccccc")).lstrip("#")
    desc = label.get("description", "")

    if dry_run:
        print(f"  [DRY-RUN] gh label create \"{name}\" --color \"{color}\" --description \"{desc}\" --force")
    else:
        cmd = ["gh", "label", "create", name, "--color", color, "--description", desc, "--force"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  ✔ Synced: {name} (#{color})")
        else:
            print(f"  ✖ Failed: {name}: {res.stderr.strip()}")

print("✔ Label synchronization complete.")
PYEOF

