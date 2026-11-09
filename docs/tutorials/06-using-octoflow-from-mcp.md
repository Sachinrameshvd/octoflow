# Tutorial 6: Using OctoFlow from Cursor & Claude Code via MCP

**Estimated Duration:** 6 minutes  
**Verification:** Verified on 2026-11-09, OctoFlow v0.2.0  

This tutorial explains how to connect OctoFlow to **Claude Code** and **Cursor** using the Model Context Protocol (MCP) standard, enabling external AI assistants to invoke OctoFlow's 8-arm swarm, query the 3D connectome, and trigger self-healing loops.

---

## What is the OctoFlow MCP Server?

OctoFlow provides a conformant Model Context Protocol server over standard input/output (`stdio`) implementing JSON-RPC 2.0. It exposes 8 specialized tools:
- `octoflow_run`: Launch the 8-arm swarm on an objective.
- `octoflow_status`: Inspect recent missions, active branches, and token receipts.
- `octoflow_audit`: Run the 100-point cephalopod system diagnostic.
- `octoflow_heal`: Trigger closed-loop autonomous test failure repair.
- `octoflow_connectome`: Retrieve the live 8-arm neural status and surprise meters.
- `octoflow_replay`: Replay past execution events into the client.
- `octoflow_eject`: Export a standalone multi-agent harness.
- `octoflow_receipt`: Inspect truthful token accounting for any run.

---

## Step 1: One-Command Auto-Configuration

The fastest way to configure Claude Code, Cursor, and VS Code is the `init` command:

```bash
octoflow init
```

### Expected Output

```text
◈ OctoFlow Omni-IDE Onboarding
✔ Injected .cursorrules with 8-arm delegation heuristics
✔ Configured ~/.claude.json with OctoFlow MCP server
✔ Added .vscode/tasks.json shortcuts (make dev, test, audit)
✔ Installed Git pre-commit secret leak guard
```

---

## Step 2: Manual Configuration for Claude Code

If you prefer manual configuration, add the following to `~/.claude.json`:

```json
{
  "mcpServers": {
    "octoflow": {
      "command": "octoflow",
      "args": ["mcp-serve"]
    }
  }
}
```

Restart Claude Code. In your next session, test the integration:

```text
> What tools are available from the OctoFlow MCP server?
Claude: The OctoFlow MCP server provides 8 tools: octoflow_run, octoflow_status, octoflow_audit, octoflow_heal, octoflow_connectome, octoflow_replay, octoflow_eject, and octoflow_receipt.
```

---

## Step 3: Manual Configuration for Cursor

In Cursor, navigate to **Settings > Features > MCP**, click **Add New MCP Server**, and enter:
- **Name**: `octoflow`
- **Type**: `command`
- **Command**: `octoflow mcp-serve`

Once added, the green status indicator confirms connection. You can now prompt Composer:
> *"Use octoflow_run in dry-run mode to design an authentication service."*

---

## Step 4: Verify MCP Handshake Manually

To verify the JSON-RPC stdio protocol directly from your terminal:

```bash
python3 -c '
import json, subprocess
proc = subprocess.Popen(["octoflow", "mcp-serve"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
out, _ = proc.communicate(json.dumps(req) + "\n", timeout=5)
print("Handshake Response:", json.loads(out.strip())["result"]["tools"][0]["name"])
'
```

*Expected output: `Handshake Response: octoflow_run`.*

---

## Next Steps

- Complete protocol specifications and error handling: [docs/integrations/mcp.md](../integrations/mcp.md)
- Learn how to visualize runs live in 3D: [Tutorial 7: Watching in the Visualizer](07-watching-in-the-visualizer.md)
