# Terminal Accessibility & Glyph Policy

OctoFlow provides complete terminal accessibility, cross-platform emulator compatibility, and CI/pipe scriptability across diverse environments.

## Standards Compliance

### 1. Zero-Emoji & Single-Width Glyphs
Terminals frequently misalign multi-column layout grids when rendering characters with ambiguous display widths or emoji presentation (such as `⚡` U+26A1 or `⏳` U+23F3). 
OctoFlow strictly enforces that **every active glyph has `wcwidth == 1`** and text presentation presentation.

- `BOLT`: Replaced wide `⚡` (U+26A1, wcwidth=2) with text-presentation `↯` (U+21AF, wcwidth=1) or ASCII `!`.
- `OK`: Replaced heavy `✔` (U+2714) with text check `✓` (U+2713, wcwidth=1) or ASCII `+`.
- `FAIL`: Replaced heavy `✖` (U+2716) with text cross `✗` (U+2717, wcwidth=1) or ASCII `x`.
- `WARN`: Text triangle `▲` (U+25B2, wcwidth=1) or ASCII `!`.
- `DIAMOND`: Geometric diamond `◈` (U+25C8, wcwidth=1) or ASCII `*`.
- `HOURGLASS`: Text dot `·` (U+00B7, wcwidth=1) or ASCII `~`.

### 2. NO_COLOR Standard
OctoFlow adheres to the open [NO_COLOR](https://no-color.org) specification. When the `NO_COLOR` environment variable is set (or `--no-color` is supplied), all ANSI color sequences are completely stripped from terminal and log outputs.

```bash
NO_COLOR=1 octoflow run "verify contracts"
# or
octoflow run "verify contracts" --no-color
```

### 3. Pure ASCII Fallback
For legacy terminals, serial consoles, or ASCII-only environments, `--ascii` (or `OCTOFLOW_ASCII=1`) forces all output to strictly use characters with byte values `< 128`. All Unicode box characters, arrows, and glyphs are automatically transliterated into ASCII equivalents (`+`, `-`, `|`, `*`, `>`, `<`).

```bash
octoflow run "verify contracts" --ascii
# or
OCTOFLOW_ASCII=1 octoflow
```

### 4. Non-TTY Pipes & Headless CI
When stdout is redirected or piped (`not sys.stdout.isatty()`), OctoFlow automatically:
- Disables interactive cockpit animations.
- Suppresses cursor control codes (`\x1b[2K`, `\x1b[1A`).
- Emits clean, line-oriented output suitable for `grep`, `cat`, and log aggregators.
- Enables plain execution mode for `run` and `consortium` commands.

```bash
octoflow run "build service" | cat
```

### 5. Non-Animated Static Mode
For accessibility needs sensitive to continuous movement or low-bandwidth SSH sessions, animations can be turned off via `--no-anim` or `OCTOFLOW_ANIM=0`.
In static mode:
- The cockpit maintains non-blocking keyboard input.
- Redraws occur **only** on user keystrokes, window resize, or state change. Two consecutive idle reads are byte-for-byte identical.

```bash
octoflow --no-anim
# or
OCTOFLOW_ANIM=0 octoflow
```

### 6. Narrow Terminal Adaptation (< 60 cols or < 15 rows)
When running in narrow split panes or small terminal windows:
- Large ASCII banners, topology rings, and benthic runner animations are skipped.
- A compact single-line HUD panel is rendered dynamically.
- Terminal resize events (`SIGWINCH`) are queried dynamically on every frame without crashing or throwing unhandled signals.

### 7. Scriptable Plain Mode, Quiet Mode, and Machine-Readable JSON
For automated pipelines and shell scripting:
- `--plain`: Forces line-oriented progress output in format: `[arm <id> <role>] <summary>`.
- `--quiet` / `-q`: Suppresses intermediate progress events, emitting only final status ribbons.
- `--json`: Outputs machine-readable JSON object representing the final mission outcome to stdout.

```bash
octoflow run "generate api schemas" --json | jq .status
```

---

## Central Glyph Table

All symbols used across OctoFlow must originate from `octoflow/glyphs.py`. Direct literal glyphs in UI or command strings are prohibited.

| Glyph Name | Standard Unicode (`wcwidth=1`) | ASCII Fallback (`ord < 128`) | Legacy Option (`--legacy-glyphs`) | Usage Description |
|:---|:---:|:---:|:---:|:---|
| `OK` | `✓` (U+2713) | `+` | `✔` | Task completion, test pass, verification |
| `FAIL` | `✗` (U+2717) | `x` | `✖` | Error, failure, violation |
| `WARN` | `▲` (U+25B2) | `!` | `▲` | Warnings, environmental interrupts |
| `BOLT` | `↯` (U+21AF) | `!` | `⚡` | Active firing arm, live service ignition |
| `BULLET` | `•` (U+2022) | `*` | `•` | List bullets, file lists |
| `MIDDLE_DOT`| `·` (U+00B7) | `.` | `·` | Standby arms, paused state |
| `CIRCLE` | `○` (U+25CB) | `o` | `○` | Hollow circle, frontend icon |
| `DISC` | `●` (U+25CF) | `*` | `●` | Filled circle, visualizer badge |
| `DIAMOND` | `◈` (U+25C8) | `*` | `◈` | Section header, mission milestone |
| `HOURGLASS`| `·` (U+00B7) | `~` | `·` | Elapsed ETA timer indicator |

---

## CLI Flags Reference

| Flag | Environment Variable | Default | Purpose |
|:---|:---|:---:|:---|
| `--no-color` | `NO_COLOR=1` | `False` | Strip all ANSI escape sequences |
| `--no-anim` | `OCTOFLOW_ANIM=0` | `False` | Disable continuous 20 FPS refresh |
| `--ascii` | `OCTOFLOW_ASCII=1` | `False` | Force strictly 7-bit ASCII (< 128) characters |
| `--plain` | `OCTOFLOW_PLAIN=1` | `False` | Plain line-by-line arm progress events |
| `--quiet`, `-q` | - | `False` | Suppress progress lines |
| `--json` | - | `False` | Emit final mission outcome as structured JSON |
| `--legacy-glyphs` | `OCTOFLOW_LEGACY_GLYPHS=1` | `False` | Restore previous heavy glyphs for one release cycle |

---

## Developer Policy

When authoring terminal output in OctoFlow:
1. **Never use raw emojis** (`⚡`, `🐙`, `🔥`, etc.) in terminal-facing strings.
2. **Import symbols exclusively from `octoflow.glyphs`**:
   ```python
   from octoflow.glyphs import glyph
   console.print(f"{glyph('OK')} Done")
   ```
3. Use `markup=False` when printing user-supplied text or square bracket identifiers `[arm ...]` to prevent Rich BBCode tag stripping.
4. Run regression audits before submitting:
   ```bash
   pytest tests/test_glyph_policy.py tests/test_plain_mode.py
   ```
