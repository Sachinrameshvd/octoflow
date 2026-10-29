"""ProjectIgniter: Autonomous Phase 4 Live Ignition & Runtime Environment Server.

Auto-provisions, boots, and monitors live web applications, backend APIs,
and AI/ML training/inference pipelines directly from synthesized project deliverables.
Generates interactive test links, ensures reliable TCP/HTTP readiness detection,
captures logs to <workspace>/.octoflow/ignition/<service>.log, tracks PIDs/PGIDs in
~/.octoflow/runs/<id>/ignition.json, and guarantees clean process group shutdown.
"""

import atexit
import asyncio
import http.client
import json
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, Field

from octoflow.encoder import CodeSensoryEncoder
from octoflow.tools import ToolResult
from octoflow.logging_config import get_logger
from octoflow.checkpoint import get_runs_dir

logger = get_logger("ignition")


# -----------------------------------------------------------------------------
# Process Group Management & Global Signal Safety
# -----------------------------------------------------------------------------

_ACTIVE_IGNITERS: List["ProjectIgniter"] = []
_ACTIVE_PGIDS: Set[int] = set()
_SIGNALS_INSTALLED = False


def kill_process_group(pgid: int, grace_seconds: float = 3.0) -> bool:
    """Terminate a process group with SIGTERM, 3s grace period, then SIGKILL.
    
    Guarantees no orphaned child processes remain after shutdown or Ctrl-C.
    """
    if pgid <= 0:
        return True
    if not hasattr(os, "killpg"):
        return True

    # 1. Send SIGTERM to process group
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return True
    except Exception as e:
        logger.debug("Failed sending SIGTERM to pgid %d: %s", pgid, e)

    # 2. Wait up to grace_seconds
    deadline = time.time() + grace_seconds
    while time.time() < deadline:
        try:
            os.killpg(pgid, 0)
            time.sleep(0.1)
        except ProcessLookupError:
            return True
        except Exception:
            break

    # 3. Escalate to SIGKILL if still alive
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        return True
    except Exception as e:
        logger.debug("Failed sending SIGKILL to pgid %d: %s", pgid, e)

    return True


def is_pid_alive(pid: int) -> bool:
    """Check if a given PID is currently active and not a dead zombie."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except Exception:
        return False

    # Check for in-process children to reap zombies
    for ign in _ACTIVE_IGNITERS:
        for p, _, _ in ign.active_processes:
            if p.pid == pid:
                if p.poll() is not None:
                    return False

    # If on macOS/Linux, verify process is not a zombie via ps
    try:
        res = subprocess.run(
            ["ps", "-o", "stat=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=1.0,
        )
        if res.returncode == 0:
            stat = res.stdout.strip()
            if stat.startswith("Z"):
                return False
        else:
            return False
    except Exception:
        pass

    return True


def get_safe_pgid(pid: int) -> int:
    """Safely obtain process group ID for pid without crashing if process exited."""
    if pid <= 0:
        return pid
    try:
        return os.getpgid(pid) if hasattr(os, "getpgid") else pid
    except Exception:
        return pid


def _install_signal_handlers():
    """Install SIGINT and SIGTERM handlers to cleanly terminate spawned process groups."""
    global _SIGNALS_INSTALLED
    if _SIGNALS_INSTALLED:
        return
    if threading.current_thread() is not threading.main_thread():
        return
    try:
        orig_sigint = signal.getsignal(signal.SIGINT)
        orig_sigterm = signal.getsignal(signal.SIGTERM)

        def _signal_handler(signum, frame):
            for ign in list(_ACTIVE_IGNITERS):
                try:
                    ign.terminate_all()
                except Exception:
                    pass
            for pgid in list(_ACTIVE_PGIDS):
                kill_process_group(pgid, grace_seconds=1.5)

            if signum == signal.SIGINT:
                if callable(orig_sigint) and orig_sigint not in (signal.SIG_IGN, signal.SIG_DFL, _signal_handler):
                    orig_sigint(signum, frame)
                else:
                    raise KeyboardInterrupt()
            elif signum == signal.SIGTERM:
                if callable(orig_sigterm) and orig_sigterm not in (signal.SIG_IGN, signal.SIG_DFL, _signal_handler):
                    orig_sigterm(signum, frame)
                else:
                    sys.exit(128 + signal.SIGTERM)

        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
        _SIGNALS_INSTALLED = True
    except Exception as e:
        logger.debug("Failed installing ignition signal handlers: %s", e)


def _cleanup_atexit():
    for ign in list(_ACTIVE_IGNITERS):
        try:
            ign.terminate_all()
        except Exception:
            pass
    for pgid in list(_ACTIVE_PGIDS):
        kill_process_group(pgid, grace_seconds=1.5)


atexit.register(_cleanup_atexit)


# -----------------------------------------------------------------------------
# Port Discovery & Readiness Verification
# -----------------------------------------------------------------------------

def find_free_port(start_port: int, max_attempts: int = 50) -> int:
    """Find the next available unallocated port bound to 127.0.0.1."""
    for p in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", p))
                return p
        except OSError:
            continue
    raise RuntimeError(f"Unable to find available port in range {start_port}-{start_port + max_attempts}")


def is_port_listening(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    """Check if a service is actively accepting TCP connections on a given port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception as e:
        logger.debug("Port check probe failed for %s:%s: %s", host, port, e)
        return False


def check_http_ready(host: str, port: int, path: str = "/", timeout: float = 1.0) -> bool:
    """Send an HTTP GET request to verify that the HTTP server is actively answering."""
    try:
        conn = http.client.HTTPConnection(host, port, timeout=timeout)
        conn.request("GET", path)
        resp = conn.getresponse()
        status = resp.status
        conn.close()
        # Any valid HTTP response indicates the server is mounted and responding
        return status < 500 or status in (500, 501, 502, 503)
    except Exception:
        return False


def get_log_tail(log_path: Optional[Path], max_lines: int = 20) -> str:
    """Retrieve the last max_lines lines from a service log file."""
    if not log_path or not log_path.exists():
        return ""
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace")
        lines = [line for line in text.splitlines() if line.strip()]
        tail = lines[-max_lines:] if len(lines) > max_lines else lines
        return "\n".join(tail)
    except Exception as e:
        logger.debug("Failed reading log tail from %s: %s", log_path, e)
        return ""


def wait_for_service_readiness(
    port: int,
    host: str = "127.0.0.1",
    is_http: bool = True,
    timeout: float = 30.0,
    proc: Optional[subprocess.Popen] = None,
    log_file: Optional[Path] = None,
) -> Tuple[bool, str]:
    """Poll TCP port and HTTP GET until ready or timeout is exceeded.
    
    Returns (is_ready, last_20_log_lines). If the process terminates prematurely,
    returns immediately without waiting the full timeout.
    """
    t_end = time.time() + timeout
    while time.time() < t_end:
        # Check if process terminated prematurely
        if proc is not None and proc.poll() is not None:
            tail = get_log_tail(log_file, 20)
            return False, tail

        if is_port_listening(port, host=host):
            if not is_http:
                return True, ""
            if check_http_ready(host, port, path="/", timeout=0.8):
                return True, ""

        time.sleep(0.2)

    tail = get_log_tail(log_file, 20)
    return False, tail


def wait_for_service(port: int, host: str = "127.0.0.1", timeout: float = 6.0) -> bool:
    """Backward-compatible TCP poll until port responds or timeout expires."""
    is_ready, _ = wait_for_service_readiness(port, host=host, is_http=False, timeout=timeout)
    return is_ready


def open_url_in_browser(url: str) -> bool:
    """Open URL in browser if session is an interactive local TTY and not SSH.
    
    Returns True if browser was successfully invoked, False otherwise.
    In non-TTY or SSH sessions, prints the URL instead.
    """
    is_ssh = bool(os.environ.get("SSH_CLIENT") or os.environ.get("SSH_TTY") or os.environ.get("SSH_CONNECTION"))
    is_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    if is_tty and not is_ssh:
        import webbrowser
        try:
            return webbrowser.open(url)
        except Exception as e:
            logger.debug("Failed opening webbrowser for %s: %s", url, e)
            print(f"Service URL: {url}")
            return False
    else:
        logger.info("Non-interactive or SSH session. Open URL in local browser: %s", url)
        print(f"Service URL: {url}")
        return False


# -----------------------------------------------------------------------------
# Data Models & Process Registry
# -----------------------------------------------------------------------------

class IgnitionServiceInfo(BaseModel):
    """Detailed metadata for a single running child service."""
    name: str
    pid: int
    pgid: int
    port: int
    url: str
    log_path: str
    status: str = "INITIALIZING"  # "READY", "FAILED", "STOPPED"
    started_at: float = Field(default_factory=time.time)


class LiveServiceManifest(BaseModel):
    """Manifest describing actively running services provisioned by ProjectIgniter."""
    service_type: str = "web_app"  # "web_app", "api_service", "aiml_training", "aiml_inference", "static_web"
    title: str = "Generated Application"
    primary_url: Optional[str] = None
    api_docs_url: Optional[str] = None
    inference_url: Optional[str] = None
    status: str = "INITIALIZING"  # "READY", "RUNNING", "FAILED", "STOPPED"
    backend_port: Optional[int] = None
    frontend_port: Optional[int] = None
    pids: List[int] = Field(default_factory=list)
    pgids: List[int] = Field(default_factory=list)
    services: List[IgnitionServiceInfo] = Field(default_factory=list)
    endpoints: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    log_tail: Optional[str] = None
    command_launched: str = ""
    run_id: Optional[str] = None


def save_ignition_registry(run_id: str, manifest: LiveServiceManifest, workspace_dir: Path) -> Path:
    """Persist ignition processes and status to ~/.octoflow/runs/<id>/ignition.json."""
    runs_dir = get_runs_dir() / run_id
    runs_dir.mkdir(parents=True, exist_ok=True)
    reg_file = runs_dir / "ignition.json"
    data = {
        "run_id": run_id,
        "workspace_dir": str(workspace_dir.resolve()),
        "status": manifest.status,
        "service_type": manifest.service_type,
        "title": manifest.title,
        "primary_url": manifest.primary_url,
        "api_docs_url": manifest.api_docs_url,
        "inference_url": manifest.inference_url,
        "backend_port": manifest.backend_port,
        "frontend_port": manifest.frontend_port,
        "pids": manifest.pids,
        "pgids": manifest.pgids,
        "services": [s.model_dump() for s in manifest.services],
        "endpoints": manifest.endpoints,
        "error_message": manifest.error_message,
        "log_tail": manifest.log_tail,
        "command_launched": manifest.command_launched,
        "updated_at": time.time(),
    }
    reg_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return reg_file


def load_ignition_registry(run_id: str) -> Optional[Dict[str, Any]]:
    """Load ignition metadata for a specific run ID."""
    reg_file = get_runs_dir() / run_id / "ignition.json"
    if reg_file.exists():
        try:
            return json.loads(reg_file.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def list_active_ignitions(workspace_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Scan all recorded ignition runs and return currently active service sets."""
    runs_dir = get_runs_dir()
    if not runs_dir.exists():
        return []

    active = []
    ws_resolved = str(workspace_dir.resolve()) if workspace_dir else None

    for run_dir in runs_dir.iterdir():
        if not run_dir.is_dir():
            continue
        reg_file = run_dir / "ignition.json"
        if not reg_file.exists():
            continue
        try:
            data = json.loads(reg_file.read_text(encoding="utf-8"))
            if ws_resolved and data.get("workspace_dir") != ws_resolved:
                continue

            if data.get("status") in ("STOPPED", "FAILED"):
                continue

            any_alive = False
            for s in data.get("services", []):
                pid = s.get("pid")
                if pid and is_pid_alive(pid):
                    any_alive = True
                else:
                    s["status"] = "STOPPED"

            if any_alive:
                active.append(data)
            else:
                data["status"] = "STOPPED"
                reg_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            continue

    active.sort(key=lambda d: d.get("updated_at", 0), reverse=True)
    return active


def get_active_ignition_manifest(workspace_dir: Optional[Path] = None) -> Optional[LiveServiceManifest]:
    """Retrieve the most recent active LiveServiceManifest for a workspace."""
    active = list_active_ignitions(workspace_dir=workspace_dir)
    if not active:
        return None
    top = active[0]
    try:
        return LiveServiceManifest(**top)
    except Exception:
        return None


def stop_ignition(
    run_id: Optional[str] = None,
    stop_all: bool = False,
    workspace_dir: Optional[Path] = None,
) -> List[int]:
    """Stop ignition processes by run_id, all, or latest. Returns list of stopped PIDs."""
    stopped_pids = []
    runs_dir = get_runs_dir()
    if not runs_dir.exists():
        return stopped_pids

    target_files = []
    if stop_all:
        for run_dir in runs_dir.iterdir():
            if run_dir.is_dir() and (run_dir / "ignition.json").exists():
                target_files.append(run_dir / "ignition.json")
    elif run_id:
        rf = runs_dir / run_id / "ignition.json"
        if rf.exists():
            target_files.append(rf)
    else:
        active = list_active_ignitions(workspace_dir=workspace_dir)
        if active:
            target_files.append(runs_dir / active[0]["run_id"] / "ignition.json")

    for reg_file in target_files:
        try:
            data = json.loads(reg_file.read_text(encoding="utf-8"))
            for s in data.get("services", []):
                pgid = s.get("pgid")
                pid = s.get("pid")
                if pgid and pgid > 0:
                    kill_process_group(pgid, grace_seconds=3.0)
                    if pid:
                        stopped_pids.append(pid)
                elif pid and pid > 0:
                    try:
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(0.3)
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    stopped_pids.append(pid)
                s["status"] = "STOPPED"
            data["status"] = "STOPPED"
            reg_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            logger.debug("Failed stopping ignition in %s: %s", reg_file, e)

    # Also terminate any matching in-memory active igniters
    for ign in list(_ACTIVE_IGNITERS):
        if stop_all or not run_id or ign.run_id == run_id:
            try:
                ign.terminate_all()
            except Exception:
                pass

    return stopped_pids


# -----------------------------------------------------------------------------
# Main ProjectIgniter Engine
# -----------------------------------------------------------------------------

class ProjectIgniter:
    """Autonomous Phase Gate 4 engine: provisions, launches, and monitors live deliverables."""

    def __init__(
        self,
        workspace_dir: Union[str, Path] = ".",
        sensory_encoder: Optional[CodeSensoryEncoder] = None,
        run_id: Optional[str] = None,
    ):
        self.workspace_dir = Path(workspace_dir).expanduser().resolve()
        self.encoder = sensory_encoder or CodeSensoryEncoder()
        self.run_id = run_id or f"ignite-{int(time.time())}-{uuid.uuid4().hex[:6]}"
        self.active_processes: List[Tuple[subprocess.Popen, Any, int]] = []  # (proc, log_fp, pgid)
        self.manifest: Optional[LiveServiceManifest] = None
        self.log_handles: List[Any] = []

        _install_signal_handlers()
        _ACTIVE_IGNITERS.append(self)
        atexit.register(self.terminate_all)

    def _get_log_dir(self) -> Path:
        log_dir = self.workspace_dir / ".octoflow" / "ignition"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    def inspect_deliverables(self) -> Dict[str, Any]:
        """Scan workspace folder topology to detect build artifacts and runnable targets."""
        ws = self.workspace_dir
        deliverables = {
            "has_node_frontend": False,
            "has_static_html": False,
            "has_python_backend": False,
            "has_fastapi": False,
            "has_aiml_train": False,
            "has_aiml_infer": False,
            "frontend_dir": None,
            "backend_entrypoint": None,
            "train_entrypoint": None,
            "infer_entrypoint": None,
            "html_entrypoint": None,
        }

        if not ws.exists():
            return deliverables

        # 1. Check Node/Vite Frontend
        pkg_paths = [ws / "package.json", ws / "frontend" / "package.json"]
        for pkg_p in pkg_paths:
            if pkg_p.exists():
                deliverables["has_node_frontend"] = True
                deliverables["frontend_dir"] = pkg_p.parent
                break

        # 2. Check Static HTML
        html_paths = [ws / "index.html", ws / "frontend" / "index.html", ws / "public" / "index.html"]
        for html_p in html_paths:
            if html_p.exists():
                deliverables["has_static_html"] = True
                deliverables["html_entrypoint"] = html_p
                break

        # 3. Check Python Backend & Entrypoints
        backend_candidates = [
            ws / "backend" / "main.py",
            ws / "backend" / "server.py",
            ws / "api" / "server.py",
            ws / "api" / "main.py",
            ws / "main.py",
            ws / "app.py",
            ws / "server.py",
        ]
        for py_p in backend_candidates:
            if py_p.exists():
                deliverables["has_python_backend"] = True
                deliverables["backend_entrypoint"] = py_p
                try:
                    content = py_p.read_text(errors="ignore")
                    if "FastAPI" in content or "uvicorn" in content:
                        deliverables["has_fastapi"] = True
                except Exception:
                    pass
                break

        # 4. Check AI/ML Training & Inference Scripts
        train_candidates = [
            ws / "train.py",
            ws / "train_model.py",
            ws / "training.py",
            ws / "train" / "train.py",
        ]
        for tr_p in train_candidates:
            if tr_p.exists():
                deliverables["has_aiml_train"] = True
                deliverables["train_entrypoint"] = tr_p
                break

        infer_candidates = [
            ws / "infer.py",
            ws / "predict.py",
            ws / "serve.py",
            ws / "inference.py",
            ws / "eval" / "infer.py",
        ]
        for inf_p in infer_candidates:
            if inf_p.exists():
                deliverables["has_aiml_infer"] = True
                deliverables["infer_entrypoint"] = inf_p
                break

        return deliverables

    def ignite(
        self,
        objective: str = "",
        open_browser: bool = False,
        timeout: float = 30.0,
    ) -> LiveServiceManifest:
        """Analyze, allocate ports, boot live services, probe readiness, and record provenance."""
        deliverables = self.inspect_deliverables()

        # Route to appropriate scenario
        if deliverables["has_aiml_train"] or deliverables["has_aiml_infer"]:
            manifest = self._ignite_aiml(deliverables, objective, timeout=timeout)
        elif deliverables["has_python_backend"] and (deliverables["has_node_frontend"] or deliverables["has_static_html"]):
            manifest = self._ignite_fullstack(deliverables, objective, timeout=timeout)
        elif deliverables["has_python_backend"]:
            manifest = self._ignite_backend(deliverables, objective, timeout=timeout)
        elif deliverables["has_node_frontend"] or deliverables["has_static_html"]:
            manifest = self._ignite_frontend(deliverables, objective, timeout=timeout)
        else:
            manifest = LiveServiceManifest(
                service_type="workspace",
                title=objective or "Synthesized Workspace",
                status="STOPPED",
                error_message="No executable server entrypoints detected in workspace.",
                run_id=self.run_id,
            )

        self.manifest = manifest
        save_ignition_registry(self.run_id, manifest, self.workspace_dir)

        # Handle --open flag: only open browser upon confirmed readiness
        if open_browser and manifest.status in ("READY", "RUNNING") and manifest.primary_url:
            open_url_in_browser(manifest.primary_url)

        return manifest

    def _spawn_with_port_retry(
        self,
        spawn_fn: Callable[[int, Path], Optional[subprocess.Popen]],
        service_name: str,
        base_port: int,
        log_file: Path,
        max_retries: int = 3,
    ) -> Tuple[Optional[subprocess.Popen], int]:
        """Spawn service with automatic retry on EADDRINUSE / address collision."""
        curr_port = find_free_port(base_port)
        for attempt in range(max_retries):
            proc = spawn_fn(curr_port, log_file)
            if proc is None:
                return None, curr_port

            # Brief check to see if process died immediately due to port conflict
            time.sleep(0.3)
            if proc.poll() is not None:
                tail = get_log_tail(log_file, 10).lower()
                if any(err in tail for err in ["address already in use", "eaddrinuse", "errno 48", "errno 98"]):
                    logger.warning("Port %d busy for %s. Retrying attempt %d/%d...", curr_port, service_name, attempt + 1, max_retries)
                    curr_port = find_free_port(curr_port + 1)
                    continue
                return proc, curr_port

            return proc, curr_port

        return None, curr_port

    def _ignite_fullstack(self, deliverables: Dict[str, Any], objective: str, timeout: float = 30.0) -> LiveServiceManifest:
        """Launch both backend API and frontend dev server."""
        log_dir = self._get_log_dir()
        backend_log = log_dir / "backend.log"
        frontend_log = log_dir / "frontend.log"

        services_info = []
        pids = []
        pgids = []

        # 1. Spawn Backend
        backend_p, backend_port = self._spawn_with_port_retry(
            lambda p, lf: self._spawn_python_backend(deliverables["backend_entrypoint"], p, lf),
            "backend",
            8000,
            backend_log,
        )
        if backend_p:
            pids.append(backend_p.pid)
            pgid = get_safe_pgid(backend_p.pid)
            pgids.append(pgid)
            _ACTIVE_PGIDS.add(pgid)

        # 2. Spawn Frontend
        if deliverables["has_node_frontend"] and deliverables["frontend_dir"]:
            frontend_p, frontend_port = self._spawn_with_port_retry(
                lambda p, lf: self._spawn_node_frontend(deliverables["frontend_dir"], p, lf),
                "frontend",
                5173,
                frontend_log,
            )
        elif deliverables["has_static_html"] and deliverables["html_entrypoint"]:
            frontend_p, frontend_port = self._spawn_with_port_retry(
                lambda p, lf: self._spawn_static_server(deliverables["html_entrypoint"].parent, p, lf),
                "frontend",
                5173,
                frontend_log,
            )
        else:
            frontend_p, frontend_port = None, 5173

        if frontend_p:
            pids.append(frontend_p.pid)
            f_pgid = get_safe_pgid(frontend_p.pid)
            pgids.append(f_pgid)
            _ACTIVE_PGIDS.add(f_pgid)

        # 3. Probe Readiness
        b_ready, b_tail = False, ""
        f_ready, f_tail = False, ""
        if backend_p:
            b_ready, b_tail = wait_for_service_readiness(backend_port, is_http=True, timeout=timeout, proc=backend_p, log_file=backend_log)
            services_info.append(IgnitionServiceInfo(
                name="backend",
                pid=backend_p.pid,
                pgid=get_safe_pgid(backend_p.pid),
                port=backend_port,
                url=f"http://127.0.0.1:{backend_port}",
                log_path=str(backend_log),
                status="READY" if b_ready else "FAILED",
            ))

        if frontend_p:
            f_ready, f_tail = wait_for_service_readiness(frontend_port, is_http=True, timeout=timeout, proc=frontend_p, log_file=frontend_log)
            services_info.append(IgnitionServiceInfo(
                name="frontend",
                pid=frontend_p.pid,
                pgid=get_safe_pgid(frontend_p.pid),
                port=frontend_port,
                url=f"http://127.0.0.1:{frontend_port}",
                log_path=str(frontend_log),
                status="READY" if f_ready else "FAILED",
            ))

        primary_url = f"http://127.0.0.1:{frontend_port}" if frontend_p else f"http://127.0.0.1:{backend_port}"
        api_docs = f"http://127.0.0.1:{backend_port}/docs" if deliverables["has_fastapi"] else f"http://127.0.0.1:{backend_port}"

        is_overall_ready = (b_ready and f_ready) if (backend_p and frontend_p) else (b_ready or f_ready)
        status = "READY" if is_overall_ready else "FAILED"
        err_msg = None
        log_tail = None
        if not is_overall_ready:
            log_tail = f"Backend log:\n{b_tail}\n\nFrontend log:\n{f_tail}".strip()
            err_msg = f"Full-stack readiness timeout ({timeout}s):\n{log_tail}"

        return LiveServiceManifest(
            service_type="web_app",
            title=objective or "Full-Stack Application",
            primary_url=primary_url,
            api_docs_url=api_docs,
            backend_port=backend_port,
            frontend_port=frontend_port,
            status=status,
            pids=pids,
            pgids=pgids,
            services=services_info,
            endpoints=["/", "/api", "/docs" if deliverables["has_fastapi"] else "/health"],
            command_launched=f"Uvicorn Backend (:{backend_port}) & Frontend Dev Server (:{frontend_port})",
            error_message=err_msg,
            log_tail=log_tail,
            run_id=self.run_id,
        )

    def _ignite_backend(self, deliverables: Dict[str, Any], objective: str, timeout: float = 30.0) -> LiveServiceManifest:
        """Launch standalone backend API."""
        log_dir = self._get_log_dir()
        backend_log = log_dir / "backend.log"

        backend_p, backend_port = self._spawn_with_port_retry(
            lambda p, lf: self._spawn_python_backend(deliverables["backend_entrypoint"], p, lf),
            "backend",
            8000,
            backend_log,
        )

        pids = []
        pgids = []
        services_info = []

        if backend_p:
            pids.append(backend_p.pid)
            pgid = get_safe_pgid(backend_p.pid)
            pgids.append(pgid)
            _ACTIVE_PGIDS.add(pgid)

        api_url = f"http://127.0.0.1:{backend_port}"
        docs_url = f"{api_url}/docs" if deliverables["has_fastapi"] else api_url

        is_ready, tail = wait_for_service_readiness(backend_port, is_http=True, timeout=timeout, proc=backend_p, log_file=backend_log)

        if backend_p:
            services_info.append(IgnitionServiceInfo(
                name="backend",
                pid=backend_p.pid,
                pgid=pgids[0],
                port=backend_port,
                url=api_url,
                log_path=str(backend_log),
                status="READY" if is_ready else "FAILED",
            ))

        return LiveServiceManifest(
            service_type="api_service",
            title=objective or "Backend REST Service",
            primary_url=docs_url,
            api_docs_url=docs_url,
            backend_port=backend_port,
            status="READY" if is_ready else "FAILED",
            pids=pids,
            pgids=pgids,
            services=services_info,
            endpoints=["/docs" if deliverables["has_fastapi"] else "/", "/health"],
            command_launched=f"Python API Server on :{backend_port}",
            error_message=f"Backend readiness failed ({timeout}s):\n{tail}" if not is_ready else None,
            log_tail=tail if not is_ready else None,
            run_id=self.run_id,
        )

    def _ignite_frontend(self, deliverables: Dict[str, Any], objective: str, timeout: float = 30.0) -> LiveServiceManifest:
        """Launch standalone frontend UI."""
        log_dir = self._get_log_dir()
        frontend_log = log_dir / "frontend.log"

        if deliverables["has_node_frontend"] and deliverables["frontend_dir"]:
            frontend_p, frontend_port = self._spawn_with_port_retry(
                lambda p, lf: self._spawn_node_frontend(deliverables["frontend_dir"], p, lf),
                "frontend",
                5173,
                frontend_log,
            )
        elif deliverables["has_static_html"] and deliverables["html_entrypoint"]:
            frontend_p, frontend_port = self._spawn_with_port_retry(
                lambda p, lf: self._spawn_static_server(deliverables["html_entrypoint"].parent, p, lf),
                "frontend",
                5173,
                frontend_log,
            )
        else:
            frontend_p, frontend_port = None, 5173

        pids = []
        pgids = []
        services_info = []

        if frontend_p:
            pids.append(frontend_p.pid)
            pgid = get_safe_pgid(frontend_p.pid)
            pgids.append(pgid)
            _ACTIVE_PGIDS.add(pgid)

        primary_url = f"http://127.0.0.1:{frontend_port}"
        is_ready, tail = wait_for_service_readiness(frontend_port, is_http=True, timeout=timeout, proc=frontend_p, log_file=frontend_log)

        if frontend_p:
            services_info.append(IgnitionServiceInfo(
                name="frontend",
                pid=frontend_p.pid,
                pgid=pgids[0],
                port=frontend_port,
                url=primary_url,
                log_path=str(frontend_log),
                status="READY" if is_ready else "FAILED",
            ))

        return LiveServiceManifest(
            service_type="web_app",
            title=objective or "Interactive Web Application",
            primary_url=primary_url,
            frontend_port=frontend_port,
            status="READY" if is_ready else "FAILED",
            pids=pids,
            pgids=pgids,
            services=services_info,
            endpoints=["/"],
            command_launched=f"Frontend Server on :{frontend_port}",
            error_message=f"Frontend readiness failed ({timeout}s):\n{tail}" if not is_ready else None,
            log_tail=tail if not is_ready else None,
            run_id=self.run_id,
        )

    def _ignite_aiml(self, deliverables: Dict[str, Any], objective: str, timeout: float = 30.0) -> LiveServiceManifest:
        """Launch AI/ML Training loop and optional Inference Server."""
        log_dir = self._get_log_dir()
        infer_log = log_dir / "aiml_infer.log"
        train_log = log_dir / "aiml_train.log"

        pids = []
        pgids = []
        services_info = []
        infer_url = None

        # 1. Spawn Inference API if present
        if deliverables["has_aiml_infer"] and deliverables["infer_entrypoint"]:
            infer_p, infer_port = self._spawn_with_port_retry(
                lambda p, lf: self._spawn_python_backend(deliverables["infer_entrypoint"], p, lf),
                "aiml_infer",
                8000,
                infer_log,
            )
            if infer_p:
                pids.append(infer_p.pid)
                pgid = get_safe_pgid(infer_p.pid)
                pgids.append(pgid)
                _ACTIVE_PGIDS.add(pgid)
                infer_url = f"http://127.0.0.1:{infer_port}"
                is_ready, tail = wait_for_service_readiness(infer_port, is_http=True, timeout=timeout, proc=infer_p, log_file=infer_log)
                services_info.append(IgnitionServiceInfo(
                    name="aiml_infer",
                    pid=infer_p.pid,
                    pgid=pgid,
                    port=infer_port,
                    url=infer_url,
                    log_path=str(infer_log),
                    status="READY" if is_ready else "FAILED",
                ))

        # 2. Spawn Training Loop in background if present
        if deliverables["has_aiml_train"] and deliverables["train_entrypoint"]:
            train_fp = open(train_log, "a+", encoding="utf-8")
            self.log_handles.append(train_fp)
            train_p = subprocess.Popen(
                [sys.executable, str(deliverables["train_entrypoint"])],
                cwd=str(deliverables["train_entrypoint"].parent),
                stdout=train_fp,
                stderr=train_fp,
                text=True,
                start_new_session=True,
            )
            pids.append(train_p.pid)
            tr_pgid = get_safe_pgid(train_p.pid)
            pgids.append(tr_pgid)
            _ACTIVE_PGIDS.add(tr_pgid)
            self.active_processes.append((train_p, train_fp, tr_pgid))
            services_info.append(IgnitionServiceInfo(
                name="aiml_train",
                pid=train_p.pid,
                pgid=tr_pgid,
                port=0,
                url="",
                log_path=str(train_log),
                status="RUNNING",
            ))

        return LiveServiceManifest(
            service_type="aiml_training",
            title=objective or "AI/ML Model Training Pipeline",
            primary_url=infer_url,
            inference_url=f"{infer_url}/predict" if infer_url else None,
            api_docs_url=f"{infer_url}/docs" if infer_url else None,
            status="READY" if pids else "FAILED",
            pids=pids,
            pgids=pgids,
            services=services_info,
            endpoints=["/predict", "/metrics"],
            command_launched="AI/ML Training & Inference Pipeline",
            run_id=self.run_id,
        )

    # -------------------------------------------------------------------------
    # Process Launching Helpers
    # -------------------------------------------------------------------------
    def _spawn_python_backend(self, entrypoint: Path, port: int, log_file: Path) -> Optional[subprocess.Popen]:
        """Spawn Python FastAPI/HTTP backend on target port bound to 127.0.0.1."""
        env = os.environ.copy()
        env["PORT"] = str(port)
        env["HOST"] = "127.0.0.1"

        cmd = [sys.executable, str(entrypoint)]
        try:
            content = entrypoint.read_text(errors="ignore")
            app_match = re.search(r"(\w+)\s*=\s*FastAPI\(", content)
            app_var = app_match.group(1) if app_match else "app"

            rel_path = entrypoint.relative_to(self.workspace_dir).as_posix()
            dotted_module = rel_path.replace("/", ".").replace(".py", "")
            cmd = [sys.executable, "-m", "uvicorn", f"{dotted_module}:{app_var}", "--host", "127.0.0.1", "--port", str(port)]
        except Exception:
            cmd = [sys.executable, str(entrypoint)]

        try:
            log_fp = open(log_file, "a+", encoding="utf-8")
            self.log_handles.append(log_fp)
            proc = subprocess.Popen(
                cmd,
                cwd=str(self.workspace_dir),
                env=env,
                stdout=log_fp,
                stderr=log_fp,
                text=True,
                start_new_session=True,
            )
            pgid = get_safe_pgid(proc.pid)
            self.active_processes.append((proc, log_fp, pgid))
            return proc
        except Exception as e:
            logger.debug("Failed launching backend process: %s", e)
            return None

    def _spawn_node_frontend(self, frontend_dir: Path, port: int, log_file: Path) -> Optional[subprocess.Popen]:
        """Spawn Node / Vite frontend dev server bound to 127.0.0.1."""
        env = os.environ.copy()
        env["PORT"] = str(port)

        cmd = ["npx", "-y", "vite", "--port", str(port), "--host", "127.0.0.1"]
        try:
            log_fp = open(log_file, "a+", encoding="utf-8")
            self.log_handles.append(log_fp)
            proc = subprocess.Popen(
                cmd,
                cwd=str(frontend_dir),
                env=env,
                stdout=log_fp,
                stderr=log_fp,
                text=True,
                start_new_session=True,
            )
            pgid = get_safe_pgid(proc.pid)
            self.active_processes.append((proc, log_fp, pgid))
            return proc
        except Exception as e:
            logger.debug("Node frontend launch failed: %s; falling back to static server", e)
            return self._spawn_static_server(frontend_dir, port, log_file)

    def _spawn_static_server(self, static_dir: Path, port: int, log_file: Path) -> Optional[subprocess.Popen]:
        """Spawn lightweight Python HTTP static server bound to 127.0.0.1."""
        cmd = [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"]
        try:
            log_fp = open(log_file, "a+", encoding="utf-8")
            self.log_handles.append(log_fp)
            proc = subprocess.Popen(
                cmd,
                cwd=str(static_dir),
                stdout=log_fp,
                stderr=log_fp,
                text=True,
                start_new_session=True,
            )
            pgid = get_safe_pgid(proc.pid)
            self.active_processes.append((proc, log_fp, pgid))
            return proc
        except Exception as e:
            logger.debug("Static server launch failed: %s", e)
            return None

    def _update_registry_file(self) -> None:
        """Update the saved ignition registry JSON file with current status."""
        if self.manifest:
            try:
                save_ignition_registry(self.run_id, self.manifest, self.workspace_dir)
            except Exception:
                pass

    def monitor_sensory_stream(self) -> Optional[ToolResult]:
        """Check all active processes for runtime errors and encode into sensory signals."""
        for proc, log_fp, _ in self.active_processes:
            if proc.poll() is not None and proc.returncode != 0:
                stderr_text = ""
                try:
                    if log_fp and hasattr(log_fp, "name"):
                        stderr_text = get_log_tail(Path(log_fp.name), 20)
                except Exception:
                    pass

                result = ToolResult(
                    exit_code=proc.returncode,
                    stderr=stderr_text or "Process terminated unexpectedly.",
                    latency_ms=100.0,
                )
                return result
        return None

    def terminate_all(self) -> None:
        """Safely terminate all spawned background processes and their process groups."""
        for proc, log_fp, pgid in self.active_processes:
            try:
                if pgid and pgid > 0:
                    kill_process_group(pgid, grace_seconds=3.0)
                    _ACTIVE_PGIDS.discard(pgid)
                elif proc and proc.poll() is None:
                    proc.terminate()
                    try:
                        proc.wait(timeout=1.5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
            except Exception as e:
                logger.debug("Error terminating process: %s", e)
            finally:
                if log_fp and hasattr(log_fp, "close") and not log_fp.closed:
                    try:
                        log_fp.close()
                    except Exception:
                        pass

        for fp in self.log_handles:
            if fp and hasattr(fp, "close") and not fp.closed:
                try:
                    fp.close()
                except Exception:
                    pass

        self.active_processes.clear()
        self.log_handles.clear()

        if self in _ACTIVE_IGNITERS:
            _ACTIVE_IGNITERS.remove(self)

        if self.manifest:
            self.manifest.status = "STOPPED"
            for s in self.manifest.services:
                s.status = "STOPPED"
            self._update_registry_file()
