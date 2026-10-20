"""Telemetry WebSocket & HTTP Server for OctoFlow 3D Connectome Visualizer.

Streams live swarm telemetry (sensory surprise deltas, dynamic coalition bindings,
and tool executions) to the 3D WebGL cephalopod visualizer on localhost:8088.
"""

import asyncio
import json
import threading
from pathlib import Path
from typing import Set, Optional, Any, List, Dict
from octoflow.conductor import SwarmTelemetryEvent

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import HTMLResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


import socket

def find_available_port(start_port: int, max_attempts: int = 10) -> Optional[int]:
    """Find the next available port starting from start_port."""
    for p in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("0.0.0.0", p))
                return p
        except OSError:
            continue
    return None


class TelemetryBroadcaster:
    """Manages active WebSocket connections and broadcasts telemetry packets."""

    def __init__(self, port: int = 8088):
        self.requested_port = port
        self.port = port
        self.active_sockets: Set[Any] = set()
        self.server_thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.history: List[dict] = []

    def broadcast(self, event: SwarmTelemetryEvent) -> None:
        """Broadcast telemetry event to all connected visualizer clients."""
        try:
            self.history.append(event.model_dump())
        except Exception:
            pass

        if not self.active_sockets or not self.loop:
            return

        payload = event.model_dump_json()

        async def _send_all():
            dead_sockets = set()
            for ws in self.active_sockets:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead_sockets.add(ws)
            self.active_sockets.difference_update(dead_sockets)

        asyncio.run_coroutine_threadsafe(_send_all(), self.loop)

    def broadcast_raw(self, data: dict) -> None:
        """Broadcast arbitrary JSON data packet (e.g. theme changes) to all connected clients."""
        try:
            self.history.append(data)
        except Exception:
            pass

        if not self.active_sockets or not self.loop:
            return

        payload = json.dumps(data)

        async def _send_all():
            dead_sockets = set()
            for ws in self.active_sockets:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead_sockets.add(ws)
            self.active_sockets.difference_update(dead_sockets)

        asyncio.run_coroutine_threadsafe(_send_all(), self.loop)

    def get_history(self) -> List[dict]:
        """Retrieve all recorded telemetry events from the current session."""
        return list(self.history)

    def start_in_background(self) -> None:
        """Launch the telemetry server on a daemon background thread."""
        if not FASTAPI_AVAILABLE:
            return

        available_port = find_available_port(self.requested_port)
        if available_port is None:
            # Cannot bind any telemetry port, skip gracefully without crashing swarm
            return
        self.port = available_port

        app = FastAPI(title="OctoFlow 3D Telemetry Bridge")

        @app.websocket("/ws/telemetry")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            self.active_sockets.add(websocket)
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.active_sockets.discard(websocket)

        @app.get("/llm/pool")
        async def get_llm_pool():
            cfg_file = Path.home() / ".octoflow" / "config.json"
            cfg_data = {}
            if cfg_file.exists():
                try:
                    cfg_data = json.loads(cfg_file.read_text(encoding="utf-8"))
                except Exception:
                    cfg_data = {}
            raw_pool = cfg_data.get("llm_pool", [])
            safe_entries = []
            for item in raw_pool:
                copy_item = dict(item)
                raw_k = copy_item.get("api_key") or ""
                if len(raw_k) > 6:
                    copy_item["masked_key"] = raw_k[:3] + "..." + raw_k[-4:]
                elif raw_k:
                    copy_item["masked_key"] = "***"
                else:
                    copy_item["masked_key"] = "(none / local)"
                copy_item["has_key"] = bool(raw_k)
                copy_item.pop("api_key", None)
                safe_entries.append(copy_item)
            return {"pool": safe_entries}

        @app.post("/llm/pool")
        async def post_llm_pool(payload: dict):
            cfg_dir = Path.home() / ".octoflow"
            cfg_dir.mkdir(parents=True, exist_ok=True)
            cfg_file = cfg_dir / "config.json"
            cfg_data = {}
            if cfg_file.exists():
                try:
                    cfg_data = json.loads(cfg_file.read_text(encoding="utf-8"))
                except Exception:
                    cfg_data = {}

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
            cfg_file.write_text(json.dumps(cfg_data, indent=2), encoding="utf-8")
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

        # Serve visualizer dist if exists (bundled package dist or local dev dist)
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
                    "<h1>🐙 OctoFlow 3D Telemetry Server Active</h1>"
                    f"<p>WebSocket streaming on <code>ws://localhost:{self.port}/ws/telemetry</code></p>"
                    "<p>Run <code>npm run build</code> in <code>visualizer/</code> to load the 3D connectome canvas.</p>"
                    "</body></html>"
                )

        def _run():
            try:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
                config = uvicorn.Config(app=app, host="0.0.0.0", port=self.port, log_level="error")
                server = uvicorn.Server(config)
                self.loop.run_until_complete(server.serve())
            except Exception:
                pass

        self.server_thread = threading.Thread(target=_run, daemon=True)
        self.server_thread.start()
