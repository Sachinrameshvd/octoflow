# ADR 0005: Workspace Tool Policy and Advisory Path Security over Rigid Sandboxes

## Status
Accepted

## Context
Autonomous software agents require file write capabilities, test execution access, and CLI tooling. Running every tool execution within rigid virtualization or isolated Docker containers guarantees process containment, but introduces 1-3 second container spin-up latencies, heavy daemon dependencies, and failures inside nested CI/container environments (e.g. Docker-in-Docker or Kubernetes pods).

## Decision
Adopt an in-process, policy-driven security model (`WorkspaceSandbox`) as the primary execution runtime, while maintaining ephemeral Docker sandboxing as an optional flag:
1. Enforce strict workspace root boundaries using canonicalized path validation (`os.path.commonpath`). Path traversal attempts (`../`) targeting outside the workspace are blocked with `SecurityError`.
2. Manage concurrent multi-arm file writes using file-level advisory locks (`.lock`) with bounded timeouts.
3. Restrict shell command execution to an explicit allowlist (`DEFAULT_ALLOWED_COMMANDS`), covering standard compilers, test runners, and linters.
4. Require explicit user interactive confirmation (`[y/N]`) for compound shell operators (`;`, `&&`, redirects) and destructive commands (`rm`, `sudo`, `chmod -R`).
5. Support containerized execution via `--sandbox docker` for users explicitly desiring ephemeral container boundaries.

## Alternatives Considered
- **Mandatory Docker Sandboxing:** Require Docker for all runs. Rejected because many development laptops lack Docker Desktop or permissions, and container startup overhead kills interactive swarm speed.
- **Unrestricted Host Shell (`shell=True`):** Pass agent-generated strings directly to `/bin/sh`. Rejected due to extreme vulnerability to prompt injection and accidental destructive actions (`rm -rf /`).

## Consequences
- **Positive:** Sub-millisecond tool execution, zero container prerequisites, and seamless operation across macOS, Linux, and WSL.
- **Negative:** In-process policy enforcement relies on Python AST analysis and string sanitization, which requires ongoing maintenance against novel bypass patterns.

## Evidence & References
- Implementation: [`octoflow/tools.py`](../../octoflow/tools.py) (`WorkspaceSandbox`, `DEFAULT_ALLOWED_COMMANDS`)
- Cockpit Router: [`octoflow/cockpit/input.py`](../../octoflow/cockpit/input.py) (destructive confirmation prompts)
- Verification: [`tests/test_tools_security.py`](../../tests/test_tools_security.py)
- Commit: `a93de48` (P5.3 Workspace sandbox security and advisory locking)

## What Would Change This Decision
If OctoFlow is deployed as a multi-tenant shared cloud service executing untrusted third-party user missions, requiring hardware-level microVM isolation (e.g. Firecracker or gVisor).

