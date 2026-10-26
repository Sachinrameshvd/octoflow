"""ArmAgent: Autonomous Peripheral Arm Ganglion Worker.

Wraps an LLM provider, local workspace tool sandbox, CodeSensoryEncoder,
SurpriseGate, and InterBrachialBus into an autonomous, silent execution agent.
"""

import json
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import numpy as np

from octoflow.config import ArmRoleConfig
from octoflow.encoder import CodeSensoryEncoder, get_encoder
from octoflow.gate import SurpriseGate
from octoflow.tools import ToolResult, WorkspaceSandbox
from octoflow.bus import InterBrachialBus, BrachialMessage
from octoflow.memory import VerticalLobeMemory
from octoflow.provider import BaseLLMProvider, LLMResponse
from octoflow.logging_config import get_logger

logger = get_logger("arm")


class ArmStepResult(BaseModel):
    """Telemetry and outcome of a single arm execution step."""
    arm_id: int
    role: str
    status: str  # "SILENT_WORKING", "ESCALATED", "COALITION_BOUND", "QUIESCENT"
    tool_name: str
    tool_target: str
    success: bool
    surprise: float
    threshold: float
    escalated: bool
    quiescent: bool
    explanation: str = ""
    tokens_used: int = 0
    cost_dollars: float = 0.0


class ArmAgent:
    """Autonomous arm agent with event-triggered sensory surprise gating."""

    def __init__(
        self,
        role_config: ArmRoleConfig,
        sandbox: WorkspaceSandbox,
        provider: BaseLLMProvider,
        bus: InterBrachialBus,
        memory: VerticalLobeMemory,
        encoder: Optional[CodeSensoryEncoder] = None,
        obs_dim: int = 16,
        hidden_dim: int = 64,
    ):
        self.role = role_config
        self.arm_id = role_config.arm_id
        self.sandbox = sandbox
        self.provider = provider
        self.bus = bus
        self.memory = memory
        self.encoder = encoder or get_encoder(obs_dim=obs_dim)

        self.gate = SurpriseGate(
            arm_id=self.arm_id,
            obs_dim=obs_dim,
            initial_threshold=role_config.initial_threshold,
            backend=getattr(self.encoder, "backend", "numpy"),
        )

        self.status = "IDLE"
        self.step_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.is_quiescent = False

        # Sensory Saccade Buffer: retains only the last 3 tool cycles to prevent token bloat
        self.saccade_buffer: List[Dict[str, Any]] = []
        self.compacted_summary: str = ""

        # Recurrent state vector
        self.hidden_state = np.zeros((1, hidden_dim), dtype=np.float32)

    def compact_context(self, max_buffer_size: int = 4) -> str:
        """Prune and compact older execution history steps into a condensed memory synopsis."""
        if len(self.saccade_buffer) <= max_buffer_size:
            return self.compacted_summary

        older_steps = self.saccade_buffer[:-3]
        self.saccade_buffer = self.saccade_buffer[-3:]

        bullets = []
        for s in older_steps:
            st = "SUCCESS" if s.get("success") else "FAIL"
            bullets.append(f"• Step {s.get('step')}: {s.get('action')} ({st}) -> {s.get('summary', '')[:80]}")

        new_synopsis = "\n".join(bullets)
        if self.compacted_summary:
            self.compacted_summary += "\n" + new_synopsis
        else:
            self.compacted_summary = new_synopsis

        return self.compacted_summary

    def _build_system_prompt(self) -> str:
        domain_str = ", ".join(self.role.workspace_domain) or "workspace root"
        return (
            f"You are {self.role.title} (Arm {self.arm_id}) in the OctoFlow cephalopod swarm.\n"
            f"Role Description: {self.role.description}\n"
            f"Your Assigned Domain: {domain_str}\n"
            f"Rule 1: Execute actions using ONLY the requested JSON structure.\n"
            f"Rule 2: Available actions: 'write_file', 'read_file', 'run_command', 'mark_quiescent'.\n"
            f"Rule 3: Execute tasks efficiently and silently. Do not output conversational text.\n"
            f"JSON format example:\n"
            f'{{"action": "write_file", "path": "models/user.py", "content": "class User: pass", "explanation": "Creating user model"}}\n'
            f'or {{"action": "run_command", "command": "pytest tests/", "explanation": "Running test suite"}}\n'
            f'or {{"action": "mark_quiescent", "explanation": "All objectives satisfied"}}'
        )

    def _parse_llm_action(self, text: str) -> Dict[str, Any]:
        """Extract structured action JSON from LLM text, handling markdown blocks and formatting quirks."""
        cleaned = text.strip()
        # Strip markdown fences
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if fence_match:
            candidate = fence_match.group(1)
        else:
            first_brace = cleaned.find("{")
            last_brace = cleaned.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                candidate = cleaned[first_brace:last_brace + 1]
            else:
                candidate = cleaned

        # Attempt standard JSON parse
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and "action" in parsed:
                return self._sanitize_action_dict(parsed)
        except Exception as e:
            logger.debug("Candidate text is not valid standard JSON: %s", e, exc_info=True)  # best-effort: model output may be free-form text

        # Try repairing trailing commas
        try:
            repaired = re.sub(r",\s*([\}\]])", r"\1", candidate)
            parsed = json.loads(repaired)
            if isinstance(parsed, dict) and "action" in parsed:
                return self._sanitize_action_dict(parsed)
        except Exception as e:
            logger.debug("Repaired candidate text is not valid JSON: %s", e, exc_info=True)  # best-effort: falling back to heuristic classification

        # Fallback heuristic
        lowered = text.lower()
        if "quiescent" in lowered or "all objectives satisfied" in lowered or "task complete" in lowered:
            return {"action": "mark_quiescent", "explanation": "Marking complete via text heuristic"}

        if "def " in text or "import " in text or "<html" in text or "FROM " in text:
            fname = "app.py"
            if "<html" in text:
                fname = "index.html"
            elif "FROM " in text:
                fname = "Dockerfile"
            return self._sanitize_action_dict({
                "action": "write_file",
                "path": fname,
                "content": text,
                "explanation": "Extracted code from direct LLM output",
            })

        return {"action": "read_file", "path": "README.md", "explanation": "Fallback inspection"}

    def _sanitize_action_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize action dictionary keys and paths."""
        action = str(data.get("action", "read_file")).strip()
        data["action"] = action
        if "path" in data and isinstance(data["path"], str):
            clean_path = data["path"].strip().strip("'\"").lstrip("/\\")
            data["path"] = clean_path or "output.txt"
        if "command" in data and isinstance(data["command"], str):
            data["command"] = data["command"].strip()
        return data

    def step(
        self,
        sub_goal: str,
        coalition_context: Optional[str] = None,
        max_steps: int = 15,
    ) -> ArmStepResult:
        """Execute one autonomous reasoning and tool execution cycle."""
        self.step_count += 1

        # 1. Check lateral messages from ring neighbors
        inbox = self.bus.poll_inbox(self.arm_id)
        lateral_notes = ""
        if inbox:
            lateral_notes = "Lateral Ring Messages:\n" + "\n".join(
                f"- [From Arm {m.sender_id} | {m.intent}]: {m.summary}" for m in inbox
            )

        # 2. Check Vertical Lobe LTP for any recalled guidance on last error
        recalled_guidance = ""
        if self.gate.surprise_history and self.gate.surprise_history[-1] > 0.40:
            last_obs = self.encoder.encode(
                ToolResult(tool_name="prev", target="", success=False, returncode=1, stderr="error"),
                as_tensor=False,
            )
            recalled = self.memory.recall(last_obs)
            if recalled:
                recalled_guidance = f"\n[Vertical Lobe LTP Fast-Recall]: {recalled[0]}"

        # 3. Compact earlier cycles and construct concise prompt
        self.compact_context()
        compacted_block = f"\n[Compacted Synaptic Memory of Earlier Cycles]:\n{self.compacted_summary}" if self.compacted_summary else ""
        recent_history = "\n".join(
            f"Step {s['step']}: {s['action']} -> {'SUCCESS' if s['success'] else 'FAIL'}: {s['summary']}"
            for s in self.saccade_buffer[-2:]
        )

        recent_history_block = f"Recent Tool History:\n{recent_history}\n" if recent_history else ""
        prompt = (
            f"Current Arm Objective: {sub_goal}\n"
            f"{f'Active Coalition Context: {coalition_context}' if coalition_context else ''}\n"
            f"{lateral_notes}\n"
            f"{recalled_guidance}\n"
            f"{compacted_block}\n"
            f"{recent_history_block}"
            f"Choose your next tool action in JSON:"
        )

        # 4. Generate LLM action with biophysically modulated temperature
        system_prompt = self._build_system_prompt()
        last_surprise = self.gate.surprise_history[-1] if self.gate.surprise_history else 0.0
        dyn_temp, _ = self.gate.compute_generation_parameters(last_surprise)
        llm_resp: LLMResponse = self.provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=dyn_temp,
        )
        self.total_tokens += llm_resp.total_tokens
        self.total_cost += llm_resp.estimated_cost_dollars

        action_data = self._parse_llm_action(llm_resp.content)
        action_type = action_data.get("action", "read_file")
        explanation = action_data.get("explanation", "")

        # 5. Execute action inside sandbox
        tool_result = ToolResult(tool_name="noop", target="", success=True)
        if action_type == "write_file":
            path = action_data.get("path", "temp.py")
            content = action_data.get("content", "")
            try:
                with self.sandbox.file_lock(path, self.arm_id):
                    tool_result = self.sandbox.write_file(path, content, arm_id=self.arm_id)
            except Exception as e:
                tool_result = ToolResult(tool_name="write_file", target=path, success=False, returncode=1, stderr=str(e), error=str(e))
        elif action_type == "read_file":
            path = action_data.get("path", "README.md")
            tool_result = self.sandbox.read_file(path)
        elif action_type == "run_command":
            cmd = action_data.get("command", "ls")
            tool_result = self.sandbox.run_command(cmd)
        elif action_type == "mark_quiescent":
            self.is_quiescent = True
            tool_result = ToolResult(
                tool_name="mark_quiescent",
                target=sub_goal,
                success=True,
                returncode=0,
                stdout="Sub-goal completed.",
            )

        # 6. Encode into sensory observation & evaluate Surprise Gate
        obs = self.encoder.encode(
            result=tool_result,
            step=self.step_count,
            max_steps=max_steps,
        )

        escalate, surprise, telemetry = self.gate.evaluate(actual_obs=obs, tool_result=tool_result)

        # 7. Update status
        if self.is_quiescent or (tool_result.success and not escalate and not coalition_context and tool_result.tool_name == "write_file"):
            self.is_quiescent = True
            self.status = "QUIESCENT"
        elif escalate:
            self.status = "ESCALATED"
            # Consolidate pattern in Vertical Lobe if it's an actionable failure
            if tool_result.stderr:
                self.memory.consolidate(
                    error_obs=obs.numpy() if hasattr(obs, "numpy") else obs,
                    error_name=f"Arm {self.arm_id} Error",
                    fix_guidance=f"Inspect tool failure: {tool_result.stderr[:200]}",
                )
        elif coalition_context:
            self.status = "COALITION_BOUND"
        else:
            self.status = "SILENT_WORKING"

        # 8. Saccade buffer management (keep last 3)
        self.saccade_buffer.append({
            "step": self.step_count,
            "action": action_type,
            "success": tool_result.success,
            "summary": (tool_result.stdout or tool_result.stderr)[:150],
        })
        if len(self.saccade_buffer) > 3:
            self.saccade_buffer.pop(0)

        return ArmStepResult(
            arm_id=self.arm_id,
            role=self.role.title,
            status=self.status,
            tool_name=tool_result.tool_name,
            tool_target=tool_result.target,
            success=tool_result.success,
            surprise=surprise,
            threshold=self.gate.threshold,
            escalated=escalate,
            quiescent=self.is_quiescent,
            explanation=explanation,
            tokens_used=llm_resp.total_tokens,
            cost_dollars=llm_resp.estimated_cost_dollars,
        )

    async def astep(
        self,
        sub_goal: str,
        coalition_context: Optional[str] = None,
        max_steps: int = 15,
    ) -> ArmStepResult:
        """Asynchronously execute one autonomous reasoning and tool execution cycle."""
        self.step_count += 1

        # 1. Check lateral messages from ring neighbors
        inbox = self.bus.poll_inbox(self.arm_id)
        lateral_notes = ""
        if inbox:
            lateral_notes = "Lateral Ring Messages:\n" + "\n".join(
                f"- [From Arm {m.sender_id} | {m.intent}]: {m.summary}" for m in inbox
            )

        # 2. Check Vertical Lobe LTP for any recalled guidance on last error
        recalled_guidance = ""
        if self.gate.surprise_history and self.gate.surprise_history[-1] > 0.40:
            last_obs = self.encoder.encode(
                ToolResult(tool_name="prev", target="", success=False, returncode=1, stderr="error"),
                as_tensor=False,
            )
            recalled = self.memory.recall(last_obs)
            if recalled:
                recalled_guidance = f"\n[Vertical Lobe LTP Fast-Recall]: {recalled[0]}"

        # 3. Construct concise prompt
        recent_history = "\n".join(
            f"Step {s['step']}: {s['action']} -> {'SUCCESS' if s['success'] else 'FAIL'}: {s['summary']}"
            for s in self.saccade_buffer[-2:]
        )

        recent_history_block = f"Recent Tool History:\n{recent_history}\n" if recent_history else ""
        prompt = (
            f"Current Arm Objective: {sub_goal}\n"
            f"{f'Active Coalition Context: {coalition_context}' if coalition_context else ''}\n"
            f"{lateral_notes}\n"
            f"{recalled_guidance}\n"
            f"{recent_history_block}"
            f"Choose your next tool action in JSON:"
        )

        # 4. Asynchronously generate LLM action with biophysically modulated temperature
        system_prompt = self._build_system_prompt()
        last_surprise = self.gate.surprise_history[-1] if self.gate.surprise_history else 0.0
        dyn_temp, _ = self.gate.compute_generation_parameters(last_surprise)
        llm_resp: LLMResponse = await self.provider.agenerate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=dyn_temp,
            max_tokens=512,
        )
        self.total_tokens += llm_resp.total_tokens
        self.total_cost += llm_resp.estimated_cost_dollars

        action_data = self._parse_llm_action(llm_resp.content)
        action_type = action_data.get("action", "read_file")
        explanation = action_data.get("explanation", "")

        # 5. Asynchronously execute action inside sandbox
        tool_result = ToolResult(tool_name="noop", target="", success=True)
        try:
            if action_type == "write_file":
                path = action_data.get("path", "temp.py")
                content = action_data.get("content", "")
                try:
                    with self.sandbox.file_lock(path, self.arm_id):
                        tool_result = await self.sandbox.awrite_file(path, content, arm_id=self.arm_id)
                except Exception as e:
                    tool_result = ToolResult(tool_name="write_file", target=path, success=False, returncode=1, stderr=str(e), error=str(e))
            elif action_type == "read_file":
                path = action_data.get("path", "README.md")
                tool_result = await self.sandbox.aread_file(path)
            elif action_type == "run_command":
                cmd = action_data.get("command", "ls")
                tool_result = await self.sandbox.arun_command(cmd)
            elif action_type == "list_dir":
                path = action_data.get("path", ".")
                tool_result = await self.sandbox.alist_dir(path)
            elif action_type == "mark_quiescent":
                self.is_quiescent = True
                tool_result = ToolResult(
                    tool_name="mark_quiescent",
                    target=sub_goal,
                    success=True,
                    returncode=0,
                    stdout="Sub-goal completed.",
                )
        except Exception as e:
            tool_result = ToolResult(
                tool_name=action_type,
                target=action_data.get("path", action_data.get("command", "error")),
                success=False,
                returncode=1,
                stderr=str(e),
                explanation=f"Error executing {action_type}: {e}",
            )

        # 6. Encode into sensory observation & evaluate Surprise Gate
        obs = self.encoder.encode(
            result=tool_result,
            step=self.step_count,
            max_steps=max_steps,
        )

        escalate, surprise, telemetry = self.gate.evaluate(actual_obs=obs, tool_result=tool_result)

        # 7. Update status
        if self.is_quiescent or (tool_result.success and not escalate and not coalition_context and tool_result.tool_name == "write_file"):
            self.is_quiescent = True
            self.status = "QUIESCENT"
        elif escalate:
            self.status = "ESCALATED"
            if tool_result.stderr:
                self.memory.consolidate(
                    error_obs=obs.numpy() if hasattr(obs, "numpy") else obs,
                    error_name=f"Arm {self.arm_id} Error",
                    fix_guidance=f"Inspect tool failure: {tool_result.stderr[:200]}",
                )
        elif coalition_context:
            self.status = "COALITION_BOUND"
        else:
            self.status = "SILENT_WORKING"

        # 8. Saccade buffer management
        self.saccade_buffer.append({
            "step": self.step_count,
            "action": action_type,
            "success": tool_result.success,
            "summary": (tool_result.stdout or tool_result.stderr)[:150],
        })
        if len(self.saccade_buffer) > 3:
            self.saccade_buffer.pop(0)

        return ArmStepResult(
            arm_id=self.arm_id,
            role=self.role.title,
            status=self.status,
            tool_name=tool_result.tool_name,
            tool_target=tool_result.target,
            success=tool_result.success,
            surprise=surprise,
            threshold=self.gate.threshold,
            escalated=escalate,
            quiescent=self.is_quiescent,
            explanation=explanation,
            tokens_used=llm_resp.total_tokens,
            cost_dollars=llm_resp.estimated_cost_dollars,
        )

    def answer_query(self, query: str, context: Optional[str] = None) -> str:
        """Answer a direct developer question or code review query using specialist domain grounding."""
        domain_str = ", ".join(self.role.workspace_domain) or "workspace root"
        recent_actions = ""
        if self.saccade_buffer:
            recent_actions = "Recent Actions Performed:\n" + "\n".join(
                f"- Step {s['step']}: {s['action']} (success: {s['success']}) - {s['summary']}"
                for s in self.saccade_buffer
            )

        bus_messages = ""
        if hasattr(self.bus, "messages") and self.bus.messages:
            bus_messages = "Inter-Brachial Bus Context:\n" + "\n".join(
                f"- Arm {m.sender_arm}: {m.content[:120]}"
                for m in self.bus.messages[-4:]
            )

        system_prompt = (
            f"You are {self.role.title} (Arm {self.arm_id}) in the OctoFlow cephalopod swarm.\n"
            f"Specialty: {self.role.description}\n"
            f"Domain Scope: {domain_str}\n"
            f"You are speaking 1-on-1 with the developer in the terminal cockpit.\n"
            f"Answer with authoritative technical insight as the specialist who designed, built, or verified this domain.\n"
            f"Reference specific files, contracts, patterns, and tradeoffs where appropriate.\n"
            f"Be concise, clear, and direct. Do not output JSON; output natural markdown explanation."
        )

        user_content = f"Developer Question:\n{query}\n\n"
        if context:
            user_content += f"Codebase Context & Semantic Vectors:\n{context}\n\n"
        if recent_actions:
            user_content += f"{recent_actions}\n\n"
        if bus_messages:
            user_content += f"{bus_messages}\n\n"

        response = self.provider.generate(
            prompt=user_content,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=600,
        )
        return response.content.strip()

