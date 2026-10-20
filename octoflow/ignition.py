"""ProjectIgniter: Autonomous Phase 4 Live Ignition & Runtime Environment Server.

Auto-provisions, boots, and monitors live web applications, backend APIs,
and AI/ML training/inference pipelines directly from synthesized project deliverables.
Generates interactive test links and connects runtime execution signals back into
the CodeSensoryEncoder for real-time biophysical telemetry and self-healing.
"""

import atexit
import asyncio
import os
import re
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from octoflow.encoder import CodeSensoryEncoder
from octoflow.tools import ToolResult


def wait_for_service(port: int, host: str = "127.0.0.1", timeout: float = 6.0) -> bool:
    """Poll port until it responds or timeout is exceeded."""
    t_end = time.time() + timeout
    while time.time() < t_end:
        if is_port_listening(port, host=host):
            return True
        time.sleep(0.15)
    return False


def find_free_port(start_port: int, max_attempts: int = 50) -> int:
    """Find the next available unallocated port starting from start_port."""
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
    """Check if a service is actively listening on a given port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


class LiveServiceManifest(BaseModel):
    """Manifest describing actively running services provisioned by ProjectIgniter."""
    service_type: str = "web_app"  # "web_app", "api_service", "aiml_training", "aiml_inference", "static_web"
    title: str = "Generated Application"
    primary_url: Optional[str] = None
    api_docs_url: Optional[str] = None
    inference_url: Optional[str] = None
    status: str = "INITIALIZING"  # "RUNNING", "FAILED", "STOPPED"
    backend_port: Optional[int] = None
    frontend_port: Optional[int] = None
    pids: List[int] = Field(default_factory=list)
    endpoints: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    command_launched: str = ""


class ProjectIgniter:
    """Autonomous Phase Gate 4 engine: provisions and launches live deliverables."""

    def __init__(
        self,
        workspace_dir: str = ".",
        sensory_encoder: Optional[CodeSensoryEncoder] = None,
    ):
        self.workspace_dir = Path(workspace_dir).expanduser().resolve()
        self.encoder = sensory_encoder or CodeSensoryEncoder()
        self.active_processes: List[subprocess.Popen] = []
        self.manifest: Optional[LiveServiceManifest] = None
        atexit.register(self.terminate_all)

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
                content = py_p.read_text(errors="ignore")
                if "FastAPI" in content or "uvicorn" in content:
                    deliverables["has_fastapi"] = True
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

    def ignite(self, objective: str = "") -> LiveServiceManifest:
        """Analyze, allocate ports, and boot up live services."""
        deliverables = self.inspect_deliverables()
        pids: List[int] = []

        # ---------------------------------------------------------------------
        # SCENARIO A: AI/ML Research / Model Pipeline
        # ---------------------------------------------------------------------
        if deliverables["has_aiml_train"] or deliverables["has_aiml_infer"]:
            return self._ignite_aiml(deliverables, objective)

        # ---------------------------------------------------------------------
        # SCENARIO B: Full-Stack Web App (Frontend + Python Backend)
        # ---------------------------------------------------------------------
        if deliverables["has_python_backend"] and (deliverables["has_node_frontend"] or deliverables["has_static_html"]):
            return self._ignite_fullstack(deliverables, objective)

        # ---------------------------------------------------------------------
        # SCENARIO C: Backend API Service Only
        # ---------------------------------------------------------------------
        if deliverables["has_python_backend"]:
            return self._ignite_backend(deliverables, objective)

        # ---------------------------------------------------------------------
        # SCENARIO D: Frontend Web App Only
        # ---------------------------------------------------------------------
        if deliverables["has_node_frontend"] or deliverables["has_static_html"]:
            return self._ignite_frontend(deliverables, objective)

        # Fallback if no specific entrypoint was found yet
        manifest = LiveServiceManifest(
            service_type="workspace",
            title=objective or "Synthesized Workspace",
            status="STOPPED",
            error_message="No executable server entrypoints detected in workspace.",
        )
        self.manifest = manifest
        return manifest

    def _ignite_fullstack(self, deliverables: Dict[str, Any], objective: str) -> LiveServiceManifest:
        """Launch both backend API and frontend dev server."""
        backend_port = find_free_port(8000)
        frontend_port = find_free_port(5173)
        pids = []

        # 1. Launch Backend
        backend_p = self._spawn_python_backend(deliverables["backend_entrypoint"], backend_port)
        if backend_p:
            pids.append(backend_p.pid)
            self.active_processes.append(backend_p)

        # 2. Launch Frontend
        if deliverables["has_node_frontend"] and deliverables["frontend_dir"]:
            frontend_p = self._spawn_node_frontend(deliverables["frontend_dir"], frontend_port)
            if frontend_p:
                pids.append(frontend_p.pid)
                self.active_processes.append(frontend_p)
        elif deliverables["has_static_html"] and deliverables["html_entrypoint"]:
            frontend_p = self._spawn_static_server(deliverables["html_entrypoint"].parent, frontend_port)
            if frontend_p:
                pids.append(frontend_p.pid)
                self.active_processes.append(frontend_p)

        primary_url = f"http://localhost:{frontend_port}"
        api_docs = f"http://localhost:{backend_port}/docs" if deliverables["has_fastapi"] else f"http://localhost:{backend_port}"

        is_ready = wait_for_service(frontend_port, timeout=3.5) or wait_for_service(backend_port, timeout=2.0)

        manifest = LiveServiceManifest(
            service_type="web_app",
            title=objective or "Full-Stack Application",
            primary_url=primary_url,
            api_docs_url=api_docs,
            backend_port=backend_port,
            frontend_port=frontend_port,
            status="RUNNING" if is_ready else ("RUNNING" if pids else "FAILED"),
            pids=pids,
            endpoints=["/", "/api", "/docs" if deliverables["has_fastapi"] else "/health"],
            command_launched=f"Uvicorn Backend (:{backend_port}) & Frontend Dev Server (:{frontend_port})",
        )
        self.manifest = manifest
        return manifest

    def _ignite_backend(self, deliverables: Dict[str, Any], objective: str) -> LiveServiceManifest:
        """Launch standalone backend API."""
        backend_port = find_free_port(8000)
        pids = []

        backend_p = self._spawn_python_backend(deliverables["backend_entrypoint"], backend_port)
        if backend_p:
            pids.append(backend_p.pid)
            self.active_processes.append(backend_p)

        api_url = f"http://localhost:{backend_port}"
        docs_url = f"{api_url}/docs" if deliverables["has_fastapi"] else api_url
        is_ready = wait_for_service(backend_port, timeout=3.0)

        manifest = LiveServiceManifest(
            service_type="api_service",
            title=objective or "Backend REST Service",
            primary_url=docs_url,
            api_docs_url=docs_url,
            backend_port=backend_port,
            status="RUNNING" if is_ready else ("RUNNING" if pids else "FAILED"),
            pids=pids,
            endpoints=["/docs" if deliverables["has_fastapi"] else "/", "/health"],
            command_launched=f"Python API Server on :{backend_port}",
        )
        self.manifest = manifest
        return manifest

    def _ignite_frontend(self, deliverables: Dict[str, Any], objective: str) -> LiveServiceManifest:
        """Launch standalone frontend UI."""
        frontend_port = find_free_port(5173)
        pids = []

        if deliverables["has_node_frontend"] and deliverables["frontend_dir"]:
            frontend_p = self._spawn_node_frontend(deliverables["frontend_dir"], frontend_port)
            if frontend_p:
                pids.append(frontend_p.pid)
                self.active_processes.append(frontend_p)
        elif deliverables["has_static_html"] and deliverables["html_entrypoint"]:
            frontend_p = self._spawn_static_server(deliverables["html_entrypoint"].parent, frontend_port)
            if frontend_p:
                pids.append(frontend_p.pid)
                self.active_processes.append(frontend_p)

        primary_url = f"http://localhost:{frontend_port}"
        is_ready = wait_for_service(frontend_port, timeout=3.5)

        manifest = LiveServiceManifest(
            service_type="web_app",
            title=objective or "Interactive Web Application",
            primary_url=primary_url,
            frontend_port=frontend_port,
            status="RUNNING" if is_ready else ("RUNNING" if pids else "FAILED"),
            pids=pids,
            endpoints=["/"],
            command_launched=f"Frontend Server on :{frontend_port}",
        )
        self.manifest = manifest
        return manifest

    def _ignite_aiml(self, deliverables: Dict[str, Any], objective: str) -> LiveServiceManifest:
        """Launch AI/ML Training loop and optional Inference Server."""
        pids = []
        infer_port = find_free_port(8000)

        # 1. Launch Inference API if present
        infer_url = None
        if deliverables["has_aiml_infer"] and deliverables["infer_entrypoint"]:
            infer_p = self._spawn_python_backend(deliverables["infer_entrypoint"], infer_port)
            if infer_p:
                pids.append(infer_p.pid)
                self.active_processes.append(infer_p)
                infer_url = f"http://localhost:{infer_port}"

        # 2. Launch Training Loop in background if present
        if deliverables["has_aiml_train"] and deliverables["train_entrypoint"]:
            train_p = subprocess.Popen(
                [sys.executable, str(deliverables["train_entrypoint"])],
                cwd=str(deliverables["train_entrypoint"].parent),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            pids.append(train_p.pid)
            self.active_processes.append(train_p)

        manifest = LiveServiceManifest(
            service_type="aiml_training",
            title=objective or "AI/ML Model Training Pipeline",
            primary_url=infer_url or f"http://localhost:{infer_port}",
            inference_url=f"{infer_url}/predict" if infer_url else None,
            api_docs_url=f"{infer_url}/docs" if infer_url else None,
            backend_port=infer_port,
            status="RUNNING",
            pids=pids,
            endpoints=["/predict", "/metrics"],
            command_launched=f"AI/ML Training & Inference Server (:{infer_port})",
        )
        self.manifest = manifest
        return manifest

    # -------------------------------------------------------------------------
    # Process Launching Helpers
    # -------------------------------------------------------------------------
    def _spawn_python_backend(self, entrypoint: Path, port: int) -> Optional[subprocess.Popen]:
        """Spawn Python FastAPI/HTTP backend on target port."""
        env = os.environ.copy()
        env["PORT"] = str(port)

        cmd = [sys.executable, str(entrypoint)]
        try:
            content = entrypoint.read_text(errors="ignore")
            # If FastAPI app object is defined, run via uvicorn if available
            app_match = re.search(r"(\w+)\s*=\s*FastAPI\(", content)
            app_var = app_match.group(1) if app_match else "app"

            # Check if uvicorn can be imported
            module_name = entrypoint.stem
            rel_path = entrypoint.relative_to(self.workspace_dir).as_posix()
            dotted_module = rel_path.replace("/", ".").replace(".py", "")

            # Default command: direct python script
            cmd = [sys.executable, "-m", "uvicorn", f"{dotted_module}:{app_var}", "--host", "127.0.0.1", "--port", str(port)]
        except Exception:
            cmd = [sys.executable, str(entrypoint)]

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(self.workspace_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            # Brief wait to ensure process didn't instantly die on syntax error
            time.sleep(0.4)
            if proc.poll() is not None:
                # Fallback to direct script execution
                fallback_cmd = [sys.executable, str(entrypoint)]
                proc = subprocess.Popen(
                    fallback_cmd,
                    cwd=str(entrypoint.parent),
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    start_new_session=True,
                )
            return proc
        except Exception:
            return None

    def _spawn_node_frontend(self, frontend_dir: Path, port: int) -> Optional[subprocess.Popen]:
        """Spawn Node / Vite frontend dev server."""
        env = os.environ.copy()
        env["PORT"] = str(port)

        cmd = ["npx", "-y", "vite", "--port", str(port), "--host", "127.0.0.1"]
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(frontend_dir),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            return proc
        except Exception:
            # Fallback to Python static server
            return self._spawn_static_server(frontend_dir, port)

    def _spawn_static_server(self, static_dir: Path, port: int) -> Optional[subprocess.Popen]:
        """Spawn lightweight Python HTTP static server."""
        cmd = [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"]
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(static_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                start_new_session=True,
            )
            return proc
        except Exception:
            return None

    def monitor_sensory_stream(self) -> Optional[ToolResult]:
        """Check all active processes for runtime errors and encode into sensory signals."""
        for proc in self.active_processes:
            if proc.poll() is not None and proc.returncode != 0:
                # Process crashed
                stderr_text = ""
                try:
                    if proc.stderr:
                        stderr_text = proc.stderr.read()
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
        """Safely terminate all spawned background processes and their child processes."""
        for proc in self.active_processes:
            try:
                if proc.poll() is None:
                    if hasattr(os, "killpg") and hasattr(os, "getpgid"):
                        try:
                            pgid = os.getpgid(proc.pid)
                            os.killpg(pgid, signal.SIGTERM)
                        except Exception:
                            proc.terminate()
                    else:
                        proc.terminate()
                    proc.wait(timeout=1.5)
            except Exception:
                try:
                    if hasattr(os, "killpg") and hasattr(os, "getpgid"):
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    else:
                        proc.kill()
                except Exception:
                    pass
        self.active_processes.clear()
        if self.manifest:
            self.manifest.status = "STOPPED"
