"""Claude Code Bridge & 8-Arm SPARC Prompt Generation for OctoFlow.

Provides native integration between OctoFlow's 8-arm active-inference framework
and Anthropic's official Claude Code CLI (`claude`), Desktop app, and web interfaces.
"""

from __future__ import annotations

import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

CLAUDE_MD_TEMPLATE = """# OctoFlow Cephalopod Intelligence Protocol for Claude Code

This workspace is integrated with **OctoFlow**, an active-inference cephalopod multi-agent architecture.
When working in this repository, you MUST follow the 8-Arm Specialist Discipline and Sensory Gating rules below.

---

## 1. The 8-Arm Neuro-Specialist Roster
When analyzing, planning, and executing tasks, compartmentalize responsibilities across these 8 domains:

* **Arm 0: System Architect** (`specs/`, `architecture/`, root configs)
  * System boundaries, module topologies, API contracts, dependency constraints.
* **Arm 1: Database & Persistence** (`models/`, `db/`, `migrations/`, schemas)
  * Data models, ORM entities, migration scripts, integrity indices, connection pools.
* **Arm 2: Backend API & Services** (`backend/`, `api/`, `services/`, `controllers/`)
  * REST/GraphQL/WebSocket endpoints, authentication, business rules, service coordination.
* **Arm 3: Frontend UI & Client** (`frontend/`, `src/components/`, `src/views/`, `ui/`)
  * Client components, reactive state, style consistency, responsive layouts, accessibility.
* **Arm 4: State & Latency Optimization** (`cache/`, `opt/`, `state/`)
  * In-memory caches, database query optimization, payload compression, async pipelines.
* **Arm 5: QA & Test Harness** (`tests/`, `e2e/`, `fixtures/`)
  * Unit test suites, integration mocks, contract verifications, regression suites.
* **Arm 6: Security & AST Protection** (`security/`, audits, sanitization)
  * Secret leak detection, input validation/sanitization, rate limiting, RBAC checks.
* **Arm 7: DevOps & Runtime Deployment** (`deploy/`, `Dockerfile`, CI/CD, entrypoints)
  * Containerization, process supervisor, healthcheck routes, dev server ignition.

---

## 2. Active Inference Sensory Gating Directives (Token Conservation θ = 0.45)
To prevent token waste and hallucinations:
1. **Targeted Reading**: Always read existing contracts, imports, and types before writing or editing.
2. **Never Fabricate Imports**: Only reference libraries confirmed in `pyproject.toml`, `package.json`, or requirements files.
3. **AST Pre-Flight Check**: Verify syntax validity before finalizing edits.
4. **Secret Quarantine**: Never commit API keys or private credentials into repository files.

---

## 3. The 4-Phase SPARC Execution Lifecycle
For all non-trivial features, proceed strictly through these 4 phase gates:

* **Phase 1: Specification & Blueprint (S/P/A)**
  * Clarify requirements, define schema contracts, and generate module boundaries.
* **Phase 2: Core Construction & TDD (R)**
  * Implement backend logic, database models, and UI components alongside automated tests.
* **Phase 3: QA, AST & Security Audit (C)**
  * Run test suites, verify zero lint errors, and audit for vulnerability and leak risks.
* **Phase 4: Live Ignition & Verification**
  * Boot or verify the application entrypoint and validate HTTP/API health.

---

## 4. OctoFlow Swarm CLI Integration
When a task exceeds single-file scope, delegate to the native OctoFlow Swarm:
* `octos run "<goal>"` — Autonomous multi-octopus execution with live visual telemetry.
* `octos` — Launch the full-screen terminal flight cockpit.
* `octos ignite` — Boot dev server and verify localhost health.
* `octos guard` — AST syntax & secret leak audit.
* `octos undo` — Rollback changes to the previous safe checkpoint.
"""


def generate_claude_md(workspace: str | Path = ".", force: bool = False) -> tuple[Path, bool]:
    """Generate or update CLAUDE.md in the target workspace.

    Args:
        workspace: Path to project directory.
        force: Overwrite existing CLAUDE.md completely if True.

    Returns:
        Tuple of (target_path, was_created_or_modified)
    """
    ws = Path(workspace).resolve()
    target = ws / "CLAUDE.md"

    if not target.exists() or force:
        target.write_text(CLAUDE_MD_TEMPLATE.strip() + "\n", encoding="utf-8")
        return target, True

    existing = target.read_text(encoding="utf-8")
    if "OctoFlow Cephalopod Intelligence Protocol" in existing:
        return target, False

    # Non-destructive append
    appended = existing.rstrip() + "\n\n" + CLAUDE_MD_TEMPLATE.strip() + "\n"
    target.write_text(appended, encoding="utf-8")
    return target, True


def compile_sparc_prompt(goal: str, workspace: str | Path = ".") -> str:
    """Compile an engineering goal into an 8-Arm SPARC execution directive for Claude.

    Args:
        goal: The user-defined feature or bugfix goal.
        workspace: Target project directory for contextual inspection.

    Returns:
        High-density structured prompt string.
    """
    ws = Path(workspace).resolve()

    # Detect workspace characteristics for contextual grounding
    tech_stack: list[str] = []
    if (ws / "pyproject.toml").exists() or (ws / "requirements.txt").exists():
        tech_stack.append("Python")
    if (ws / "package.json").exists():
        tech_stack.append("Node.js/TypeScript")
    if (ws / "Cargo.toml").exists():
        tech_stack.append("Rust")
    if (ws / "go.mod").exists():
        tech_stack.append("Go")
    if (ws / "Dockerfile").exists() or (ws / "docker-compose.yml").exists():
        tech_stack.append("Docker")

    stack_ctx = f" (Workspace Stack: {', '.join(tech_stack)})" if tech_stack else ""

    prompt_lines = [
        "◈ OCTOFLOW 8-ARM SPARC DIRECTIVE FOR CLAUDE CODE",
        f"Goal: {goal.strip()}{stack_ctx}",
        "",
        "Execute this engineering objective strictly following OctoFlow's 4-Phase SPARC protocol:",
        "",
        "### Phase 1: Specification & Architecture Blueprint [Arms 0, 1, 2]",
        "1. Define explicit module boundaries, database schemas/models, and API contracts.",
        "2. List all target files to create or modify before writing code.",
        "",
        "### Phase 2: Core Construction & TDD Implementation [Arms 3, 4, 5]",
        "1. Implement services, business logic, and UI components following established patterns.",
        "2. Write automated unit and integration tests covering standard and edge-case execution paths.",
        "",
        "### Phase 3: QA, AST Verification & Security Audit [Arms 5, 6]",
        "1. Execute test suites and verify all tests pass with zero syntax or import regressions.",
        "2. Audit for security vulnerabilities, input sanitization, and credential leaks.",
        "",
        "### Phase 4: Delivery & Ignition Readiness [Arm 7]",
        "1. Verify the project entrypoint, dev server configuration, or build pipeline.",
        "2. Ensure clean git diff status.",
    ]

    return "\n".join(prompt_lines)


def get_claude_status(workspace: str | Path = ".") -> dict[str, Any]:
    """Inspect Claude Code CLI installation and workspace integration health.

    Returns:
        Dict with keys: claude_installed, claude_path, claude_version,
        claude_md_exists, claude_md_path, mcp_configured, mcp_paths
    """
    ws = Path(workspace).resolve()
    claude_bin = shutil.which("claude")
    claude_version = None

    if claude_bin:
        try:
            res = subprocess.run(
                [claude_bin, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if res.returncode == 0:
                claude_version = res.stdout.strip()
        except Exception:
            pass

    claude_md = ws / "CLAUDE.md"
    claude_md_exists = claude_md.exists()

    # Check MCP configuration in ~/.claude.json and workspace .mcp.json
    mcp_paths: list[str] = []
    global_cfg = Path.home() / ".claude.json"
    if global_cfg.exists():
        try:
            data = json.loads(global_cfg.read_text(encoding="utf-8"))
            if "mcpServers" in data and "octoflow" in data["mcpServers"]:
                mcp_paths.append(str(global_cfg))
        except Exception:
            pass

    ws_mcp = ws / ".mcp.json"
    if ws_mcp.exists():
        try:
            data = json.loads(ws_mcp.read_text(encoding="utf-8"))
            if "mcpServers" in data and "octoflow" in data["mcpServers"]:
                mcp_paths.append(str(ws_mcp))
        except Exception:
            pass

    return {
        "claude_installed": claude_bin is not None,
        "claude_path": claude_bin,
        "claude_version": claude_version,
        "claude_md_exists": claude_md_exists,
        "claude_md_path": str(claude_md) if claude_md_exists else None,
        "mcp_configured": len(mcp_paths) > 0,
        "mcp_paths": mcp_paths,
    }


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard across macOS, Linux, and Windows.

    Returns:
        True if successfully copied, False otherwise.
    """
    # Try pyperclip if available
    try:
        import pyperclip  # type: ignore

        pyperclip.copy(text)
        return True
    except Exception:
        pass

    system = platform.system()
    try:
        if system == "Darwin":
            proc = subprocess.run(
                ["pbcopy"],
                input=text.encode("utf-8"),
                check=True,
                capture_output=True,
            )
            return proc.returncode == 0
        if system == "Linux":
            if shutil.which("xclip"):
                proc = subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=text.encode("utf-8"),
                    check=True,
                    capture_output=True,
                )
                return proc.returncode == 0
            if shutil.which("wl-copy"):
                proc = subprocess.run(
                    ["wl-copy"],
                    input=text.encode("utf-8"),
                    check=True,
                    capture_output=True,
                )
                return proc.returncode == 0
        if system == "Windows":
            proc = subprocess.run(
                ["clip"],
                input=text.encode("utf-8"),
                check=True,
                capture_output=True,
            )
            return proc.returncode == 0
    except Exception:
        pass

    return False


def execute_claude_cli(
    goal: str,
    print_mode: bool = False,
    dangerously_skip_permissions: bool = False,
    dry_run: bool = False,
    workspace: str | Path = ".",
) -> int:
    """Execute official Claude Code CLI with the compiled 8-Arm SPARC prompt.

    Args:
        goal: User engineering goal.
        print_mode: If True, passes -p for non-interactive output.
        dangerously_skip_permissions: If True, passes --dangerously-skip-permissions.
        dry_run: If True, does not execute; only prints intended command.
        workspace: Target project directory.

    Returns:
        Exit code (0 on success).
    """
    prompt = compile_sparc_prompt(goal, workspace=workspace)
    claude_bin = shutil.which("claude")

    if not claude_bin:
        return 127

    cmd = [claude_bin]
    if print_mode:
        cmd.extend(["-p", prompt])
    else:
        cmd.append(prompt)

    if dangerously_skip_permissions:
        cmd.append("--dangerously-skip-permissions")

    if dry_run:
        return 0

    ws = Path(workspace).resolve()
    try:
        res = subprocess.run(cmd, cwd=str(ws))
        return res.returncode
    except Exception:
        return 1
