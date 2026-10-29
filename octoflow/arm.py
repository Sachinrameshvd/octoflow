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
        gate_mode: str = "gated",
        temperature: Optional[float] = None,
    ):
        self.role = role_config
        self.arm_id = role_config.arm_id
        self.sandbox = sandbox
        self.provider = provider
        self.bus = bus
        self.memory = memory
        self.encoder = encoder or get_encoder(obs_dim=obs_dim)
        self.temperature = temperature

        self.gate = SurpriseGate(
            arm_id=self.arm_id,
            obs_dim=obs_dim,
            initial_threshold=role_config.initial_threshold,
            backend=getattr(self.encoder, "backend", "numpy"),
            gate_mode=gate_mode,
        )

        self.status = "IDLE"
        self.step_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.is_quiescent = False
        self.budget_tracker: Optional[Any] = None

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
        is_qa = any(kw in self.role.name.lower() or kw in self.role.title.lower() for kw in ("test", "qa"))
        role_notes = (
            "- For QA & Testing: Write test suites in test_<module>.py (do NOT overwrite the implementation file). Run pytest using run_command to verify tests pass.\n"
            if is_qa else
            "- For Implementation: Write the module file with complete code and all required imports. Never emit placeholders or unclosed strings.\n"
        )
        return (
            f"You are {self.role.title} (Arm {self.arm_id}) in the OctoFlow swarm.\n"
            f"Role: {self.role.description}\n"
            f"Workspace Root: All file paths are relative to workspace root (e.g. 'limiter.py', 'app.py', 'test_app.py').\n"
            f"Assigned Domain: {domain_str}\n\n"
            f"Allowed Tools (respond with ONLY a JSON object):\n"
            f"1. write_file: {{\"action\": \"write_file\", \"path\": \"relative/path.py\", \"content\": \"...\", \"explanation\": \"...\"}}\n"
            f"   - Write complete, robust, self-contained Python code without placeholders. Always include all required standard library imports (e.g., import time, import threading).\n"
            f"2. read_file: {{\"action\": \"read_file\", \"path\": \"relative/path.py\", \"explanation\": \"...\"}}\n"
            f"3. run_command: {{\"action\": \"run_command\", \"command\": \"pytest -q <test_file>\", \"explanation\": \"...\"}}\n"
            f"4. list_dir: {{\"action\": \"list_dir\", \"path\": \".\", \"explanation\": \"...\"}}\n"
            f"5. mark_quiescent: {{\"action\": \"mark_quiescent\", \"explanation\": \"Task verified and complete.\"}}\n\n"
            f"Workflow Guidelines:\n"
            f"{role_notes}"
            f"- When all requirements and tests pass, emit {{\"action\": \"mark_quiescent\"}} as your explicit completion signal.\n"
            f"- Output strictly valid JSON."
        )

    def _parse_llm_action(self, text: str) -> Dict[str, Any]:
        """Extract structured action JSON from LLM text, handling markdown blocks, trailing commas, and formatting quirks."""
        cleaned = text.strip()
        if not cleaned:
            return {
                "action": "invalid_action",
                "error": "Empty response from model. Please output a valid tool action JSON object.",
            }

        # 1. Search for markdown code block containing JSON: ```json ... ``` or ``` ... ```
        candidate = None
        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if fence_match:
            candidate = fence_match.group(1).strip()
        else:
            first_brace = cleaned.find("{")
            last_brace = cleaned.rfind("}")
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                candidate = cleaned[first_brace:last_brace + 1].strip()

        if candidate:
            # Attempt 1: direct parse with strict=False to tolerate unescaped control chars
            try:
                parsed = json.loads(candidate, strict=False)
                if isinstance(parsed, dict):
                    return self._sanitize_action_dict(parsed)
            except Exception as e:
                logger.debug("Candidate text is not valid standard JSON: %s", e)

            # Attempt 2: trailing comma repair
            try:
                repaired = re.sub(r",\s*([\}\]])", r"\1", candidate)
                parsed = json.loads(repaired, strict=False)
                if isinstance(parsed, dict):
                    return self._sanitize_action_dict(parsed)
            except Exception as e:
                logger.debug("Repaired candidate text is not valid JSON: %s", e)

            # Attempt 3: single-quote evaluation if valid Python literal dict
            try:
                import ast
                val = ast.literal_eval(candidate)
                if isinstance(val, dict):
                    return self._sanitize_action_dict(val)
            except Exception:
                pass

        # 2. Heuristics for completion
        lowered = cleaned.lower()
        if "mark_quiescent" in lowered or "all objectives satisfied" in lowered or "task complete" in lowered or "all tests pass" in lowered:
            return {"action": "mark_quiescent", "explanation": "Marking complete via text heuristic"}

        # 3. Direct python code block fallback (if model dumped code without JSON wrapper)
        code_block_match = re.search(r"```(?:python|py)?\s*(.*?)\s*```", cleaned, re.DOTALL)
        if code_block_match:
            code_text = code_block_match.group(1).strip()
            if code_text and ("def " in code_text or "import " in code_text or "class " in code_text):
                fname = "main.py"
                if "test_" in code_text or "pytest" in code_text or "assert " in code_text:
                    fname = "test_main.py"
                return self._sanitize_action_dict({
                    "action": "write_file",
                    "path": fname,
                    "content": code_text,
                    "explanation": "Extracted code from direct LLM code block",
                })

        # 4. If unparseable, return invalid_action with corrective instructions
        snippet = cleaned[:200].replace("\n", " ")
        return {
            "action": "invalid_action",
            "error": f"Invalid tool format. Expected JSON like {{\"action\": \"write_file\", \"path\": \"...\", \"content\": \"...\"}} or {{\"action\": \"run_command\", \"command\": \"...\"}}. Received: '{snippet}'",
        }

    def _sanitize_action_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize keys, action names, and paths for structured actions."""
        key_aliases = {
            "tool": "action",
            "function": "action",
            "tool_name": "action",
            "name": "action",
            "file": "path",
            "filename": "path",
            "filepath": "path",
            "target": "path",
            "code": "content",
            "body": "content",
            "text": "content",
            "file_content": "content",
            "cmd": "command",
            "shell": "command",
            "exec": "command",
            "reason": "explanation",
            "desc": "explanation",
            "description": "explanation",
        }
        normalized: Dict[str, Any] = {}
        for k, v in data.items():
            norm_k = key_aliases.get(str(k).lower(), str(k).lower())
            if norm_k not in normalized:
                normalized[norm_k] = v

        action = str(normalized.get("action", "")).strip().lower()

        action_aliases = {
            "create_file": "write_file",
            "write": "write_file",
            "save_file": "write_file",
            "overwrite_file": "write_file",
            "cat": "read_file",
            "view_file": "read_file",
            "open_file": "read_file",
            "read": "read_file",
            "run": "run_command",
            "shell": "run_command",
            "bash": "run_command",
            "execute": "run_command",
            "exec": "run_command",
            "dir": "list_dir",
            "ls": "list_dir",
            "list_files": "list_dir",
            "done": "mark_quiescent",
            "complete": "mark_quiescent",
            "finish": "mark_quiescent",
            "stop": "mark_quiescent",
            "quiescent": "mark_quiescent",
        }
        action = action_aliases.get(action, action)
        normalized["action"] = action

        allowed_actions = {"write_file", "read_file", "run_command", "list_dir", "mark_quiescent"}
        if action not in allowed_actions:
            return {
                "action": "invalid_action",
                "error": f"Unknown tool '{action}'. Allowed tools: write_file, read_file, run_command, list_dir, mark_quiescent.",
                "raw": data,
            }

        if action == "write_file":
            path = str(normalized.get("path", "")).strip().strip("'\"").lstrip("/\\")
            normalized["path"] = path or "main.py"
            if "content" not in normalized:
                normalized["content"] = ""
            elif not isinstance(normalized["content"], str):
                normalized["content"] = str(normalized["content"])

        elif action == "read_file":
            path = str(normalized.get("path", "")).strip().strip("'\"").lstrip("/\\")
            normalized["path"] = path or "README.md"

        elif action == "run_command":
            cmd = str(normalized.get("command", "")).strip()
            if not cmd:
                return {
                    "action": "invalid_action",
                    "error": "Missing 'command' argument for run_command.",
                    "raw": data,
                }
            normalized["command"] = cmd

        elif action == "list_dir":
            path = str(normalized.get("path", ".")).strip().strip("'\"")
            normalized["path"] = path or "."

        return normalized

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

        # Workspace files overview
        existing_files = []
        try:
            for p in sorted(self.sandbox.root.iterdir()):
                if not p.name.startswith((".", "__")) and p.name not in ("venv", ".git"):
                    existing_files.append(p.name)
        except Exception:
            pass
        files_str = ", ".join(existing_files) if existing_files else "(empty workspace)"

        prompt = (
            f"Current Arm Objective: {sub_goal}\n"
            f"Execution Step: {self.step_count} of max {max_steps}\n"
            f"Workspace Files: {files_str}\n"
            f"{f'Active Coalition Context: {coalition_context}' if coalition_context else ''}\n"
            f"{lateral_notes}\n"
            f"{recalled_guidance}\n"
            f"{compacted_block}\n"
            f"{recent_history_block}"
            f"Choose your next tool action in JSON:"
        )

        # 4. Generate LLM action with biophysically modulated temperature (or fixed temperature if specified)
        system_prompt = self._build_system_prompt()
        last_surprise = self.gate.surprise_history[-1] if self.gate.surprise_history else 0.0
        if self.temperature is not None:
            dyn_temp = float(self.temperature)
        else:
            dyn_temp, _ = self.gate.compute_generation_parameters(last_surprise)
        if self.budget_tracker is not None:
            self.budget_tracker.check_wall_time()
            self.budget_tracker.check_llm_call()
        llm_resp: LLMResponse = self.provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=dyn_temp,
        )
        if self.budget_tracker is not None:
            self.budget_tracker.record_tokens(llm_resp.total_tokens)
        self.total_tokens += llm_resp.total_tokens
        self.total_cost += llm_resp.estimated_cost_dollars

        action_data = self._parse_llm_action(llm_resp.content)
        action_type = action_data.get("action", "read_file")
        explanation = action_data.get("explanation", "")

        # 5. Execute action inside sandbox
        tool_result = ToolResult(tool_name="noop", target="", success=True)
        is_qa = any(kw in self.role.name.lower() or kw in self.role.title.lower() for kw in ("test", "qa"))
        if action_type == "write_file":
            path = action_data.get("path", "temp.py")
            content = action_data.get("content", "")
            p_clean = str(path).strip().lower()
            if is_qa and not (p_clean.startswith("test_") or "test" in p_clean or p_clean.startswith("tests/")):
                tool_result = ToolResult(
                    tool_name="write_file",
                    target=path,
                    success=False,
                    returncode=1,
                    stderr=f"Action rejected: QA arm cannot write implementation file '{path}'. Write test suites in 'test_<module>.py' or 'tests/' instead.",
                    error=f"Action rejected: QA arm cannot write implementation file '{path}'. Write test suites in 'test_<module>.py' or 'tests/' instead.",
                )
            else:
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
        elif action_type == "list_dir":
            path = action_data.get("path", ".")
            tool_result = self.sandbox.list_dir(path)
        elif action_type == "mark_quiescent":
            self.is_quiescent = True
            tool_result = ToolResult(
                tool_name="mark_quiescent",
                target=sub_goal,
                success=True,
                returncode=0,
                stdout="Sub-goal completed.",
            )
        elif action_type == "invalid_action":
            err_msg = action_data.get("error", "Invalid or unknown tool action.")
            tool_result = ToolResult(
                tool_name="invalid_action",
                target="",
                success=False,
                returncode=1,
                stderr=err_msg,
                error=err_msg,
            )
        else:
            err_msg = f"Unknown tool '{action_type}'. Allowed tools: write_file, read_file, run_command, list_dir, mark_quiescent."
            tool_result = ToolResult(
                tool_name=action_type,
                target="",
                success=False,
                returncode=1,
                stderr=err_msg,
                error=err_msg,
            )

        # 6. Encode into sensory observation & evaluate Surprise Gate
        obs = self.encoder.encode(
            result=tool_result,
            step=self.step_count,
            max_steps=max_steps,
        )

        escalate, surprise, telemetry = self.gate.evaluate(actual_obs=obs, tool_result=tool_result)

        # 7. Update status
        is_qa_or_tester = any(kw in self.role.name.lower() or kw in self.role.title.lower() for kw in ("test", "qa"))
        if self.is_quiescent or (
            self.gate.gate_mode != "always_escalate"
            and tool_result.success
            and not escalate
            and not coalition_context
            and tool_result.tool_name == "write_file"
            and not is_qa_or_tester
        ) or self.step_count >= max_steps:
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
            "summary": (tool_result.stdout or tool_result.stderr or "")[:400],
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

        # Workspace files overview
        existing_files = []
        try:
            for p in sorted(self.sandbox.root.iterdir()):
                if not p.name.startswith((".", "__")) and p.name not in ("venv", ".git"):
                    existing_files.append(p.name)
        except Exception:
            pass
        files_str = ", ".join(existing_files) if existing_files else "(empty workspace)"

        prompt = (
            f"Current Arm Objective: {sub_goal}\n"
            f"Execution Step: {self.step_count} of max {max_steps}\n"
            f"Workspace Files: {files_str}\n"
            f"{f'Active Coalition Context: {coalition_context}' if coalition_context else ''}\n"
            f"{lateral_notes}\n"
            f"{recalled_guidance}\n"
            f"{recent_history_block}"
            f"Choose your next tool action in JSON:"
        )

        # 4. Asynchronously generate LLM action with biophysically modulated temperature (or fixed temperature if specified)
        system_prompt = self._build_system_prompt()
        last_surprise = self.gate.surprise_history[-1] if self.gate.surprise_history else 0.0
        if self.temperature is not None:
            dyn_temp = float(self.temperature)
        else:
            dyn_temp, _ = self.gate.compute_generation_parameters(last_surprise)
        if self.budget_tracker is not None:
            self.budget_tracker.check_wall_time()
            self.budget_tracker.check_llm_call()
        llm_resp: LLMResponse = await self.provider.agenerate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=dyn_temp,
            max_tokens=2048,
        )
        if self.budget_tracker is not None:
            self.budget_tracker.record_tokens(llm_resp.total_tokens)
        self.total_tokens += llm_resp.total_tokens
        self.total_cost += llm_resp.estimated_cost_dollars

        action_data = self._parse_llm_action(llm_resp.content)
        action_type = action_data.get("action", "read_file")
        explanation = action_data.get("explanation", "")

        # 5. Asynchronously execute action inside sandbox
        tool_result = ToolResult(tool_name="noop", target="", success=True)
        try:
            is_qa = any(kw in self.role.name.lower() or kw in self.role.title.lower() for kw in ("test", "qa"))
            if action_type == "write_file":
                path = action_data.get("path", "temp.py")
                content = action_data.get("content", "")
                p_clean = str(path).strip().lower()
                if is_qa and not (p_clean.startswith("test_") or "test" in p_clean or p_clean.startswith("tests/")):
                    tool_result = ToolResult(
                        tool_name="write_file",
                        target=path,
                        success=False,
                        returncode=1,
                        stderr=f"Action rejected: QA arm cannot write implementation file '{path}'. Write test suites in 'test_<module>.py' or 'tests/' instead.",
                        error=f"Action rejected: QA arm cannot write implementation file '{path}'. Write test suites in 'test_<module>.py' or 'tests/' instead.",
                    )
                else:
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
            elif action_type == "invalid_action":
                err_msg = action_data.get("error", "Invalid or unknown tool action.")
                tool_result = ToolResult(
                    tool_name="invalid_action",
                    target="",
                    success=False,
                    returncode=1,
                    stderr=err_msg,
                    error=err_msg,
                )
            else:
                err_msg = f"Unknown tool '{action_type}'. Allowed tools: write_file, read_file, run_command, list_dir, mark_quiescent."
                tool_result = ToolResult(
                    tool_name=action_type,
                    target="",
                    success=False,
                    returncode=1,
                    stderr=err_msg,
                    error=err_msg,
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
        is_qa_or_tester = any(kw in self.role.name.lower() or kw in self.role.title.lower() for kw in ("test", "qa"))
        if self.is_quiescent or (
            self.gate.gate_mode != "always_escalate"
            and tool_result.success
            and not escalate
            and not coalition_context
            and tool_result.tool_name == "write_file"
            and not is_qa_or_tester
        ) or self.step_count >= max_steps:
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
            "summary": (tool_result.stdout or tool_result.stderr or "")[:400],
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

        if self.budget_tracker is not None:
            self.budget_tracker.check_wall_time()
            self.budget_tracker.check_llm_call()
        response = self.provider.generate(
            prompt=user_content,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=600,
        )
        if self.budget_tracker is not None:
            self.budget_tracker.record_tokens(response.total_tokens)
        return response.content.strip()

