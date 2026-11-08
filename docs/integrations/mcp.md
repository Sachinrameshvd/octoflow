# Model Context Protocol (MCP) Integration Guide

OctoFlow provides a fully conformant **Model Context Protocol (MCP)** JSON-RPC 2.0 stdio server (`octoflow mcp`). It exposes OctoFlow's 8-arm cephalopod multi-agent architecture, Active Inference sensory gating, associative memory, and workspace diagnostic tools directly to AI developer hosts including **Claude Code**, **Cursor**, and **Antigravity IDE**.

---

## 1. Specification Conformance & Protocol Negotiation

- **Specification Revision:** Evaluated against the Model Context Protocol standard (`modelcontextprotocol.io`). Protocol versions supported during handshake negotiation include `2024-11-05` (canonical default), `2024-10-07`, `2025-03-26`, and `2026-07-28`.
- **Transport:** Standard Input/Output (`stdio`) JSON-RPC 2.0 stream.
- **Server Identity:** Returns `serverInfo` with `name="octoflow"` and current package semantic version.
- **Stdio Hygiene:** Strict stdout isolation (`StdoutGuard`). Internal logger outputs and arbitrary library prints are redirected to `stderr`. Protocol messages emitted to `stdout` are strictly valid single-line JSON-RPC 2.0 objects followed by a newline (`\n`).

---

## 2. Host Setup

### Claude Code Setup

Claude Code can integrate with OctoFlow via CLI registration or through the repository's `.mcp.json` manifest.

#### Method A: Claude Code CLI
Register OctoFlow globally or per-project:
```bash
claude mcp add octoflow -- octoflow mcp
```

Or specify a dedicated workspace directory:
```bash
claude mcp add octoflow -- octoflow mcp --dir /path/to/project
```

#### Method B: Project Configuration (`.mcp.json`)
Place a `.mcp.json` file in the root of your repository:
```json
{
  "mcpServers": {
    "octoflow": {
      "command": "octoflow",
      "args": ["mcp"],
      "description": "OctoFlow Cephalopod Neural Multi-Agent Harness & Connectome Tools"
    }
  }
}
```

#### Method C: Claude Code Plugin (`.claude-plugin/plugin.json`)
If utilizing OctoFlow as a Claude Plugin:
```json
{
  "name": "octoflow",
  "version": "0.2.0",
  "entrypoint": "octoflow.cli:app",
  "mcp": {
    "server": "octoflow",
    "command": "octoflow",
    "args": ["mcp"]
  }
}
```

---

### Cursor Setup

Cursor connects to stdio MCP servers via `.cursor/mcp.json` or through Cursor Settings.

#### Project-level Configuration (`.cursor/mcp.json`)
Create `.cursor/mcp.json` in your workspace root:
```json
{
  "mcpServers": {
    "octoflow": {
      "command": "octoflow",
      "args": ["mcp", "--dir", "${workspaceFolder}"]
    }
  }
}
```

#### Global Cursor Settings
1. Navigate to **Cursor Settings** > **Features** > **MCP Servers**.
2. Click **+ Add New MCP Server**.
3. Name: `octoflow`
4. Type: `command`
5. Command: `octoflow mcp`

---

## 3. Exposed Core Tools & Schemas

OctoFlow exposes 8 canonical tools. All tool input schemas conform strictly to **JSON Schema Draft 2020-12**.

| Canonical Tool Name | Legacy / Alias Support | Primary Purpose | Side Effects & Scope |
| :--- | :--- | :--- | :--- |
| `octoflow_run` | `octoflow_run_swarm` | Launch 8-arm autonomous swarm mission | Modifies workspace files, executes tests/builds within `--dir` |
| `octoflow_get_run_status` | `status`, `get_run_status`, `octoflow_status` | Query cycle progress & thoughts of runs | Read-only session state inspection |
| `octoflow_inspect_arms` | `octoflow_arms_status` | Query surprise ($\Delta S$) & status of 8 arms | Read-only arm telemetry query |
| `octoflow_recall_memory` | — | Associative Hebbian memory recall in Vertical Lobe | Read-only memory matrix query |
| `octoflow_audit` | — | Score workspace readiness & security (1-100) | Read-only scan confined to `--dir` |
| `octoflow_guild_list` | — | Discover 8-arm specialist guilds | Read-only discovery across configs |
| `octoflow_receipt` | — | Truthful token receipt & gate savings | Read-only accounting query |
| `octoflow_read_file` | — | Read workspace file content with boundary guard | Read-only file access strictly within `--dir` |

### Detailed Tool Specifications

#### 1. `octoflow_run`
Executes an objective across the 8 brachial ganglia with sensory surprise gating ($\Delta S = \frac{1}{D}\|o_t - \hat{o}_t\|^2$).
- **Parameters:**
  - `objective` (string, required): The coding, refactoring, or research goal.
  - `morphology` (string, optional, default `"software_dev"`): Presets: `software_dev`, `aiml_research`, `fullstack_ai`, `custom`.
  - `guild` (string, optional): Specific guild name loaded from `.octoflow/guilds/` or built-ins.
  - `max_cycles` (integer, optional, default `10`): Maximum cognitive problem-solving cycles.
  - `dry_run` (boolean, optional, default `false`): Execute with mock LLM simulation without external calls.
  - `async` / `async_run` (boolean, optional, default `false`): Background the run immediately and return a `run_id` for asynchronous polling.
  - `timeout_seconds` (number, optional, default `60.0`): Max seconds to wait in synchronous mode before gracefully backgrounding to prevent host timeouts.

#### 2. `octoflow_get_run_status`
Polls active background tasks or completed run archives.
- **Parameters:**
  - `run_id` (string, optional): The run identifier returned by `octoflow_run`. Defaults to latest run.
- **Returns:** Arm cycle index, total cycles, latest neural thought, quiescent arm count, tokens consumed, files written, and completion status.

#### 3. `octoflow_inspect_arms`
Inspects real-time sensory surprise deltas ($\Delta S$), reflex thresholds ($\theta$), and current tool permissions for all 8 arm agents.
- **Parameters:** None.

#### 4. `octoflow_recall_memory`
Queries the cephalopod Vertical Lobe associative memory for known bug patterns and remediation strategies.
- **Parameters:**
  - `error_text` (string, required): Traceback, compiler error, or test failure string.

#### 5. `octoflow_audit`
Evaluates workspace test density, syntax hygiene, security sanitization, and sensory gating on a 1-100 scale.
- **Parameters:**
  - `path` (string, optional): Subdirectory within workspace to audit. Defaults to workspace root.

#### 6. `octoflow_guild_list`
Lists discovered 8-arm specialist guilds across project (`.octoflow/guilds/`), user (`~/.octoflow/guilds/`), and built-in templates.
- **Parameters:** None.

#### 7. `octoflow_receipt`
Returns the truthful token receipt, measured token savings from sensory gating, and cost accounting.
- **Parameters:**
  - `run_id` (string, optional): Defaults to latest completed run.

#### 8. `octoflow_read_file`
Reads contents of a workspace file with strict boundary containment.
- **Parameters:**
  - `path` (string, required): Relative path within workspace.
  - `max_lines` (integer, optional, default `500`): Maximum lines returned before truncation.

---

## 4. Security, Isolation & Boundary Enforcement

1. **Workspace Confinement (`--dir`):**
   - The server enforces that all file reads, writes, audits, and tool executions stay inside the directory passed via `--dir` (default: current working directory).
   - Attempts to access paths outside this tree (e.g., `../../etc/passwd` or absolute root paths) are blocked and return `isError: true` without server termination.
   - Null-byte path injection attacks are actively rejected.

2. **Stdio Protocol Hygiene:**
   - Client parsers (such as Claude Code's JSON-RPC parser) fail if non-JSON bytes appear on stdout.
   - OctoFlow wraps `sys.stdout` with `StdoutGuard(sys.stderr)`, guaranteeing that third-party logs, progress bars, or debug prints do not pollute the protocol channel.

3. **Error Handling Architecture:**
   - **Protocol Errors:** Malformed JSON returns code `-32700`. Unknown methods or nonexistent tools return `-32601`. Missing required schema parameters return `-32602`.
   - **Tool Execution Failures:** Domain errors (e.g. file not found, permission denied, test failures) return standard JSON-RPC response objects with `"isError": true` and informative text in `"content"`, avoiding protocol aborts.

---

## 5. Verification & Health Check

Verify your OctoFlow MCP server configuration in under five seconds using this interactive shell check:

```bash
python3 - << 'EOF'
import json, subprocess

proc = subprocess.Popen(
    ["octoflow", "mcp"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

def query(req):
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()
    return json.loads(proc.stdout.readline())

# 1. Initialize
init_resp = query({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}})
print(f"✔ Initialized: {init_resp['result']['serverInfo']['name']} v{init_resp['result']['serverInfo']['version']}")

# 2. Tools List
tools_resp = query({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
tool_count = len(tools_resp['result']['tools'])
print(f"✔ Tools registered: {tool_count} tools available")

proc.stdin.close()
proc.wait()
EOF
```

Expected output:
```text
✔ Initialized: octoflow v0.2.0
✔ Tools registered: 8 tools available
```

