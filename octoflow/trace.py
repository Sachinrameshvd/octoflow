"""OctoFlow Execution Trace & Replay Engine.

Records structured execution traces to ~/.octoflow/runs/<id>/trace.jsonl (mode 0600):
- Gate evaluations: arm_id, cycle, sensory surprise ΔS, threshold θ, decision (reflex vs escalate)
- Tool calls: arm_id, tool_name, sanitized arguments, return code, outcome, duration
- Provider requests: provider, model, token usage, latency_ms, status (metadata only by default)
- Prompts/Responses: only included when --trace-prompts is explicitly enabled (redacted)
- Telemetry events: real-time state, coalition bindings, and quiescence

Replays recorded traces back into the terminal and the 3D connectome visualizer bridge.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from octoflow.checkpoint import get_runs_dir
from octoflow.conductor import SwarmTelemetryEvent
from octoflow.logging_config import get_logger
from octoflow.provider import redact_secrets

logger = get_logger("trace")


@dataclass
class TraceEvent:
    """A single atomic trace event recorded in trace.jsonl."""

    timestamp: float
    event_type: str  # gate_eval, tool_call, provider_request, telemetry, mission_start, mission_end
    payload: dict[str, Any]

    def to_json_line(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


class TraceLogger:
    """Manages appending sanitized trace events to ~/.octoflow/runs/<id>/trace.jsonl."""

    def __init__(
        self,
        run_id: str,
        enabled: bool = False,
        trace_prompts: bool = False,
        base_dir: Path | None = None,
    ) -> None:
        self.run_id = run_id
        self.enabled = enabled or (os.getenv("OCTOFLOW_TRACE") == "1")
        self.trace_prompts = trace_prompts or (os.getenv("OCTOFLOW_TRACE_PROMPTS") == "1")
        self.base_dir = base_dir or get_runs_dir()
        self.run_dir = self.base_dir / self.run_id
        self.trace_file = self.run_dir / "trace.jsonl"
        self._initialized = False

    def _ensure_init(self) -> None:
        if self._initialized or not self.enabled:
            return
        self.run_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.run_dir.chmod(0o700)
        except OSError:
            pass

        if not self.trace_file.exists():
            self.trace_file.touch(mode=0o600)
        else:
            try:
                self.trace_file.chmod(0o600)
            except OSError:
                pass
        self._initialized = True

    def _sanitize_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Deeply sanitize dictionaries to mask secrets and bound size."""
        clean: dict[str, Any] = {}
        for k, v in data.items():
            k_lower = str(k).lower()

            # Filter prompt and response text if trace_prompts is disabled
            if not self.trace_prompts:
                if k_lower in (
                    "prompt",
                    "prompts",
                    "system_prompt",
                    "user_prompt",
                    "messages",
                    "response_content",
                    "response_text",
                    "llm_prompt",
                    "llm_response",
                ):
                    continue

            # Redact known credentials (avoid false positives on token count metrics)
            is_credential = False
            if k_lower in ("key", "token", "secret", "password", "auth"):
                is_credential = True
            elif any(
                term in k_lower
                for term in (
                    "api_key",
                    "apikey",
                    "secret_key",
                    "auth_token",
                    "access_token",
                    "bearer",
                    "password",
                    "private_key",
                    "authorization",
                )
            ):
                is_credential = True

            if is_credential:
                clean[k] = "[REDACTED_CREDENTIAL]"
                continue

            if isinstance(v, str):
                redacted = redact_secrets(v)
                # Cap extremely large payloads (e.g. giant file contents) in traces to 2000 chars
                if len(redacted) > 2000:
                    clean[k] = redacted[:2000] + f"... [Truncated: {len(redacted)} chars total]"
                else:
                    clean[k] = redacted
            elif isinstance(v, dict):
                clean[k] = self._sanitize_dict(v)
            elif isinstance(v, list):
                clean[k] = [
                    self._sanitize_dict(item)
                    if isinstance(item, dict)
                    else (redact_secrets(str(item)) if isinstance(item, str) else item)
                    for item in v
                ]
            else:
                clean[k] = v
        return clean

    def log_event(self, event_type: str, payload: dict[str, Any]) -> None:
        """Append an arbitrary sanitized event to trace.jsonl."""
        if not self.enabled:
            return

        self._ensure_init()
        clean_payload = self._sanitize_dict(payload)
        event = TraceEvent(
            timestamp=round(time.time(), 4),
            event_type=event_type,
            payload=clean_payload,
        )

        try:
            with self.trace_file.open("a", encoding="utf-8") as f:
                f.write(event.to_json_line() + "\n")
            try:
                self.trace_file.chmod(0o600)
            except OSError:
                pass
        except Exception as e:
            logger.debug("Failed writing trace event: %s", e)

    def log_gate_eval(
        self,
        arm_id: int,
        cycle: int,
        surprise: float,
        threshold: float,
        decision: str,
        role: str = "",
        **kwargs: Any,
    ) -> None:
        """Record Active Inference sensory gate evaluation."""
        self.log_event(
            "gate_eval",
            {
                "arm_id": arm_id,
                "role": role,
                "cycle": cycle,
                "surprise": round(float(surprise), 4),
                "threshold": round(float(threshold), 4),
                "decision": decision,
                **kwargs,
            },
        )

    def log_tool_call(
        self,
        arm_id: int,
        tool_name: str,
        args: dict[str, Any],
        success: bool,
        returncode: int = 0,
        elapsed_ms: float = 0.0,
        role: str = "",
        error: str | None = None,
    ) -> None:
        """Record arm tool execution and sandbox response."""
        self.log_event(
            "tool_call",
            {
                "arm_id": arm_id,
                "role": role,
                "tool_name": tool_name,
                "arguments": args,
                "success": bool(success),
                "returncode": int(returncode),
                "elapsed_ms": round(float(elapsed_ms), 2),
                "error": error,
            },
        )

    def log_provider_request(
        self,
        provider: str,
        model: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        latency_ms: float = 0.0,
        status: str = "success",
        prompt: str | None = None,
        response: str | None = None,
    ) -> None:
        """Record LLM provider interaction metadata (and prompts only if trace_prompts=True)."""
        data: dict[str, Any] = {
            "provider": provider,
            "model": model,
            "prompt_tokens": int(prompt_tokens),
            "completion_tokens": int(completion_tokens),
            "total_tokens": int(total_tokens),
            "latency_ms": round(float(latency_ms), 2),
            "status": status,
        }
        if self.trace_prompts:
            if prompt is not None:
                data["prompt"] = prompt
            if response is not None:
                data["response_content"] = response

        self.log_event("provider_request", data)

    def log_telemetry(self, event: SwarmTelemetryEvent) -> None:
        """Record real-time swarm telemetry broadcast."""
        try:
            data = event.model_dump()
            self.log_event("telemetry", data)
        except Exception as e:
            logger.debug("Failed serializing telemetry for trace: %s", e)


_GLOBAL_TRACER: TraceLogger | None = None


def get_active_tracer() -> TraceLogger | None:
    """Retrieve global active tracer instance."""
    return _GLOBAL_TRACER


def set_active_tracer(tracer: TraceLogger | None) -> None:
    """Set global active tracer instance."""
    global _GLOBAL_TRACER
    _GLOBAL_TRACER = tracer


def init_tracer(
    run_id: str,
    enabled: bool = False,
    trace_prompts: bool = False,
    base_dir: Path | None = None,
) -> TraceLogger:
    """Initialize and set the global tracer singleton."""
    tracer = TraceLogger(
        run_id=run_id,
        enabled=enabled,
        trace_prompts=trace_prompts,
        base_dir=base_dir,
    )
    set_active_tracer(tracer)
    return tracer


# ==============================================================================
# Replay Engine
# ==============================================================================


def find_trace_file(run_id: str | None = None, base_dir: Path | None = None) -> tuple[str, Path]:
    """Find trace.jsonl for specified run_id or the latest available run."""
    runs_dir = base_dir or get_runs_dir()

    if run_id and run_id.strip() and run_id.strip() != "latest":
        target = runs_dir / run_id / "trace.jsonl"
        if not target.exists():
            raise FileNotFoundError(f"Trace log not found for run '{run_id}': {target}")
        return run_id, target

    # Resolve latest
    latest_id_file = runs_dir / "latest_run_id"
    if latest_id_file.exists():
        lid = latest_id_file.read_text(encoding="utf-8").strip()
        candidate = runs_dir / lid / "trace.jsonl"
        if candidate.exists():
            return lid, candidate

    candidates = sorted(
        runs_dir.glob("*/trace.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise FileNotFoundError(f"No execution traces found under {runs_dir}")

    resolved_id = candidates[0].parent.name
    return resolved_id, candidates[0]


def load_trace_events(trace_file: Path) -> list[dict[str, Any]]:
    """Load and parse JSON lines from a trace.jsonl file."""
    events: list[dict[str, Any]] = []
    with trace_file.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                events.append(json.loads(line_str))
            except json.JSONDecodeError as e:
                logger.warning("Corrupt JSON on trace line %d: %s", idx, e)
    return events


def format_replay_line(event: dict[str, Any]) -> str:
    """Format a single trace event as a clear, plain terminal line."""
    ts = event.get("timestamp", 0.0)
    etype = event.get("event_type", "unknown")
    p = event.get("payload", {})

    time_str = time.strftime("%H:%M:%S", time.localtime(ts)) if ts else "--:--:--"

    if etype == "gate_eval":
        arm = p.get("arm_id", 0)
        role = p.get("role", f"Arm-{arm}")
        cycle = p.get("cycle", 1)
        surprise = p.get("surprise", 0.0)
        threshold = p.get("threshold", 0.5)
        decision = p.get("decision", "unknown").upper()
        glyph = "●" if decision == "ESCALATE" else "○"
        return f"[{time_str}] GATE {glyph} Arm {arm} [{role}] cycle={cycle} ΔS={surprise:.3f} (θ={threshold:.3f}) -> {decision}"

    elif etype == "tool_call":
        arm = p.get("arm_id", 0)
        tool = p.get("tool_name", "tool")
        status = "SUCCESS" if p.get("success") else f"FAILED (rc={p.get('returncode', 1)})"
        elapsed = p.get("elapsed_ms", 0.0)
        args_str = json.dumps(p.get("arguments", {}), ensure_ascii=False)
        if len(args_str) > 80:
            args_str = args_str[:77] + "..."
        return f"[{time_str}] TOOL ◈ Arm {arm} {tool}({args_str}) -> {status} ({elapsed:.1f}ms)"

    elif etype == "provider_request":
        prov = p.get("provider", "llm")
        mod = p.get("model", "")
        toks = p.get("total_tokens", 0)
        lat = p.get("latency_ms", 0.0)
        status = p.get("status", "ok")
        return f"[{time_str}] LLM  ◈ {prov}:{mod} tokens={toks} latency={lat:.1f}ms status={status}"

    elif etype == "telemetry":
        sub_type = p.get("event_type", "EVENT")
        arm = p.get("arm_id", 0)
        role = p.get("role", "")
        summary = p.get("summary", "")
        cycle = p.get("cycle", 1)
        return f"[{time_str}] TELEMETRY ◈ {sub_type} Arm {arm} [{role}] cycle={cycle} - {summary}"

    elif etype == "mission_start":
        obj = p.get("objective", "")
        mode = p.get("mode", "software_dev")
        return f"[{time_str}] MISSION START ◈ Mode: {mode} | Objective: {obj}"

    elif etype == "mission_end":
        outcome = p.get("outcome", "complete")
        exec_time = p.get("execution_time", 0.0)
        return f"[{time_str}] MISSION END ◈ Outcome: {outcome.upper()} (elapsed: {exec_time:.2f}s)"

    return f"[{time_str}] {etype.upper()} ◈ {json.dumps(p)}"


def replay_trace(
    run_id: str | None = None,
    speed: float = 1.0,
    no_visualizer: bool = False,
    port: int = 8088,
    host: str = "127.0.0.1",
    base_dir: Path | None = None,
    output_fn: Callable[[str], None] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Replay a recorded run trace into the terminal and 3D visualizer.

    Returns:
        (resolved_run_id, replayed_events_list)
    """
    resolved_id, trace_path = find_trace_file(run_id=run_id, base_dir=base_dir)
    events = load_trace_events(trace_path)

    out = output_fn or print

    out(f"◈ OctoFlow Replay: Run [{resolved_id}] ({len(events)} events, speed={speed}x)")
    out(f"• Trace source: {trace_path}")
    if no_visualizer:
        out("• Visualizer broadcast: disabled (--no-visualizer)")
    else:
        out(f"• Visualizer bridge: http://{host}:{port} (ws://{host}:{port}/ws/telemetry)")
    out("-" * 78)

    broadcaster = None
    if not no_visualizer:
        try:
            from octoflow.server import TelemetryBroadcaster

            broadcaster = TelemetryBroadcaster(port=port, host=host)
            broadcaster.start_in_background()
        except Exception as e:
            logger.debug("Could not start visualizer broadcaster during replay: %s", e)

    last_ts: float | None = None
    replayed: list[dict[str, Any]] = []

    for evt in events:
        replayed.append(evt)
        line = format_replay_line(evt)
        out(line)

        # Broadcast telemetry into visualizer if present
        if broadcaster is not None:
            etype = evt.get("event_type")
            p = evt.get("payload", {})
            if etype == "telemetry":
                try:
                    telemetry_obj = SwarmTelemetryEvent(**p)
                    broadcaster.broadcast(telemetry_obj)
                except Exception:
                    broadcaster.broadcast_raw(p)
            elif etype in ("gate_eval", "tool_call", "provider_request"):
                broadcaster.broadcast_raw({"type": f"REPLAY_{etype.upper()}", **p})

        # Pacing: delay proportional to original event timestamps
        ts = evt.get("timestamp")
        if speed > 0 and last_ts is not None and ts is not None and ts > last_ts:
            dt = (ts - last_ts) / speed
            sleep_time = min(dt, 0.5)  # Cap sleep at 0.5s per step to avoid long stalls
            if sleep_time > 0.005:
                time.sleep(sleep_time)
        last_ts = ts

    out("-" * 78)
    out(f"✔ Replay of run [{resolved_id}] completed ({len(replayed)} events rendered).")

    if broadcaster is not None:
        try:
            broadcaster.stop()
        except Exception:
            pass

    return resolved_id, replayed
