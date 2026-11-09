# Investigate Non-Blocking Windows Console Input in Terminal Cockpit

**Difficulty:** Intermediate  
**Labels:** `help wanted`, `enhancement`  
**Mentoring Pointer:** Inspect [`octoflow/cockpit/input.py`](../../octoflow/cockpit/input.py) and the non-blocking input design notes in [`docs/architecture.md`](../architecture.md).

---

## Context
OctoFlow's terminal cockpit operates at 20 frames per second to deliver smooth live metrics and interactive mission steering without blocking.

To achieve non-blocking keyboard input on Unix-like operating systems (macOS and Linux), [`octoflow/cockpit/input.py`](../../octoflow/cockpit/input.py) relies on standard POSIX modules `termios`, `tty`, and `select.select()`.

On native Windows environments (outside of WSL2), importing `termios` fails with `ModuleNotFoundError`. While WSL2 is the recommended environment for Windows developers, exploring a native Windows console input handler using standard library `msvcrt` would make local triage easier for Windows developers.

---

## Objectives & Requirements
1. Conduct an architectural investigation on non-blocking keyboard input on Windows.
2. Prototype a `WindowsConsoleInput` class using Python standard library `msvcrt.kbhit()` and `msvcrt.getch()`.
3. In [`octoflow/cockpit/input.py`](../../octoflow/cockpit/input.py), gracefully select `WindowsConsoleInput` when `os.name == 'nt'`.
4. Ensure zero regressions on macOS and Linux platforms (POSIX path must remain unmodified).
5. Document findings in an ADR or spike notes under `docs/adr/`.

---

## Files to Touch
- [`octoflow/cockpit/input.py`](../../octoflow/cockpit/input.py): Abstract input interface with POSIX and Windows implementations.
- [`tests/test_cockpit_imports.py`](../../tests/test_cockpit_imports.py): Test input class instantiations with mocked OS types.

---

## Acceptance Criteria
- [ ] On native Windows (or mocked `os.name == 'nt'`), importing and initializing cockpit input does not raise `ModuleNotFoundError`.
- [ ] Arrow keys, spacebar, and character input map to standard cockpit navigation events.
- [ ] Existing POSIX behavior on Linux and macOS remains completely unchanged and passing all tests.
- [ ] All unit tests pass with `pytest`.

