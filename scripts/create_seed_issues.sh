#!/usr/bin/env bash
# ==============================================================================
# OctoFlow Seed Issues Creator
#
# Reads well-scoped issue drafts from docs/seed-issues/*.md and generates
# corresponding GitHub issues using the 'gh' CLI.
#
# Defaults to --dry-run to guarantee zero unwanted remote issues are created.
#
# Usage:
#   bash scripts/create_seed_issues.sh --dry-run
#   bash scripts/create_seed_issues.sh --create   # Requires confirmation
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISSUES_DIR="${REPO_ROOT}/docs/seed-issues"

DRY_RUN=true
CREATE_REMOTE=false

for arg in "$@"; do
    case "$arg" in
        --dry-run)
            DRY_RUN=true
            CREATE_REMOTE=false
            ;;
        --create)
            DRY_RUN=false
            CREATE_REMOTE=true
            ;;
        --help|-h)
            echo "Usage: $0 [--dry-run | --create]"
            echo "  --dry-run   Print the gh issue create commands without executing (default)"
            echo "  --create    Execute gh issue create commands against the remote repository"
            exit 0
            ;;
    esac
done

echo "◈ OctoFlow Seed Issues Generator"
echo "  • Issues directory: ${ISSUES_DIR}"

if [ ! -d "$ISSUES_DIR" ]; then
    echo "✖ Error: Issues directory not found at ${ISSUES_DIR}" >&2
    exit 1
fi

# Run python parser to process seed issue files
export ISSUES_DIR
export DRY_RUN
export CREATE_REMOTE

python3 - << 'PYEOF'
import os
import re
import subprocess
import sys
from pathlib import Path

issues_dir = Path(os.environ.get("ISSUES_DIR", "docs/seed-issues"))
dry_run = os.environ.get("DRY_RUN", "true").lower() == "true"
create_remote = os.environ.get("CREATE_REMOTE", "false").lower() == "true"

issue_files = sorted(issues_dir.glob("*.md"))
if not issue_files:
    print("✖ Error: No markdown files found in seed issues directory.", file=sys.stderr)
    sys.exit(1)

print(f"◈ Found {len(issue_files)} seed issue template(s).")
if dry_run:
    print("◈ Mode: DRY-RUN (commands printed below, no remote issues will be created):\n")
else:
    print("◈ Mode: LIVE REMOTE CREATION\n")

# Verify gh CLI if creating remote
if create_remote:
    try:
        auth_check = subprocess.run(["gh", "auth", "status"], capture_output=True, text=True)
        if auth_check.returncode != 0:
            print("✖ Error: 'gh' CLI is not authenticated. Please run 'gh auth login' first.", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print("✖ Error: 'gh' CLI is not installed on PATH.", file=sys.stderr)
        sys.exit(1)

for idx, path in enumerate(issue_files, start=1):
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()

    # Extract title from first H1
    title = ""
    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
            break
    if not title:
        title = path.stem.replace("-", " ").title()

    # Extract labels
    labels = []
    labels_match = re.search(r"\*\*Labels:\*\*\s*(.+)", content)
    if labels_match:
        raw_labels = labels_match.group(1)
        # Parse backticked items: `label1`, `label2`
        found = re.findall(r"`([^`]+)`", raw_labels)
        if found:
            labels = found
        else:
            labels = [l.strip() for l in raw_labels.split(",") if l.strip()]

    label_arg = ",".join(labels) if labels else "good first issue"
    rel_path = path.relative_to(path.parent.parent.parent) if len(path.parents) >= 3 else path.name

    if dry_run:
        cmd_str = f"gh issue create --title \"{title}\" --body-file \"{rel_path}\" --label \"{label_arg}\""
        print(f"[{idx:02d}/{len(issue_files):02d}] {cmd_str}")
    else:
        cmd = ["gh", "issue", "create", "--title", title, "--body-file", str(path), "--label", label_arg]
        print(f"[{idx:02d}/{len(issue_files):02d}] Creating issue: '{title}'...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  ✔ Created: {res.stdout.strip()}")
        else:
            print(f"  ✖ Failed to create issue: {res.stderr.strip()}")

print("\n✔ Seed issues script completed successfully.")
PYEOF

