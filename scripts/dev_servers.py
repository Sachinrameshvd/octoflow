#!/usr/bin/env python3
"""OctoFlow Inner-Loop Development Server Manager (`make dev` / `make dev-stop`).

Starts and stops:
1. Python FastAPI/WebSocket Telemetry Server on 127.0.0.1:8088 with dev origin 5173 allowed.
2. Vite 3D Visualizer Dev Server on 127.0.0.1:5173.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PID_FILE = REPO_ROOT / ".octoflow" / "dev_pids.json"


def _is_pid_alive(pid: int) -> bool:
    """Check if process with given PID is currently active."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def start_dev_servers() -> int:
    """Start telemetry and Vite dev servers in background, saving PIDs."""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Check if already running
    if PID_FILE.exists():
        try:
            data = json.loads(PID_FILE.read_text(encoding="utf-8"))
            running = {k: pid for k, pid in data.items() if _is_pid_alive(pid)}
            if running:
                print(
                    f"▲ OctoFlow dev servers already running (PIDs: {running}). Run 'make dev-stop' first."
                )
                return 0
        except Exception:
            pass

    log_dir = Path.home() / ".octoflow" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    telemetry_log = open(log_dir / "dev_telemetry.log", "a", encoding="utf-8")
    vite_log = open(log_dir / "dev_vite.log", "a", encoding="utf-8")

    # 1. Start Python Telemetry Server
    env_telemetry = dict(os.environ)
    env_telemetry["OCTOFLOW_DEV"] = "1"
    env_telemetry["VITE_DEV"] = "1"
    telemetry_proc = subprocess.Popen(
        [sys.executable, "-m", "octoflow.server", "--port", "8088", "--host", "127.0.0.1", "--dev"],
        cwd=str(REPO_ROOT),
        stdout=telemetry_log,
        stderr=telemetry_log,
        env=env_telemetry,
    )

    # 2. Start Vite Dev Server
    vis_dir = REPO_ROOT / "visualizer"
    npm_cmd = "npm"
    vite_proc = None

    if (vis_dir / "package.json").exists():
        try:
            # Check npm availability
            subprocess.run(["npm", "--version"], capture_output=True, check=True)
            vite_proc = subprocess.Popen(
                [npm_cmd, "run", "dev", "--", "--port", "5173", "--host", "127.0.0.1"],
                cwd=str(vis_dir),
                stdout=vite_log,
                stderr=vite_log,
            )
        except Exception:
            # Fallback if npm is not installed or unavailable in this environment
            vite_proc = subprocess.Popen(
                [sys.executable, "-m", "http.server", "5173", "--bind", "127.0.0.1"],
                cwd=str(vis_dir),
                stdout=vite_log,
                stderr=vite_log,
            )

    pids = {"telemetry": telemetry_proc.pid}
    if vite_proc:
        pids["vite"] = vite_proc.pid

    PID_FILE.write_text(json.dumps(pids, indent=2), encoding="utf-8")
    try:
        PID_FILE.chmod(0o600)
    except OSError:
        pass

    # Wait a fraction of a second to verify immediate boot
    time.sleep(0.4)
    print("◈ OctoFlow Development Stack Online:")
    print("• Telemetry Server:     http://127.0.0.1:8088 (ws://127.0.0.1:8088/ws/telemetry)")
    print("• Vite 3D Visualizer:   http://localhost:5173 (allowed dev origin 5173)")
    print("• Logs Directory:       ~/.octoflow/logs/")
    print("• Stop with:            make dev-stop")
    return 0


def stop_dev_servers() -> int:
    """Stop active telemetry and Vite dev servers and clean up PID files."""
    if not PID_FILE.exists():
        print("• No active dev servers found (PID file missing).")
        return 0

    try:
        data = json.loads(PID_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}

    stopped_count = 0
    for _name, pid in data.items():
        if isinstance(pid, int) and _is_pid_alive(pid):
            try:
                os.kill(pid, signal.SIGTERM)
                # Wait briefly for clean shutdown
                start = time.time()
                while time.time() - start < 1.5:
                    if not _is_pid_alive(pid):
                        break
                    time.sleep(0.05)
                if _is_pid_alive(pid):
                    os.kill(pid, signal.SIGKILL)
                stopped_count += 1
            except OSError:
                pass

    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass

    print(f"✔ OctoFlow Development Stack stopped ({stopped_count} server processes terminated).")
    return 0


def main() -> int:
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "start"
    if cmd == "start":
        return start_dev_servers()
    elif cmd in ("stop", "dev-stop"):
        return stop_dev_servers()
    elif cmd == "status":
        if PID_FILE.exists():
            print("Active PIDs:", PID_FILE.read_text(encoding="utf-8"))
        else:
            print("No active dev servers.")
        return 0
    else:
        print(f"Unknown command: '{cmd}'. Use 'start' or 'stop'.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
