# OctoFlow Security Model & Architecture

This document defines OctoFlow's defense-in-depth security model across tool sandboxing, localhost network services, telemetry streaming, and credential management.

---

## 1. Local Telemetry Server

The OctoFlow 3D Connectome Visualizer bridge (`octoflow/server.py`) streams live active-inference swarm telemetry over WebSockets and serves static assets and configuration endpoints over HTTP. Localhost network services face unique security challenges, particularly from browser-based cross-origin attacks and DNS rebinding.

### 1.1 Bind Address & Network Isolation
- **Default Bind Address:** The server binds strictly to IPv4 loopback `127.0.0.1` by default (port 8088 or next available ephemeral port). It never binds to `0.0.0.0` or wildcard interfaces by default.
- **External Exposure Warning:** A `--host` flag may override the bind address when intentional remote visualization is required. When binding to any non-localhost interface, OctoFlow emits an explicit security warning to `stderr` and logging subsystems:
  `SECURITY WARNING: Telemetry server binding to '<host>' instead of 127.0.0.1. This exposes the swarm and visualizer bridge to the external network.`

### 1.2 WebSocket Origin Validation (RFC 6455 Code 1008)
WebSockets are not constrained by the browser's Same-Origin Policy during connection establishment; any malicious webpage visited in a browser could attempt to open a WebSocket connection to `ws://localhost:8088`.
- **Enforcement:** Every incoming WebSocket connection to `/ws/telemetry` is inspected:
  - **Missing Origin:** Permitted (enables local command-line tools, test harnesses, and automated scripts).
  - **Exact Origin Match:** Permitted only if the `Origin` header matches:
    - `http://127.0.0.1:<port>` / `http://localhost:<port>`
    - `https://127.0.0.1:<port>` / `https://localhost:<port>`
    - The custom bound `--host` (if specified).
  - **Vite Development Origin:** Permitted only when `dev_mode` is explicitly activated (`--dev`, `OCTOFLOW_DEV=1`, or `VITE_DEV=1`) matching `http://localhost:5173` or `http://127.0.0.1:5173`.
  - **Untrusted Origins:** Any other origin (e.g., `https://evil.example`, `http://attacker.com`) is rejected immediately with RFC 6455 close code `1008` (Policy Violation).

### 1.3 HTTP Host Header Validation (DNS Rebinding Defense)
DNS rebinding attacks bypass localhost IP restrictions by binding an attacker-controlled domain name to `127.0.0.1`.
- **Enforcement:** An ASGI middleware intercepts every incoming HTTP request and validates the `Host` header before route handling.
- **Permitted Hosts:** Only `127.0.0.1`, `localhost`, `testserver` (internal test client), and the explicitly configured bind host are accepted.
- **Rejection:** Requests with unauthorized Host headers (e.g., `Host: evil.example`) are rejected immediately with status `400 Bad Request`.

### 1.4 Telemetry Payload Structural Sanitization
Telemetry streams broadcast the internal cognitive state of the 8-arm swarm to the 3D WebGL visualizer. To prevent accidental data or secret exfiltration:
- **Structural Fields Broadcast:** Arm ID, specialist role, state/status, surprise delta ($dS$), sensory thresholds ($\theta$), dynamic coalition bindings, deliverable progress, and token savings.
- **Sensitive Field Stripping:** All prompt text (`prompt`, `system_prompt`, `user_prompt`, `messages`), file contents (`file_content`, `content`, `diff`, `patch`), subprocess outputs (`stdout`, `stderr`, `command_output`), and credentials (`api_key`, `token`, `secret`) are recursively stripped from telemetry packets.
- **Free-Text Redaction:** All free-text strings and summaries pass through `redact_secrets()`, ensuring any accidental credential references are replaced with sanitization placeholders before being broadcast or saved to session history.

---

## 2. Secrets & Configuration Hardening

### 2.1 File System Permissions (POSIX Modes)
- **Configuration Directory:** `~/.octoflow` is created with permissions `0700` (`rwx------`), restricting access exclusively to the owner.
- **Configuration File:** `~/.octoflow/config.json` is created using `os.open` with flags `O_CREAT | O_WRONLY` and mode `0600` (`rw-------`).
- **Automatic Auto-Hardening on Load:** When loading configuration, OctoFlow inspects the permissions of both `~/.octoflow` and `config.json`. If either has permissions looser than `0700` or `0600` respectively, OctoFlow tightens them and prints a one-line notice:
  `Notice: Hardened permissions on <path> to 0o600 (was <old_mode>).`

### 2.2 Terminal Input & Display Masking
- **Non-Echoing Setup:** When configuring API keys during `octos setup`, inputs are captured using `getpass.getpass()`, preventing credentials from being echoed to the terminal screen.
- **Display Masking:** In all diagnostic listings, configuration displays, and REST endpoints (such as `/llm/pool`), credentials are never printed in plain text. They are masked to display only the first three characters followed by `****` (e.g., `sk-****`).

### 2.3 Artifact & Git Exclusions
The repository `.gitignore` strictly excludes configuration artifacts, keys, and checkpoint outputs:
- `.octoflow/` and `.octoflow-mission/`
- `*.key` and `*.pem`
- `*.checkpoint` and `checkpoints/`
- `.octoflow_bench/` and `octoflow_bench/`

---

## 3. Tool Execution Sandbox

OctoFlow's `WorkspaceSandbox` (`octoflow/tools.py`) enforces strict boundaries on file manipulation and command execution:
- **Path Confinement:** Strict lexical and symlink path resolution within the canonical workspace directory.
- **Command Allowlist:** Subprocesses execute argument arrays with `shell=False` against a curated allowlist of compilers, package managers, and test runners.
- **Controlled Subprocess Environment:** Sensitive environment variables (API keys, tokens) are purged from child process environments (`SAFE_ENV_PASSTHROUGH`).
- **Resource Timeouts & Bounded Capture:** Subprocesses have bounded execution timeouts (default 60s, max 300s) and bounded output buffers (64 KB).
