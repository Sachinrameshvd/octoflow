# OctoFlow STRIDE Threat Model

**Version:** 1.0 (Phase 5.1 Security Review)  
**Status:** Approved for Security Hardening  
**Scope:** OctoFlow CLI, Cockpit TUI, 3D WebGL Visualizer Bridge, MCP Server, Ignition Runtime, CI/CD Engine, and Associative Memory.

---

## 1. System Overview & Trust Architecture

OctoFlow operates as an autonomous, 8-ganglia active-inference cephalopod multi-agent system executing local code generation, tool invocation, interactive Cockpit rendering, and telemetry streaming. The system interfaces between untrusted inputs (LLM token completions, workspace code repositories, terminal pastes, and local network ports) and high-privilege operations (subprocess execution, file modification, git branch manipulation, and background service ignition).

```mermaid
flowchart TD
    subgraph Boundary 1: LLM Engine
        LLM[Frontier LLM Provider] -->|ToolCall / Code| Arm[Ganglia Arms]
    end

    subgraph Boundary 2: Workspace Repository
        RepoFiles[Untrusted Workspace Files] -->|AST / RAG Chunks| Memory[Vertical Lobe & RAG]
    end

    subgraph Boundary 3: User Interface
        Terminal[User Terminal / Paste] -->|Commands| Cockpit[Cockpit TUI & Router]
    end

    subgraph Boundary 4: Localhost Network
        Browser[Browser / Local Client] -->|WebSocket / HTTP| Server[FastAPI Telemetry Bridge]
    end

    subgraph Boundary 5: MCP Host
        MCPClient[Claude Code / Cursor] -->|JSON-RPC stdio| MCPServer[OctoFlow MCP Server]
    end

    subgraph Boundary 6: Generated Runtimes
        Ignition[ProjectIgniter] -->|Spawn Subprocess| LiveApp[Generated Backend/Frontend]
    end

    subgraph Boundary 7: Tooling & Git
        Guard[Pre-Commit Hook / CI] -->|git diff / Actions| Workflow[GitHub Actions / Git Hook]
    end

    subgraph Boundary 8: Dependencies
        PyPI_NPM[PyPI & NPM Dependencies] -->|Imports| Runtime[OctoFlow Core & Visualizer]
    end
```

---

## 2. STRIDE Threat Analysis Across 8 Trust Boundaries

### Boundary 1: LLM Output (Untrusted, Drives Tools)
- **Assets at Risk:** Host filesystem integrity, local developer credentials, shell process execution rights, git commit tree.
- **Attacker Profile:** Adversary performing prompt injection (direct or indirect) via poisoned issues, malicious dependencies, or search context to hijack LLM tool invocations.
- **Entry Points:** LLM completion tokens parsed into `ToolCall` objects (`octoflow/arm.py:180-210`), shell command strings, and code diff proposals.
- **Existing Controls:**
  - `ToolPolicy` and `ToolExecutor` (`octoflow/tools.py:126-218`): Whitelisted tool commands, path canonicalization, and workspace boundary enforcement.
  - Subprocess environment sanitization (`octoflow/tools.py:89-122`, `296-319`): `SAFE_ENV_PASSTHROUGH` purges API keys and tokens from child processes.
  - AST pre-flight verification (`octoflow/tools.py:465-485`): Validates Python AST syntax before file persistence.
  - Secret masking / redaction (`octoflow/provider.py:18-40`): Replaces known credential formats with redaction placeholders.
- **Gaps Identified:**
  - `octoflow/router.py:798-805`: Executes `SHELL_EXPLICIT` routes with `shell=True`. While cockpit requests confirmation, non-interactive execution pipelines or tricked users are susceptible to shell command chaining (`cmd1 && cmd2`).
  - `octoflow/arm.py:184`: `ast.literal_eval` is used to parse LLM structured outputs; vulnerable to deep recursion resource exhaustion attacks.
  - When invoked via MCP (`octoflow/mcp.py`), swarm runs mutating actions without interactive user confirmation.
- **Threat Status:** **PARTIAL** (Tool confinement enforced; shell chaining and non-interactive MCP oversight remain open).

---

### Boundary 2: Workspace File Contents (Untrusted, Fed to the LLM)
- **Assets at Risk:** LLM context integrity, developer system instructions, system persona stability, private repository code privacy.
- **Attacker Profile:** Untrusted repository authors or contributors embedding malicious prompts, instruction overrides, or hidden payloads in codebase files.
- **Entry Points:** `octoflow/memory.py:287-357` (`EpisodicCodebaseRAG.index_workspace`), `octoflow/tools.py:340-390` (`read_file`), git diff loaders.
- **Existing Controls:**
  - Lexical and resolved path traversal checks (`octoflow/tools.py:230-265`).
  - Secret redaction before display in diffs (`octoflow/report.py:82`, `octoflow/ci.py:150-155`).
- **Gaps Identified:**
  - **Indirect Prompt Injection:** RAG chunks and file contents are interpolated directly into LLM prompts without delimiter isolation or untrusted content wrapping (`octoflow/conductor.py:150-250`).
  - **Plaintext Disk Persistence:** `octoflow/memory.py:390-412` (`EpisodicCodebaseRAG.save`) writes indexed full source text into `~/.octoflow/vertical_lobe.json` using default umask (permissions `0644`), leaking private code to any local unprivileged process.
- **Threat Status:** **OPEN** (Indirect prompt injection lacks structural shielding; memory file permissions unhardened).

---

### Boundary 3: Pasted / Typed Terminal Input
- **Assets at Risk:** User shell environment, credentials in terminal history, TUI display integrity.
- **Attacker Profile:** Malicious instructions on websites convincing users to copy-paste multiline commands ("pastejacking") or exploit ANSI escape codes.
- **Entry Points:** Interactive Cockpit input loop (`octoflow/cockpit/app.py:500-600`), Typer CLI option parsing (`octoflow/cli.py`).
- **Existing Controls:**
  - `RouterClassifier` (`octoflow/router.py:400-500`): Classifies commands into `OCTOFLOW_NATIVE`, `OCTOFLOW_MUTATING`, `SHELL_SIMPLE`, `SHELL_EXPLICIT`, and `DESTRUCTIVE`.
  - `RouterConfirmation` (`octoflow/router.py:650-770`): Blocks destructive actions (`rm -rf`, `git reset --hard`) until confirmed.
  - Sensitive input masking (`octoflow/config.py:150-180`): Uses `getpass.getpass()` for interactive API key configuration.
- **Gaps Identified:**
  - Multiline pastejacking: Cockpit input processing does not strip carriage returns/newlines before parsing, potentially executing the first line immediately before the user reviews it.
  - Terminal ANSI injection: Unescaped ANSI escape sequences in command arguments can alter terminal title or conceal malicious payload text.
- **Threat Status:** **PARTIAL** (Destructive confirmation mitigated in `tests/test_router.py::test_destructive_confirmation`; pastejacking unmitigated).

---

### Boundary 4: WebSocket / HTTP Clients on Localhost
- **Assets at Risk:** Swarm telemetry stream, cognitive decisions, confidential diff contents, live preview navigation.
- **Attacker Profile:** Malicious web pages visited in the developer's browser attempting Cross-Site WebSocket Hijacking (CSWSH) or DNS rebinding; unauthorized local user accounts.
- **Entry Points:** `ws://127.0.0.1:8088/ws/telemetry`, `http://127.0.0.1:8088/api/history`, `/api/health` (`octoflow/server.py:240-280`).
- **Existing Controls:**
  - Strict loopback bind (`127.0.0.1`, `octoflow/server.py:44, 371`).
  - DNS Rebinding protection via Host header middleware (`octoflow/server.py:241-255`).
  - WebSocket RFC 6455 Origin validation (`octoflow/server.py:258-267`).
  - Structural field stripping and secret redaction (`octoflow/server.py:100-150`).
- **Gaps Identified:**
  - **Missing Origin Header Bypass:** `octoflow/server.py:260-267` permits incoming WebSocket connections whenever the `Origin` header is absent (allowing local non-browser processes or curl scripts without authentication).
  - **Lack of Local Session Token:** Telemetry and history endpoints lack an ephemeral bearer token or secret cookie, allowing any unprivileged process running on the same host to spy on swarm actions.
  - **Visualizer Live Preview URL Injection:** `visualizer/src/main.ts:973, 985` assigns `sandboxIframe.src = url` and `btnSandboxExternal.href = url` without scheme verification, enabling `javascript:` URI injection.
- **Threat Status:** **PARTIAL** (Origin & Host checks mitigated in `tests/test_server.py::test_origin_validation` and `test_host_rebinding_defense`; local token and URL scheme validation open).

---

### Boundary 5: MCP Client (Cursor / Claude Code) Calling Tools
- **Assets at Risk:** Local repository integrity, MCP server stdio channel, tool execution authority.
- **Attacker Profile:** Malicious prompt in Cursor/Claude Code driving the LLM to call OctoFlow MCP tools with hazardous parameters.
- **Entry Points:** JSON-RPC 2.0 messages over standard I/O (`octoflow/mcp.py:323-349`).
- **Existing Controls:**
  - Restricted tool registry (`octoflow/mcp.py:104-171`): Only 3 tools exposed (`octoflow_run_swarm`, `octoflow_inspect_arms`, `octoflow_recall_memory`).
  - Workspace resolution to canonical path (`octoflow/mcp.py:99`).
- **Gaps Identified:**
  - **Stdio Stream Pollution:** `octoflow/mcp.py:323-349` shares process `sys.stdout` with JSON-RPC. Any background log, arm progress output, or external tool writing to stdout corrupts JSON-RPC framing, breaking client communication or causing protocol desync.
  - **Unattended Swarm Execution:** MCP tool `octoflow_run_swarm` initiates autonomous multi-cycle swarms that modify filesystem files without interactive human-in-the-loop review.
- **Threat Status:** **PARTIAL** (Workspace path resolved; stdio isolation and unattended mutation gating open).

---

### Boundary 6: Generated Apps Launched by Ignition
- **Assets at Risk:** Host network interfaces, parent environment secrets (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GITHUB_TOKEN`), local process namespace.
- **Attacker Profile:** Hallucinated or maliciously injected application code synthesized by the swarm executing in the host developer environment.
- **Entry Points:** `octoflow/ignition.py:1080-1170` (`_spawn_python_backend`, `_spawn_node_frontend`, `_spawn_static_server`).
- **Existing Controls:**
  - Localhost binding flags (`--host 127.0.0.1`, `--bind 127.0.0.1`, `octoflow/ignition.py:1102, 1135, 1159`).
  - Process group tracking and cleanup (`octoflow/ignition.py:47-98` `kill_process_group`).
- **Gaps Identified:**
  - **CRITICAL: Unscrubbed Environment Inheritance:** In `octoflow/ignition.py:1084` and `1132`, `env = os.environ.copy()` is passed to `subprocess.Popen`. All parent API keys and secrets are leaked directly to the generated application process.
  - **Unconstrained Fallback Entrypoint:** In `octoflow/ignition.py:1107`, if FastAPI regex matching fails, `cmd = [sys.executable, str(entrypoint)]` is executed without forced loopback binding, allowing the script to bind to `0.0.0.0` or make outbound network requests.
- **Threat Status:** **OPEN** (Process cleanup mitigated in `tests/test_ignition.py`; environment scrubbing and port enforcement open).

---

### Boundary 7: Pre-Commit Hook and CI Generator Outputs
- **Assets at Risk:** Developer git commit workflow, repository `.git/hooks`, GitHub Actions repository secrets.
- **Attacker Profile:** Contributor submitting PRs to trigger CI workflows, or malicious repository clone executing auto-onboarding.
- **Entry Points:** `octos install-hooks` (`octoflow/commands/guard.py:108-138`), `octos onboard` (`octoflow/onboarding.py:122-223`), `generate_github_action_workflow` (`octoflow/ci.py:68-76`).
- **Existing Controls:**
  - Static AST and JSON syntax inspection (`octoflow/commands/guard.py:76-92`, `octoflow/ci.py:190-202`).
  - Secret scanning regexes (`guard.py:44-50`, `ci.py:57-65`).
- **Gaps Identified:**
  - **Unconditional Hook Overwrite:** `octoflow/commands/guard.py:127` overwrites `.git/hooks/pre-commit` without backing up existing hooks or warning the user.
  - **CI Workflow Secret Exposure:** Generated workflow (`octoflow/ci.py:48-52`) binds secrets on `pull_request` triggers (`[opened, synchronize]`), allowing PR authors in fork-friendly repositories to extract secrets via modified tests or build scripts.
  - **Global IDE Config Injection:** `octoflow/onboarding.py:165, 179` writes directly to global `~/.claude.json` and system `claude_desktop_config.json` without confirmation or strict `0600` permissions.
- **Threat Status:** **OPEN** (Syntax check verified in `tests/test_guard.py`; hook overwrite and CI secret scoping open).

---

### Boundary 8: Third-Party Dependencies
- **Assets at Risk:** Application runtime integrity, developer supply chain, memory limits.
- **Attacker Profile:** Compromised upstream dependency maintainer, malicious transitive dependency update, dependency typosquatting.
- **Entry Points:** `pyproject.toml` Python dependencies, `visualizer/package.json` npm packages.
- **Existing Controls:**
  - PyTorch made optional dependency (`pyproject.toml`, P2.5).
  - Version pinning and lockfile in `visualizer/package-lock.json`.
  - Static typing ratchet (mypy) and linting (ruff, eslint).
- **Gaps Identified:**
  - `pip-audit` detected 55 vulnerabilities in installed venv packages (`certifi`, `filelock`, `pillow`).
  - `npm audit` detected 11 moderate severity vulnerabilities in `visualizer` (`minimatch <11.0.1`).
  - Lack of automated CI audit gate to reject builds introducing High/Critical CVEs.
- **Threat Status:** **OPEN** (Audit baseline recorded; automated dependency security gate open).

---

## 3. Threat Mitigation Summary Matrix

| Boundary | Primary Threat (STRIDE) | Severity | Control Citation | Mitigation Status | Test Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **B1: LLM Output** | Arbitrary tool execution / shell injection | High | `octoflow/tools.py:126` | **PARTIAL** | `tests/test_tools.py::test_tool_policy_confinement` |
| **B2: Workspace Files** | Indirect prompt injection via codebase files | High | `octoflow/tools.py:230` | **OPEN** | None (Untested) |
| **B3: Terminal Input** | Destructive command execution via paste | Medium | `octoflow/router.py:650` | **PARTIAL** | `tests/test_router.py::test_destructive_confirmation` |
| **B4: Localhost Network** | CSWSH / DNS Rebinding / Stored XSS | Critical | `octoflow/server.py:241` | **PARTIAL** | `tests/test_server.py::test_origin_validation` |
| **B5: MCP Client** | Stdio pollution & unconfirmed mutations | Medium | `octoflow/mcp.py:99` | **PARTIAL** | `tests/test_mcp.py::test_mcp_server_initialize` |
| **B6: Ignition Apps** | Parent secret inheritance by generated code | Critical | `octoflow/ignition.py:1084`| **OPEN** | None (Untested) |
| **B7: Hooks & CI** | Hook destruction & CI secret leak | High | `octoflow/commands/guard.py:127`| **OPEN** | None (Untested) |
| **B8: Dependencies** | Supply chain vulnerabilities (CVEs) | Medium | `pyproject.toml` | **OPEN** | None (Untested) |
