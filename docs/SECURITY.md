# OctoFlow Tool Sandbox Security Policy

## 1. Overview & Threat Model

OctoFlow executes automated workflows across multiple concurrent arms that interact with the local filesystem and spawn child processes. The `WorkspaceSandbox` in `octoflow/tools.py` provides defense-in-depth confinement to prevent:
1. **Arbitrary Filesystem Escape:** Unauthorized reading or writing of sensitive files outside the designated project workspace (e.g., `~/.ssh`, `~/.aws`, system configuration).
2. **Arbitrary Command Execution:** Execution of unvetted, dangerous, or chained shell commands requested by an LLM or unverified agent prompt.
3. **Resource Exhaustion & Zombie Processes:** Indefinitely hanging subprocesses or excessive stdout/stderr memory bloat.
4. **Secret Leakage:** Exposure of sensitive environment variables (API keys, authentication tokens) to child processes or in tool outputs, exceptions, and logs.

---

## 2. Workspace Confinement

### 2.1 Canonical Path Resolution
All file-oriented operations (`read_file`, `write_file`, `list_dir`) validate target paths against the canonical, resolved workspace root:
- Null-byte injection (`\x00`) is strictly rejected.
- Path traversal sequences (such as `../` or relative paths climbing above the root) are resolved and checked with strict subpath containment (`target.is_relative_to(root)`).
- Absolute paths pointing outside the workspace boundary are rejected immediately with a permission violation error.

### 2.2 Symlink & Parent Directory Traversal Protection
- Direct symlinks within the workspace that point to targets outside the workspace root are blocked for both reads and writes.
- Symlinked parent directories: For nonexistent target files (such as when writing a new file into a subfolder), the confinement mechanism iterates through every existing ancestor directory up to the workspace root, resolving each to ensure no intermediate symlink redirects writes outside the project root.

### 2.3 Advisory File Locking
Multi-arm concurrent operations utilize advisory write locks (`acquire_lock` / `release_lock` / `file_lock`) to serialize file mutations and prevent race conditions.

---

## 3. Command Execution Policy

### 3.1 Argument Arrays & `shell=False`
Commands in `run_command` are executed using argument arrays (`argv`) with `shell=False` by default:
- Commands are parsed into argument vectors via `shlex.split`.
- Direct execution avoids invoking a system shell (`/bin/sh` or `/bin/bash`), neutralizing shell expansion attacks and command injection.

### 3.2 Command Allowlist
Only explicitly permitted development utilities, build tools, package managers, and test runners can be invoked. The default allowlist (`DEFAULT_ALLOWED_COMMANDS`) includes:
- **Interpreters & Runtimes:** `python`, `python3`, `node`
- **Testing & Quality Assurance:** `pytest`, `coverage`, `mypy`, `ruff`, `flake8`, `black`
- **Package & Build Managers:** `npm`, `npx`, `vite`, `cargo`, `rustc`, `go`, `make`, `docker`
- **Version Control & Safe Utilities:** `git`, `ls`, `cat`, `echo`, `pwd`, `grep`, `find`, `mkdir`, `touch`, `cp`, `mv`, `which`, `diff`, `head`, `tail`, `wc`, `sort`, `uniq`

Any unlisted binary (e.g., `curl`, `wget`, `nc`, `rm`, `sudo`, `dd`) is blocked with an actionable error.

### 3.3 Shell Metacharacter & Chaining Rejection
Unquoted shell metacharacters and compound execution constructs (`|`, `;`, `&&`, `||`, `>`, `<`, backticks, and `$(...)`) are rejected before execution.

### 3.4 Unrestricted Execution Opt-in
If a legitimate development task requires running an unlisted command, callers must explicitly provide `allow_unrestricted=True` to `run_command(..., allow_unrestricted=True)`. Even with `allow_unrestricted=True`, commands are executed with `shell=False` using parsed argument arrays and controlled environments unless explicitly overridden. Cockpit confirmation alone does not bypass sandbox checks.

---

## 4. Timeouts & Resource Limits

### 4.1 Subprocess Timeouts
- **Default Timeout:** 60.0 seconds.
- **Configurable Maximum:** 300.0 seconds (5 minutes). Any request exceeding the maximum limit is clamped to 300 seconds.
- **Enforcement:** Subprocesses run with `start_new_session=True`. If a command exceeds its timeout limit, `subprocess.TimeoutExpired` is triggered, terminating the process and returning exit code `124`.

### 4.2 Bounded Capture
Stdout and stderr buffers are bounded at 64 KB (`MAX_CAPTURE_BYTES = 65,536`). Any output exceeding 64 KB is truncated with a clear diagnostic notice, preventing memory spikes and log pollution.

---

## 5. Controlled Environment & Secret Redaction

### 5.1 Controlled Subprocess Environment
Subprocesses do not inherit the complete host environment. Instead, only a minimal, vetted set of system variables is passed through (`SAFE_ENV_PASSTHROUGH`):
- Essential system paths: `PATH`, `LANG`, `LC_ALL`, `TMPDIR`, `TEMP`, `TMP`, `USER`, `LOGNAME`, `HOME`
- Python runtime variables: `PYTHONPATH`, `PYTHONUNBUFFERED`, `PYTHONDONTWRITEBYTECODE`, `VIRTUAL_ENV`
- Terminal settings: `TERM`

### 5.2 Secret Scrubbing
The controlled environment automatically purges any environment key containing:
`KEY`, `TOKEN`, `SECRET`, `PASSWORD`, `CREDENTIAL`, `AUTH`, `APIKEY`

This prevents accidental inheritance of API tokens (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`) by executed scripts or child tools.

### 5.3 Output & Log Redaction
All tool output (stdout, stderr, exception messages, and directory listings) is processed through `redact_secrets()`, ensuring credentials and tokens are replaced with sanitization placeholders before being returned to agents or stored in logs.

---

## 6. Structured Error Codes

Tools return structured `ToolResult` objects with standard POSIX diagnostic exit codes:
- **0:** Successful execution.
- **1:** General error (e.g. read failure, lock contention).
- **124:** Command execution timeout.
- **126:** Disallowed command, blocked shell metacharacters, or path traversal security violation.
- **127:** Executable not found on system PATH.

---

## 7. Known Limitations & Defense-in-Depth

The `WorkspaceSandbox` provides application-level confinement and defense-in-depth:
- **Not an OS-Level Sandbox:** It is not an operating-system kernel container (such as Linux namespaces, cgroups, or seccomp-bpf). It does not isolate network sockets, kernel syscalls, or shared memory unless Docker mode (`sandbox_mode="docker"`) is explicitly enabled.
- **Time-of-Check to Time-of-Use (TOCTOU):** In environments with malicious concurrent processes mutating directory structures, symlink swapping between resolution and read/write is theoretically possible on POSIX filesystems without kernel filesystem namespace isolation (`unshare` / `bwrap`).
- **External Network Access:** Subprocesses inherit host network access unless Docker isolation with `--network none` is configured.

For high-assurance deployments running untrusted third-party code, enable Docker sandbox mode (`sandbox_mode="docker"`) with isolated container networking.
