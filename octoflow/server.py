"""Telemetry WebSocket & HTTP Server for OctoFlow 3D Connectome Visualizer.

Streams live swarm telemetry (sensory surprise deltas, dynamic coalition bindings,
and tool executions) to the 3D WebGL cephalopod visualizer on localhost:8088.
Hardened with 127.0.0.1 default binding, WebSocket Origin validation (code 1008),
HTTP Host header DNS-rebinding protection, and structural payload secret sanitization.
"""

import asyncio
import json
import os
import socket
import sys
import threading
from pathlib import Path
from typing import Any

from octoflow.conductor import SwarmTelemetryEvent
from octoflow.logging_config import get_logger
from octoflow.provider import redact_secrets

try:
    import uvicorn
    from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

logger = get_logger("server")


def find_available_port(
    start_port: int, max_attempts: int = 10, host: str = "127.0.0.1"
) -> int | None:
    """Find the next available port starting from start_port on the specified host."""
    host_str = host if isinstance(host, str) else "127.0.0.1"
    for p in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((host_str, p))
                return p
        except OSError:
            continue
    return None


class TelemetryBroadcaster:
    """Manages active WebSocket connections and broadcasts sanitized telemetry packets."""

    def __init__(self, port: int = 8088, host: str = "127.0.0.1", dev_mode: bool = False):
        self.requested_port = port if isinstance(port, int) else 8088
        self.port = self.requested_port
        self.host = host if isinstance(host, str) else "127.0.0.1"
        self.dev_mode = (
            dev_mode or (os.getenv("OCTOFLOW_DEV") == "1") or (os.getenv("VITE_DEV") == "1")
        )
        self.active_sockets: set[Any] = set()
        self.server_thread: threading.Thread | None = None
        self.server_instance: Any | None = None
        self.loop: asyncio.AbstractEventLoop | None = None
        self.history: list[dict] = []

        if self.host not in ("127.0.0.1", "localhost"):
            warning_msg = (
                f"SECURITY WARNING: Telemetry server binding to '{self.host}' instead of 127.0.0.1. "
                "This exposes the swarm and visualizer bridge to the external network."
            )
            logger.warning(warning_msg)
            sys.stderr.write(f"\n▲ {warning_msg}\n\n")

    @staticmethod
    def sanitize_telemetry_dict(data: dict) -> dict:
        """Strip sensitive fields (prompts, file contents, command output, raw API keys)
        and pass free-text fields through the secret redactor."""
        clean = {}
        sensitive_field_names = {
            "prompt",
            "prompt_text",
            "prompts",
            "system_prompt",
            "user_prompt",
            "messages",
            "file_content",
            "file_contents",
            "content",
            "contents",
            "file_data",
            "diff",
            "diff_content",
            "patch",
            "stdout",
            "stderr",
            "command_output",
            "raw_output",
            "output",
            "api_key",
            "key",
            "token",
            "secret",
            "password",
            "anthropic_api_key",
            "openai_api_key",
            "gemini_api_key",
            "grok_api_key",
            "deepseek_api_key",
            "authorization",
        }

        for k, v in data.items():
            k_lower = k.lower()
            if k_lower in sensitive_field_names:
                continue
            if any(
                term in k_lower for term in ["password", "secret", "token", "api_key", "apikey"]
            ):
                continue

            if isinstance(v, str):
                clean[k] = redact_secrets(v)
            elif isinstance(v, dict):
                clean[k] = TelemetryBroadcaster.sanitize_telemetry_dict(v)
            elif isinstance(v, list):
                clean_list = []
                for item in v:
                    if isinstance(item, dict):
                        clean_list.append(TelemetryBroadcaster.sanitize_telemetry_dict(item))
                    elif isinstance(item, str):
                        clean_list.append(redact_secrets(item))
                    else:
                        clean_list.append(item)
                clean[k] = clean_list
            else:
                clean[k] = v

        return clean

    def broadcast(self, event: SwarmTelemetryEvent) -> None:
        """Broadcast sanitized structural telemetry event to all connected visualizer clients."""
        try:
            raw_dict = event.model_dump()
            safe_dict = self.sanitize_telemetry_dict(raw_dict)
            self.history.append(safe_dict)
        except Exception as e:
            logger.debug(
                "Failed serializing telemetry event: %s", e
            )  # best-effort: fallback to empty event dict
            safe_dict = {}

        if not self.active_sockets or not self.loop:
            return

        payload = json.dumps(safe_dict)

        async def _send_all():
            dead_sockets = set()
            for ws in self.active_sockets:
                try:
                    await ws.send_text(payload)
                except Exception as e:
                    logger.debug(
                        "WebSocket client disconnected or send failed: %s", e
                    )  # best-effort: dead client pruning
                    dead_sockets.add(ws)
            self.active_sockets.difference_update(dead_sockets)

        asyncio.run_coroutine_threadsafe(_send_all(), self.loop)

    def broadcast_raw(self, data: dict) -> None:
        """Broadcast arbitrary JSON data packet (e.g. theme changes) to all connected clients."""
        try:
            safe_dict = self.sanitize_telemetry_dict(data)
            self.history.append(safe_dict)
        except Exception as e:
            logger.debug(
                "Failed sanitizing raw telemetry dict: %s", e
            )  # best-effort: fallback to unmutated data
            safe_dict = data

        if not self.active_sockets or not self.loop:
            return

        payload = json.dumps(safe_dict)

        async def _send_all():
            dead_sockets = set()
            for ws in self.active_sockets:
                try:
                    await ws.send_text(payload)
                except Exception as e:
                    logger.debug(
                        "WebSocket client disconnected during raw broadcast: %s", e
                    )  # best-effort: dead client pruning
                    dead_sockets.add(ws)
            self.active_sockets.difference_update(dead_sockets)

        asyncio.run_coroutine_threadsafe(_send_all(), self.loop)

    def get_history(self) -> list[dict]:
        """Retrieve all recorded sanitized telemetry events from the current session."""
        return list(self.history)

    def get_allowed_origins(self) -> set[str]:
        """Build exact set of allowed WebSocket Origin values."""
        allowed = {
            f"http://127.0.0.1:{self.port}",
            f"http://localhost:{self.port}",
            f"https://127.0.0.1:{self.port}",
            f"https://localhost:{self.port}",
        }
        if self.host not in ("127.0.0.1", "localhost", "0.0.0.0"):  # noqa: S104 - host whitelist check
            allowed.add(f"http://{self.host}:{self.port}")
            allowed.add(f"https://{self.host}:{self.port}")
        if self.dev_mode:
            allowed.add("http://localhost:5173")
            allowed.add("http://127.0.0.1:5173")
            allowed.add("https://localhost:5173")
            allowed.add("https://127.0.0.1:5173")
        return allowed

    def get_allowed_hosts(self) -> set[str]:
        """Build set of permitted Host header values for DNS-rebinding protection."""
        allowed = {"127.0.0.1", "localhost", "testserver"}
        if self.host not in ("127.0.0.1", "localhost", "0.0.0.0"):  # noqa: S104 - host whitelist check
            allowed.add(self.host.lower())
        if self.host == "0.0.0.0":  # noqa: S104 - permit 0.0.0.0 in header when explicitly bound
            allowed.add("0.0.0.0")  # noqa: S104 - permit 0.0.0.0 in header when explicitly bound
        return allowed

    def create_app(self) -> Any:
        """Create and configure the FastAPI telemetry application with security middleware."""
        if not FASTAPI_AVAILABLE:
            return None

        app = FastAPI(title="OctoFlow 3D Telemetry Bridge")

        # 1. HTTP Host Header Validation Middleware (DNS Rebinding Defense)
        @app.middleware("http")
        async def host_validation_middleware(request: Request, call_next):
            host_header = request.headers.get("host", "").strip()
            if not host_header:
                return Response("Forbidden: Missing Host header", status_code=400)

            host_name = host_header.split(":")[0].lower()
            if host_name.startswith("[") and host_name.endswith("]"):
                host_name = host_name[1:-1]

            allowed = self.get_allowed_hosts()
            if host_name not in allowed:
                return Response("Forbidden: Invalid Host header", status_code=400)

            return await call_next(request)

        # 2. WebSocket Telemetry Endpoint with Origin Validation
        @app.websocket("/ws/telemetry")
        async def websocket_endpoint(websocket: WebSocket):
            origin = websocket.headers.get("origin")
            if origin:
                clean_origin = origin.rstrip("/")
                if clean_origin not in self.get_allowed_origins():
                    await websocket.accept()
                    await websocket.close(code=1008, reason="Forbidden origin")
                    return

            await websocket.accept()
            self.active_sockets.add(websocket)
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.active_sockets.discard(websocket)
            except Exception as e:
                logger.debug(
                    "WebSocket receive loop encountered error: %s", e
                )  # best-effort: clean up disconnected socket
                self.active_sockets.discard(websocket)

        # 3. LLM Failover Pool Endpoints (Masked Keys and Secure Config)
        @app.get("/llm/pool")
        async def get_llm_pool():
            from octoflow.config import load_secure_config, mask_credential

            cfg_data = load_secure_config()
            raw_pool = cfg_data.get("llm_pool", [])
            safe_entries = []
            for item in raw_pool:
                copy_item = dict(item)
                raw_k = copy_item.get("api_key") or ""
                copy_item["masked_key"] = mask_credential(raw_k)
                copy_item["has_key"] = bool(raw_k)
                copy_item.pop("api_key", None)
                safe_entries.append(copy_item)
            return {"pool": safe_entries}

        @app.post("/llm/pool")
        async def post_llm_pool(payload: dict):
            from octoflow.config import load_secure_config, save_secure_config

            cfg_data = load_secure_config()
            current_pool = cfg_data.get("llm_pool", [])
            action = payload.get("action", "add")

            if action == "add":
                new_entry = payload.get("entry", {})
                if new_entry.get("id"):
                    updated = False
                    for idx, ex in enumerate(current_pool):
                        if ex.get("id") == new_entry["id"]:
                            current_pool[idx] = new_entry
                            updated = True
                            break
                    if not updated:
                        current_pool.append(new_entry)

            elif action == "remove":
                target_id = payload.get("id")
                current_pool = [e for e in current_pool if e.get("id") != target_id]

            elif action == "set_priority":
                order_ids = payload.get("order", [])
                reordered = []
                for p_idx, t_id in enumerate(order_ids):
                    for e in current_pool:
                        if e.get("id") == t_id:
                            e["priority"] = p_idx + 1
                            reordered.append(e)
                current_pool = reordered

            cfg_data["llm_pool"] = current_pool
            save_secure_config(cfg_data)
            return {"status": "ok", "pool_size": len(current_pool)}

        @app.post("/llm/test")
        async def test_llm_endpoint(payload: dict):
            entry_data = payload.get("entry", {})
            try:
                from octoflow.config import LLMConfigEntry
                from octoflow.provider import _build_from_pool_entry

                entry = LLMConfigEntry(**entry_data)
                prov = _build_from_pool_entry(entry)
                resp = prov.generate("Ping")
                return {"status": "ok", "response": resp.content[:100]}
            except Exception as e:
                return {"status": "error", "error": str(e)}

        # 4. Static Visualizer Serving & Fallback Index
        package_dist = Path(__file__).resolve().parent / "dist"
        source_dist = Path(__file__).resolve().parent.parent / "visualizer" / "dist"
        dist_path = package_dist if package_dist.exists() else source_dist
        if dist_path.exists():
            app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="visualizer")
        else:

            @app.get("/")
            async def fallback_index():
                return HTMLResponse(
                    "<html><body style='background:#0b0f19;color:#38bdf8;font-family:sans-serif;text-align:center;padding:50px;'>"
                    "<h1>◈ OctoFlow 3D Telemetry Server Active</h1>"
                    f"<p>WebSocket streaming on <code>ws://127.0.0.1:{self.port}/ws/telemetry</code></p>"
                    "<p>Run <code>npm run build</code> in <code>visualizer/</code> to load the 3D connectome canvas.</p>"
                    "</body></html>"
                )

        return app

    def start_in_background(self) -> None:
        """Launch the telemetry server on a daemon background thread binding to host (default: 127.0.0.1)."""
        if not FASTAPI_AVAILABLE:
            return

        available_port = find_available_port(self.requested_port, host=self.host)
        if available_port is None:
            return
        self.port = available_port

        app = self.create_app()

        def _run():
            try:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                config = uvicorn.Config(
                    app=app,
                    host=self.host,
                    port=self.port,
                    log_level="error",
                    ws="websockets-sansio",
                )
                self.server_instance = uvicorn.Server(config)
                self.loop.run_until_complete(self.server_instance.serve())
            except Exception as e:
                logger.debug(
                    "Telemetry server thread exited with error: %s", e
                )  # best-effort: background server shutdown

        self.server_thread = threading.Thread(target=_run, daemon=True)
        self.server_thread.start()

    def stop(self) -> None:
        """Stop the background telemetry server cleanly."""
        if self.server_instance:
            self.server_instance.should_exit = True
        for ws in list(self.active_sockets):
            try:
                if self.loop and self.loop.is_running():
                    asyncio.run_coroutine_threadsafe(ws.close(), self.loop)
            except Exception as e:
                logger.debug(
                    "Error closing websocket during server stop: %s", e
                )  # best-effort: socket may already be closed
        self.active_sockets.clear()
