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

---

## 3D Visualizer Accessibility (WCAG 2.2 AA)

OctoFlow's neural 3D visualizer (`visualizer/`) delivers an interactive 3D constellation while guaranteeing full compliance with **WCAG 2.2 AA** guidelines across motion sensitivity, non-visual access, color perception, audio consent, and keyboard navigability.

### 1. Motion Reduction & Sensitivity (`prefers-reduced-motion`)

- **System Preference Detection**: Automatically detects OS-level `prefers-reduced-motion: reduce` on startup via `MotionPolicy`.
- **Manual HUD Toggle**: A persistent button (`#btn-toggle-reduced-motion`) in the top HUD allows toggling reduced motion at any time. State is safely persisted in `localStorage["octoflow_reduced_motion"]`.
- **Motion Suppression Behaviors**:
  - **Camera Transitions**: Instantaneous cuts to target coordinates instead of interpolated lerp/tween animations.
  - **Particle Systems**: Signal propagator bursts, sparks, and ring packets are suppressed while preserving logical message steps.
  - **Orbital Mechanics**: Constellation orbital rotation and mantle breathing animations are deactivated.
  - **Static Highlights**: Node highlights use solid rings rather than oscillating pulse animations.

### 2. Audio & Speech Opt-In Policy

- **Default Silent (OFF)**: Audio synthesis (`SpeechSynthesizer`) is initialized with `isMuted = true` by default. Under no circumstances will speech or sound trigger without prior user action.
- **Explicit HUD Control**: A toggle button (`#btn-toggle-voice`) in the HUD reflects `VOICE: OFF` / `VOICE: ON`.
- **Persistence & Cancellation**: User preference is stored in `localStorage["octoflow_voice_muted"]`. Toggling to mute immediately cancels all active and pending speech synthesis utterances via `window.speechSynthesis.cancel()`.

### 3. Non-Visual Alternative & Live Semantic Feed

For screen reader users and text-only workflows:
- **ARIA Live Activity Region**: An accessible log container with `role="log"` and `aria-live="polite"` announces telemetry events.
- **Announcement Rate Limiting**: Event speech announcements are strictly rate-limited to at most 1 announcement per second with queuing/batching to prevent screen reader audio buffer flooding.
- **Semantic HTML Overview Table**: A comprehensive table (`.arm-status-table`) renders complete arm metadata (`<caption>`, `<th>`, `<td>`), updating in real time:
  - Arm identifier and human-readable role.
  - Current cognitive state (`IDLE`, `REFLEX`, `PLANNING`, `EXECUTING`, `ESCALATE`).
  - Active tool, command, and file target.
  - Free energy and entropy delta ($dS$ vs $\theta$).
- **Toggleable Panel**: The activity log panel (`#activity-log-panel`) can be toggled via the HUD button or keyboard shortcut `L`.

### 4. Non-Reliance on Color Alone (Visual Redundancy)

To support users with color vision deficiencies (protanopia, deuteranopia, tritanopia, achromatopsia), every arm is differentiated through three orthogonal channels:
1. **Color Hue**: Distinct high-contrast palette token.
2. **Short 2-3 Letter Code**: Square-bracketed mnemonic code.
3. **Geometric Symbol**: Unique Unicode geometric shape.

| Arm Index | Name | Code | Symbol | Primary Hue | Hex Code | Contrast Ratio |
|:---:|:---|:---:|:---:|:---|:---:|:---:|
| 0 | ARCHITECT | `[ARC]` | `○` (Circle) | Cyan | `#89dceb` | 13.06:1 |
| 1 | DATABASE | `[DB]` | `□` (Square) | Purple | `#cba6f7` | 9.07:1 |
| 2 | BACKEND | `[BE]` | `△` (Triangle) | Blue | `#89b4fa` | 9.21:1 |
| 3 | FRONTEND | `[FE]` | `◇` (Diamond) | Magenta | `#f5c2e7` | 12.30:1 |
| 4 | COGNITIVE | `[COG]` | `⬡` (Hexagon) | Emerald | `#a6e3a1` | 13.56:1 |
| 5 | SECURITY | `[SEC]` | `▽` (Inverted Triangle) | Red | `#f38ba8` | 7.91:1 |
| 6 | QA_AUDIT | `[QA]` | `☆` (Star) | Amber | `#fab387` | 10.74:1 |
| 7 | DEVOPS | `[OPS]` | `+` (Cross) | Gold | `#f9e2af` | 14.73:1 |

Every 3D label, HUD card, log line, and table row renders with this combined format: `○ [ARC] ARCHITECT`.

### 5. WebGL Fallback & Context Loss Recovery

- **Capability Detection**: Prior to initializing Three.js, `checkWebGLSupport()` inspects WebGL 1.0 / 2.0 availability.
- **Context Loss Handling**: Listens for the `webglcontextlost` event on the canvas.
- **Fallback Banner**: If WebGL is unavailable or lost, a prominent alert (`#webgl-fallback-banner`) appears at the top of the interface:
  > **Notice**: 3D Hardware Acceleration is unavailable. The visualizer has switched to the text-based real-time telemetry view.
- **Automatic Panel Display**: The text activity log and arm status table automatically open in fallback mode.
- **Canvas ARIA Label**: The canvas element is annotated with `role="img"` and `aria-label="OctoFlow Constellation 3D Neural View"`, supplemented by a hidden live region (`#canvas-live-summary`) announcing overall swarm status changes.

### 6. Color Contrast Validation

All interface elements satisfy or exceed WCAG 2.2 AA contrast requirements:
- **Normal Text ($\ge 4.5:1$)**:
  - `--text-light` (`#cdd6f4`) on background: **12.44:1**
  - `--text-muted` (`#787c95`) on background: **4.78:1**
- **UI Components & Borders ($\ge 3.0:1$)**:
  - `--text-dim` (`#5e627c`) on background: **3.28:1**
  - Interactive element borders meet or exceed **3.0:1**.
- **Automated Validation**: Automated contrast verification is runnable via `npm run contrast` or `node scripts/check_contrast.mjs`.

---

## Visualizer Keyboard Navigation & Accessibility Walkthrough Checklist

Use the following checklist to verify complete keyboard accessibility across all visualizer features:

- [ ] **Tab Order Flow**: Pressing `Tab` cycles logically through top controls:
  1. `[REDUCE MOTION: OFF/ON]` (`#btn-toggle-reduced-motion`)
  2. `[VOICE: OFF/ON]` (`#btn-toggle-voice`)
  3. `[ACTIVITY LOG]` (`#btn-toggle-activity-log`)
  4. Interactive arm HUD cards (Arms 0–7)
  5. Activity drawer close button (`#btn-close-activity-log`)
- [ ] **Visible Focus Rings**: All interactive controls display a prominent 2px cyan focus ring (`outline: 2px solid var(--accent-cyan); outline-offset: 2px;`) when focused via keyboard (`:focus-visible`).
- [ ] **Activation**: Pressing `Enter` or `Space` toggles buttons, checkboxes, and opens details.
- [ ] **Shortcut `L`**: Pressing `L` toggles the non-visual Activity Log and Arm Overview Table panel from anywhere in the app.
- [ ] **Shortcut `Escape`**: Pressing `Escape` closes the open Activity Log panel and returns focus cleanly.
- [ ] **Screen Reader Verification**: Screen reader announces "OctoFlow Constellation 3D Neural View" for the canvas, and polite batched announcements for arm activity without speech stutter or lag.


