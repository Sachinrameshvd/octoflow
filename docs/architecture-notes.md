# Architecture Notes: Cockpit Package (P2.1) & Command Architecture (P2.2)

## Overview
The `octoflow` CLI and Cockpit system has been decoupled into dedicated packages:
1. `octoflow.cockpit` (P2.1): Modularizes the interactive cephalopod terminal cockpit TUI.
2. `octoflow.commands` (P2.2): Modularizes every Typer command into its own cohesive module with lazy imports of heavy dependencies (`torch`, `fastapi`, `uvicorn`, `onnxruntime`), reducing `octoflow/cli.py` to pure wiring (< 160 lines) and accelerating `--help` startup by >70%.

---

## Command Architecture & Module Map (P2.2)

```
octoflow/commands/
├── __init__.py         # Package declaration
├── audit.py            # audit: 1-100 system readiness and security diagnostic
├── bench.py            # bench: standardized 8-arm algorithmic & architectural benchmarks
├── consortium.py       # consortium, octopolis: multi-octopus swarm deployment
├── dashboard.py        # render_dashboard, render_consortium_dashboard: Rich TUI displays
├── doctor.py           # doctor: environment, git, model, and network health diagnostics
├── eject.py            # eject: standalone agent harness export
├── federation.py       # federation: zero-trust multi-machine agent & PII filter
├── guard.py            # guard, install-hooks: staged git AST & secret leak verification
├── guild.py            # guild: 8-arm specialist roster and custom guild management
├── heal.py             # heal, fix: closed-loop autonomous test suite repair
├── init.py             # init-ide, init, init-action: Cursor, Claude, VS Code, CI setup
├── install_claude.py   # install-claude: register native Claude Code plugin and /octo commands
├── manual.py           # manual, docs: interactive developer manual & field guide
├── mcp.py              # mcp, mcp-serve: Model Context Protocol JSON-RPC stdio servers
├── monorepo.py         # monorepo: multi-package topology scanner and arm partitioner
├── notify.py           # notify: team Slack/Discord webhook alerts
├── record.py           # record: asciinema v2 .cast terminal recording
├── report.py           # report, export: standalone HTML audit reports with connectome replay
├── review_pr.py        # review-pr: 3-arm CI/CD PR review over git diffs
├── run.py              # run, train, octos_run: core swarm execution orchestrator
├── runner.py           # runner, play: Benthic Dot Runner game
├── setup.py            # setup: guided first-run API key, provider, and theme wizard
├── theme.py            # theme, banner, screensaver: developer palette switcher & 3D animations
├── triage.py           # triage, diff-review: patch inspector & AST triage
└── ui.py               # ui: 3D Cephalopod Connectome Visualizer bridge
```

### Module Responsibilities & Line Counts

| Module | Registered Commands | Description | Lines | Heavy Imports Deferred |
|---|---|---|---|---|
| `cli.py` | — | Typer app creation, callbacks, and command wiring | 155 | All |
| `commands/run.py` | `run`, `train`, `octos run` | Swarm execution orchestrator | 494 | `conductor`, `server`, `ignition`, `torch` |
| `commands/dashboard.py` | — | Rich live TUI dashboard renderers | 296 | Pure rendering |
| `commands/setup.py` | `setup` | First-run interactive setup wizard | 226 | `cockpit` |
| `commands/doctor.py` | `doctor` | Environment and diagnostics | 147 | `httpx` |
| `commands/guard.py` | `guard`, `install-hooks` | Git pre-commit AST & secret scanner | 135 | `git`, `ast` |
| `commands/theme.py` | `theme`, `banner`, `screensaver` | Palette switcher & 3D ASCII player | 114 | `theme_selector` |
| `commands/guild.py` | `guild` | Specialist 8-arm rosters | 67 | Config only |
| `commands/review_pr.py` | `review-pr` | 3-arm CI/CD diff audit | 61 | `ci` |
| `commands/init.py` | `init-ide`, `init`, `init-action`| Omni-IDE onboarding & GitHub Actions | 53 | `onboarding`, `ci` |
| `commands/monorepo.py` | `monorepo` | Package topology scanner | 48 | `monorepo` |
| `commands/ui.py` | `ui` | 3D Connectome visualizer bridge | 48 | `server`, `uvicorn`, `fastapi` |
| `commands/consortium.py` | `consortium`, `octopolis` | Multi-octopus consortium launcher | 43 | `run`, `consortium` |
| `commands/heal.py` | `heal`, `fix` | Closed-loop test healing | 40 | `healing` |
| `commands/federation.py` | `federation` | PII scrubber & zero-trust federation | 39 | `federation` |
| `commands/install_claude.py` | `install-claude` | Claude Code plugin installer | 37 | Rich only |
| `commands/report.py` | `report`, `export` | HTML mission audit report generator | 34 | `report` |
| `commands/mcp.py` | `mcp`, `mcp-serve` | Stdio MCP JSON-RPC servers | 33 | `mcp` |
| `commands/record.py` | `record` | Asciinema session recorder | 30 | `recorder` |
| `commands/runner.py` | `runner`, `play` | Benthic Dot Runner game | 29 | `runner` |
| `commands/triage.py` | `triage`, `diff-review` | Uncommitted patch inspector | 27 | `triage` |
| `commands/bench.py` | `bench` | 8-arm algorithmic benchmarks | 26 | `bench` |
| `commands/audit.py` | `audit` | 1-100 system readiness grader | 25 | `audit` |
| `commands/manual.py` | `manual`, `docs` | Cephalopod manual & docs viewer | 24 | `manual` |
| `commands/notify.py` | `notify` | Slack & Discord webhook dispatcher | 28 | `notify` |
| `commands/eject.py` | `eject` | Standalone harness exporter | 20 | `eject` |

*No file in `octoflow/commands/` exceeds 500 lines (all well under the 600-line ceiling).*

---

## Import-Time Optimization Results

Heavy libraries (`torch`, `fastapi`, `uvicorn`, `onnxruntime`) were deferred to command execution time rather than module import time. Module-level lazy resolution (`PEP 562 __getattr__`) was also introduced in `octoflow/__init__.py`.

### Benchmark: `python -X importtime -m octoflow.cli --help`

| Metric | Before (P2.1 Baseline) | After (P2.2 Modularized) | Improvement |
|---|---|---|---|
| **Cumulative Import Time** | 1,232.1 ms | 321.3 ms | **-73.9% (-910.7 ms)** |
| **Wall Clock `--help` Time** | 1.491 s | 0.384 s | **-74.2% (~3.9x faster)** |
| **`torch` on `--help`** | ~808 ms | **0 ms (Not imported)** | Eliminated |
| **`uvicorn` on `--help`** | ~11 ms | **0 ms (Not imported)** | Eliminated |
| **`fastapi` on `--help`** | ~89 ms | **0 ms (Not imported)** | Eliminated |
| **`onnxruntime` on `--help`** | 0 ms | **0 ms (Not imported)** | Zero overhead |

---

## Snapshot Verification Test Suite
- Test location: `tests/test_cli_help_snapshots.py`
- Snapshot directory: `tests/snapshots/help/*.txt`
- Snapshot count: 71 snapshots (1 root help + 35 `app` commands + 1 `octos` root help + 34 `octos_app` commands).
- Terminal width normalization: `COLUMNS=100`.
- Snapshot comparison: **100% byte-for-byte identical**.

---

## Cockpit Package Architecture (P2.1)

```
octoflow/cockpit/
├── __init__.py    # Public API exports and backward-compatible symbol mappings
├── app.py         # Main interactive REPL loop (run_cockpit, interactive_cockpit)
├── input.py       # Terminal cbreak/raw mode, 20 FPS keyboard polling, bracketed paste
├── render.py      # HUD panel, ring topology, prompt text, composite table grids, banners
├── session.py     # CockpitSession dataclass encapsulating mutable state
└── shell.py       # Non-blocking confirmation prompts and direct shell execution (router.py)
```

### 1. `octoflow.cockpit.session`
- **Responsibility:** Replaces module-level mutable globals with a typed `CockpitSession` dataclass.
- **State Managed:** `workspace`, `previous_workspace` (for `cd -`), `theme`, `current_model`, `current_octos`, `current_guild`, `current_budget`, `host`, `port`, `visualizer_url`, `broadcaster`, `running`, and `history`.

### 2. `octoflow.cockpit.input`
- **Responsibility:** Non-blocking 20 FPS keyboard event polling (`select.select` timeout `<= 0.045s`), arrow key navigation (`\x1b[C`, `\x1b[D`), and bracketed paste parsing (`\x1b[200~` ... `\x1b[201~`).
- **Guaranteed Terminal Restoration:** Uses `@contextlib.contextmanager` `raw_terminal_mode(fd)` with guaranteed `termios.tcsetattr` restoration in `finally` blocks, registered `atexit` cleanup, and `SIGTERM`/`SIGHUP` signal restoration handlers.
- **Strict Non-blocking:** Zero calls to blocking `input()` or `console.input()`. Falls back to non-blocking `sys.stdin.readline()` in non-tty and piped environments.

### 3. `octoflow.cockpit.render`
- **Responsibility:** Terminal frame composition and visual UI rendering.
- **Components:**
  - `build_hud_panel`: Workspace path, git branch detection, model tier, budget, and 3D visualizer URL.
  - `build_topology_text`: Ganglia ring topology indicator (Arms 0–7).
  - `build_prompt_text`: Multi-line paste indicator (`[X lines pasted]`), dynamic theme prompt (`octos ❯`), and blinking block cursor.
  - `build_cockpit_grid`: Composites Banner + HUD + Topology + Benthic Runner + Prompt into a single Table grid.
  - `build_confirm_grid`: Non-blocking confirmation dialog grid maintaining the 20 FPS runner animation.
  - `print_welcome_banner`: Static or animated 3D ASCII banner rendering.

### 4. `octoflow.cockpit.shell`
- **Responsibility:** Shell command routing and safety execution using `octoflow.router`.
- **In-Process Directory Navigation:** Custom `cd` handler operating on `session.workspace` and `session.previous_workspace` without mutating global process cwd (`os.chdir`).
- **Safety Confirmation:** Strict non-blocking confirmation dialog (`y` confirms, all other keys or Enter default to No).
- **Execution & Capture:** 60s subprocess timeout, 64 KB capture truncation, and secure 0600 file history logging (`~/.octoflow/history`).

### 5. `octoflow.cockpit.app`
- **Responsibility:** Main interactive REPL coordinator (`run_cockpit` / `interactive_cockpit`).
- **Coordination:** Readline tab completion, command dispatch, slashless normalization, conversational reflex classification (`INQUIRY` vs `SWARM_GOAL`), and swarm delegation.

## Backward Compatibility & Re-Exports
To ensure zero breaking changes for external scripts, existing tests, and IDE integrations, `octoflow/cli.py` re-exports all extracted symbols:
- `run_cockpit`, `interactive_cockpit`
- `CockpitSession`, `CockpitInput`
- `get_live_cockpit_input`, `get_live_wizard_input`
- `confirm_live_cockpit`, `print_welcome_banner`
- `render_dashboard`, `render_consortium_dashboard`
- `run`, `train`, `octos_run`
- `run_doctor`, `doctor_cli_cmd`
- `run_guard`, `install_git_hooks`, `guard_cli_cmd`, `install_hooks_cli_cmd`
- `export_cli_cmd`
- `app_theme_cmd`, `octos_theme_cmd`, `app_banner_cmd`, `octos_banner_cmd`, `app_screensaver_cmd`, `octos_screensaver_cmd`
- `run_setup_wizard`, `setup_cli_cmd`
- `install_claude_cli_cmd`
