#!/usr/bin/env bash
# Start OCTOFLOW Premium Showcase on Port 5174
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$DIR"

echo "=========================================================="
echo "  OCTOFLOW — Premium Cephalopod Project Showcase"
echo "  URL: http://localhost:5174"
echo "=========================================================="

./node_modules/.bin/vite --port 5174 --host 0.0.0.0

