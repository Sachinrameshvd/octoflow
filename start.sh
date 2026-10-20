#!/bin/bash
# OctopusBrain: Launch Live Cognitive Telemetry Bridge & 3D Web Visualizer

# 1. Clean up any lingering processes on ports 8765 or 5173
lsof -ti:8765 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

echo "================================================================================"
echo "• Starting OctopusBrain Live Cognitive Bridge & 3D Web Visualizer..."
echo "================================================================================"

# 2. Launch live bridge in background and track its PID
if [ -f ".venv/bin/python3" ]; then
  PYTHON_EXEC=".venv/bin/python3"
elif [ -f ".venv/bin/python" ]; then
  PYTHON_EXEC=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_EXEC="python3"
else
  PYTHON_EXEC="python"
fi

PYTHONPATH=. "$PYTHON_EXEC" experiments/live_bridge.py &
BRIDGE_PID=$!

# 3. Clean exit trap: When user presses Ctrl+C, shut down the bridge cleanly
cleanup() {
    echo -e "\n--> Shutting down Live Cognitive Bridge (PID: $BRIDGE_PID)..."
    kill -9 $BRIDGE_PID 2>/dev/null
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# 4. Launch Vite 3D Visualizer in foreground
cd visualizer && npm run dev
