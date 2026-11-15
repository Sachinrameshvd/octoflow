"""One-Command Omni-IDE Auto-Onboarding Engine for OctoFlow.

Configures Cursor AI (.cursorrules), Claude Code/Desktop (MCP injection),
VS Code (.vscode/tasks.json), and Git (.git/hooks/pre-commit) in one non-destructive command.
"""

import json
import os
import platform
from pathlib import Path
from typing import Any

CURSOR_RULES_TEMPLATE = """# OctoFlow Cephalopod Swarm Delegation Rules

## Architecture & Swarm Overview
This workspace is engineered with OctoFlow, an 8-arm autonomous active-inference connectome.
The swarm operates silently, minimizing LLM token consumption by up to 87.5% through bio-inspired surprise gating and AST pre-flight safety.

### 8-Arm Specialist Roster:
- Arm 0: System Architect (`specs/`, `architecture/`) - Interface contracts, folder topology, spec design.
- Arm 1: Database & Schemas (`models/`, `db/`, `migrations/`) - Persistence, ORM schemas, database connectors.
- Arm 2: Backend API (`backend/`, `api/`, `services/`) - REST/WebSocket controllers, business logic.
- Arm 3: Frontend UI (`frontend/`, `src/components/`, `src/views/`) - Web dashboard, canvas, responsive UI.
- Arm 4: State & Optimization (`export/`, `opt/`, `state/`) - Client state, caching, latency optimization.
- Arm 5: QA & Testing (`tests/`, `e2e/`) - Unit suites, integration tests, contract verification.
- Arm 6: Security & Profiling (`security/`) - Input sanitization, vulnerability audit, secret protection.
- Arm 7: DevOps & Deploy (`deploy/`, `Dockerfile`, `docker-compose.yml`) - Containerization, CI/CD, docs.

## Delegation Directives for AI Assistant:
1. **Single-file minor edits**: Feel free to edit files directly in this editor.
2. **Multi-file features, architecture refactors, or security audits**:
   Delegate to the OctoFlow Swarm via terminal CLI or MCP tool:
   ```bash
   octos run "<High-level engineering or research goal>"
   ```
   Or launch the interactive visual cockpit:
   ```bash
   octos
   ```
3. **Pre-commit safety**:
   OctoFlow enforces AST syntax verification and scans for secret leaks (Anthropic/OpenAI keys) before every git commit via `octos guard`.
"""

VSCODE_TASKS_TEMPLATE = {
    "version": "2.0.0",
    "tasks": [
        {
            "label": "OctoFlow: Launch Cockpit",
            "type": "shell",
            "command": "octos",
            "problemMatcher": [],
            "presentation": {"reveal": "always", "panel": "new", "focus": True},
        },
        {
            "label": "OctoFlow: 3D Visualizer",
            "type": "shell",
            "command": "octos ui",
            "problemMatcher": [],
            "presentation": {"reveal": "silent", "panel": "shared"},
        },
        {
            "label": "OctoFlow: Swarm Guard Scan",
            "type": "shell",
            "command": "octos guard",
            "problemMatcher": [],
            "presentation": {"reveal": "always", "panel": "shared"},
        },
        {
            "label": "OctoFlow: Doctor Diagnostics",
            "type": "shell",
            "command": "octos doctor",
            "problemMatcher": [],
            "presentation": {"reveal": "always", "panel": "shared"},
        },
    ],
}


def _merge_json_safely(
    file_path: Path, new_data: dict[str, Any], key_merger: str | None = None
) -> bool:
    """Non-destructively merge JSON configuration into an existing or new file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        existing = {}
        if file_path.exists():
            try:
                existing = json.loads(file_path.read_text(encoding="utf-8"))
            except Exception:
                existing = {}

        if key_merger and key_merger in new_data:
            # Preserve top-level keys like "version" if not present
            for k, v in new_data.items():
                if k != key_merger and k not in existing:
                    existing[k] = v

            if key_merger not in existing:
                existing[key_merger] = [] if isinstance(new_data[key_merger], list) else {}

            if isinstance(existing[key_merger], dict) and isinstance(new_data[key_merger], dict):
                existing[key_merger].update(new_data[key_merger])
            elif isinstance(existing[key_merger], list) and isinstance(new_data[key_merger], list):
                # Unique list merge by label or id if present
                existing_labels = {
                    item.get("label") for item in existing[key_merger] if isinstance(item, dict)
                }
                for item in new_data[key_merger]:
                    if isinstance(item, dict) and item.get("label") not in existing_labels:
                        existing[key_merger].append(item)
                    elif not isinstance(item, dict) and item not in existing[key_merger]:
                        existing[key_merger].append(item)
        else:
            existing.update(new_data)

        file_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
        return True
    except Exception:
        return False


def onboard_ide(workspace: str = ".") -> dict[str, Any]:
    """Execute complete 1-command Omni-IDE onboarding across Cursor, Claude, VS Code, and Git.

    Returns:
        Dict detailing which integrations were successfully injected.
    """
    ws = Path(workspace).resolve()
    details: list[str] = []
    results = {
        "cursor": False,
        "claude_md": False,
        "claude_code": False,
        "claude_desktop": False,
        "vscode_tasks": False,
        "git_hooks": False,
        "details": details,
    }

    # 1. Cursor AI (.cursorrules)
    try:
        cursor_file = ws / ".cursorrules"
        if not cursor_file.exists():
            cursor_file.write_text(CURSOR_RULES_TEMPLATE.strip() + "\n", encoding="utf-8")
            results["cursor"] = True
            details.append(f"Generated {cursor_file.relative_to(ws)}")
        else:
            existing_text = cursor_file.read_text(encoding="utf-8")
            if "OctoFlow Cephalopod Swarm" not in existing_text:
                cursor_file.write_text(
                    existing_text.rstrip() + "\n\n" + CURSOR_RULES_TEMPLATE.strip() + "\n",
                    encoding="utf-8",
                )
                results["cursor"] = True
                details.append(
                    f"Appended OctoFlow delegation rules to existing {cursor_file.relative_to(ws)}"
                )
            else:
                results["cursor"] = True
                details.append(f"Existing {cursor_file.relative_to(ws)} already configured")
    except Exception as e:
        details.append(f"Failed to configure .cursorrules: {e}")

    # 2. Claude Code CLAUDE.md Protocol
    try:
        from octoflow.claude_bridge import generate_claude_md

        _, md_created = generate_claude_md(workspace=ws, force=False)
        results["claude_md"] = True
        details.append(f"Configured CLAUDE.md 8-Arm Protocol in {ws.name}")
    except Exception as e:
        details.append(f"Failed to configure CLAUDE.md: {e}")

    # 3. Claude Code CLI (~/.claude.json)
    try:
        claude_cli_file = Path.home() / ".claude.json"
        mcp_payload = {"mcpServers": {"octoflow": {"command": "octos", "args": ["mcp"]}}}
        if _merge_json_safely(claude_cli_file, mcp_payload, key_merger="mcpServers"):
            results["claude_code"] = True
            details.append(f"Injected OctoFlow MCP server into Claude Code ({claude_cli_file})")
    except Exception as e:
        details.append(f"Failed to inject Claude Code MCP: {e}")

    # 3. Claude Desktop App (claude_desktop_config.json)
    try:
        system = platform.system()
        desktop_conf_path = None
        if system == "Darwin":
            desktop_conf_path = (
                Path.home()
                / "Library"
                / "Application Support"
                / "Claude"
                / "claude_desktop_config.json"
            )
        elif system == "Windows":
            appdata = os.getenv("APPDATA")
            if appdata:
                desktop_conf_path = Path(appdata) / "Claude" / "claude_desktop_config.json"
        else:  # Linux
            desktop_conf_path = Path.home() / ".config" / "Claude" / "claude_desktop_config.json"

        if desktop_conf_path:
            mcp_payload = {"mcpServers": {"octoflow": {"command": "octos", "args": ["mcp"]}}}
            if _merge_json_safely(desktop_conf_path, mcp_payload, key_merger="mcpServers"):
                results["claude_desktop"] = True
                details.append(
                    f"Injected OctoFlow MCP server into Claude Desktop ({desktop_conf_path})"
                )
    except Exception as e:
        details.append(f"Failed to inject Claude Desktop MCP: {e}")

    # 4. VS Code Tasks (.vscode/tasks.json)
    try:
        vscode_dir = ws / ".vscode"
        tasks_file = vscode_dir / "tasks.json"
        if _merge_json_safely(tasks_file, VSCODE_TASKS_TEMPLATE, key_merger="tasks"):
            results["vscode_tasks"] = True
            details.append(f"Configured 4 Command Palette tasks in {tasks_file.relative_to(ws)}")
    except Exception as e:
        details.append(f"Failed to configure VS Code tasks: {e}")

    # 5. Git Pre-Commit Hook (octos guard)
    try:
        from octoflow.cli import install_git_hooks

        hook_ok = install_git_hooks(workspace=str(ws))
        results["git_hooks"] = hook_ok
        if hook_ok:
            details.append("Installed automated Pre-Commit Swarm Guard (.git/hooks/pre-commit)")
    except Exception as e:
        details.append(f"Pre-commit hook installation note: {e}")

    return results
