# Architecture Notes: Cockpit Package (P2.1)

## Overview
The `octoflow.cockpit` package modularizes the interactive cephalopod terminal cockpit TUI, extracting raw-mode input handling, frame rendering, state management, shell execution, and the main REPL loop out of `octoflow/cli.py` into dedicated, cohesive, and independently testable modules.

## Package Architecture & Module Responsibilities

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
To ensure zero breaking changes for external scripts and existing test suites, `octoflow/cli.py` re-exports the extracted symbols:
- `run_cockpit`, `interactive_cockpit`
- `CockpitSession`, `CockpitInput`
- `get_live_cockpit_input`, `get_live_wizard_input`
- `confirm_live_cockpit`, `print_welcome_banner`
- `FISH_SPRITE` and other runner components remain accessible from `octoflow.runner`.
