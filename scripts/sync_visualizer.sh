#!/usr/bin/env bash
# ==============================================================================
# OctoFlow Visualizer Sync Script (P4.4)
#
# Builds the Three.js / Vite visualizer with typecheck, lint, and tests,
# then synchronizes distribution artifacts deterministically into octoflow/dist/.
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VISUALIZER_DIR="${REPO_ROOT}/visualizer"
TARGET_DIST="${REPO_ROOT}/octoflow/dist"

echo "================================================================"
echo "◈ Synchronizing Visualizer into octoflow/dist"
echo "◈ Source: ${VISUALIZER_DIR}"
echo "◈ Destination: ${TARGET_DIST}"
echo "================================================================"

cd "${VISUALIZER_DIR}"

# 1. Ensure node_modules exist
if [ ! -d "node_modules" ]; then
  echo "• Installing frontend dependencies via npm ci..."
  npm ci
fi

# 2. Quality Gates: Typecheck, Lint, Test
echo "• 1/4 TypeScript strict check..."
npx tsc --noEmit

echo "• 2/4 ESLint static analysis..."
npm run lint

echo "• 3/4 Vitest unit & reconnect test suite..."
npm run test

echo "• 4/4 Vite production build..."
npm run build

# 3. Deterministic sync into python package
echo "• Syncing built artifacts into ${TARGET_DIST}..."
mkdir -p "${TARGET_DIST}"

# Clean old generated js/css assets in target to avoid stale chunk accumulation
if [ -d "${TARGET_DIST}/assets" ]; then
  rm -rf "${TARGET_DIST}/assets"
fi

cp -R dist/* "${TARGET_DIST}/"

# 4. Summary
TOTAL_FILES=$(find "${TARGET_DIST}" -type f | wc -l | tr -d ' ')
TOTAL_SIZE=$(du -sh "${TARGET_DIST}" | cut -f1)

echo "✔ Visualizer synced successfully:"
echo "    Total files: ${TOTAL_FILES}"
echo "    Total size:  ${TOTAL_SIZE}"
echo "================================================================"
