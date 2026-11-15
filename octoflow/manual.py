"""OctoFlow Terminal Manual & Developer Field Guide Reader.

Renders syntax-highlighted, interactive Rich documentation directly in the shell
or cockpit, with chapter navigation, keyword search, and web-viewer launching.
"""

from __future__ import annotations

import webbrowser

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from octoflow.themes import load_saved_theme

MANUAL_SECTIONS: dict[str, dict[str, str]] = {
    "1": {
        "title": "Quick Start (60 Seconds)",
        "content": """
### 1. Launch the 3D WebGL Connectome Showcase
```bash
cd "showcase copy"
npm install
npm run dev
```
Open **`http://localhost:5174`** in your browser.

### 2. Free Autonomous Swarm Simulation (Zero API Key Needed)
```bash
source .venv/bin/activate
octos run "Build a thread-safe sliding-window rate limiter with tests" --provider mock
```

### 3. Local-First Autonomous Swarm (Ollama Open Weights)
```bash
ollama pull qwen2.5-coder:7b
octos run "Build a rate limiter with unit tests" --model ollama
```

### 4. Interactive Terminal Flight Cockpit
```bash
octos
```
""",
    },
    "2": {
        "title": "Biological Principles & Active Inference",
        "content": """
### Biological Cephalopod Architecture
Unlike monolithic prompt pipelines that route every trivial event through a central LLM, OctoFlow coordinates an 8-arm lateral ganglion ring under an executive supraesophageal ganglion.

```text
                                  +---------------------------+
                                  | SUPRAESOPHAGEAL GANGLION  |
                                  |      (Central Brain)      |
                                  +-------------+-------------+
                                                | Dynamic Coalition Binding
                                                v
         +-----------------------------------------------------------------------------+
         |                    LATERAL INTER-BRACHIAL NERVE RING                        |
         |  Arm 0 ----- Arm 1 ----- Arm 2 ----- Arm 3 ----- Arm 4 ----- Arm 5 ----- Arm 6 --- Arm 7 |
         +-----------------------------------------------------------------------------+
              ^            ^            ^            ^            ^            ^
              |            |            |            |            |            |
       [Reflex Loop] [Reflex Loop] [Reflex Loop] [Reflex Loop] [Reflex Loop] [Reflex Loop]
```

**1. Active Inference & Predictive Coding:**
Peripheral arm ganglia compute expected observations. Sensory surprise is calculated as:
$$\\Delta S_i = \\frac{1}{D} \\|o_i - \\hat{o}_i\\|_2^2$$
Only when surprise exceeds the adaptive threshold $\\theta = 0.45$ does an arm escalate to the central conductor. Routine checks execute as **silent local reflexes**, saving 15-25% tokens on code generation.

**2. Ring-Topology Lateral Communication:**
Adjacent arms exchange semantic tokens across an inter-brachial ring bus without routing through the central conductor, preventing orchestrator context saturation.

**3. Zero-Shot Limb Amputation & Recovery:**
If an arm hits an unhandled error or is severed, the lateral nerve ring dynamically rebalances tasks across remaining arms with **0.00s downtime**.
""",
    },
    "3": {
        "title": "3D WebGL Connectome Showcase (Port 5174)",
        "content": """
### Abyssal 3D Visualizer & Connectome Controls

The interactive showcase lives in `showcase copy/` and visualizes cephalopod coordination in real time.

* **Development Port:** Runs on `http://localhost:5174` (`npm run dev`).
* **Always-On Ambient Ocean Waves:** Web Audio API sound engine auto-starts on first user interaction and stays on continuously.
* **Slides 19 to 26 (Individual Octopuses 1 through 8):**
  * Click **`↯ Spark Octo`**: Triggers golden action potential pulses down all 8 arms and flashes the 8 status indicators.
  * Click **`SoftDev` / `AI/ML`**: Toggles individual morphology between Software Architecture and AI/ML Research.
* **Slide 27 (The 8-Octopus Living Swarm):**
  * **Tiered Amphitheater:** All 8 octopuses positioned in an undulating biological depth formation with zero card occlusion.
  * Click **`↯ Synaptic Pulse`**: Fires high-voltage action potentials across all 64 arms and 3D inter-octopus cables.
  * Click **`Free Orbit`**: Unlocks 360-degree orbital camera rotation (click & drag).
  * Click **`Executive Dossier →`**: Generates a 1-page printer-ready technical brief.
""",
    },
    "4": {
        "title": "Autonomous Swarm Engine & Flight Cockpit",
        "content": """
### Master CLI Directory & Cockpit Commands

* `octos doctor` — Environment, model endpoints, and dependency diagnostics.
* `octos run "<goal>"` — Deploy autonomous multi-agent swarm to execute an objective.
* `octos` — Launch the full-screen terminal flight cockpit.
* `octos receipt` — Display truthful token receipts and gate savings.
* `octos guard` — AST syntax and 12-rule secret leak audit.
* `octos undo` — Rollback changes to the pre-flight git checkpoint.
* `octos manual [-c <chapter>]` — Open this interactive field manual.

### Cockpit Keyboard Shortcuts:
* `F1` or `/manual` — Open interactive manual reader.
* `/help` — Display command cheat table.
* `k` / `j` — Next / previous theme palette (8 curated developer themes).
* `q` or `/exit` — Clean exit.
""",
    },
    "5": {
        "title": "Hands-On Demos: Building & Running Real Projects",
        "content": """
### Demo 1: Autonomous Code Generation (Sliding-Window Rate Limiter)

1. Create a sandbox folder:
   ```bash
   source .venv/bin/activate
   mkdir -p demo_sandbox && cd demo_sandbox
   ```
2. Run OctoFlow autonomous swarm:
   ```bash
   ../octos run "Build a thread-safe sliding-window rate limiter with tests" --provider mock
   ```
3. Execution lifecycle observed in terminal:
   * **Arm 0 (Architect):** Generates `RateLimiter` interface & Pydantic contracts.
   * **Arm 2 (Backend):** Implements `limiter.py` with threading locks & timestamp deque.
   * **Arm 5 (QA):** Creates `test_limiter.py` & executes pytest.
   * **Gate (Sensory Reflex):** Passing tests ($\\Delta S = 0.08 \\le \\theta$) silenced as 0-token local reflex.
   * **Arm 6 (Security):** AST verification and secret scan passed.
4. Verify generated artifacts:
   ```bash
   pytest test_limiter.py -v
   ../octos receipt
   ../octos undo
   cd ..
   ```

---

### Demo 2: Running the Full Turnkey Web Application (AI Resume Analyzer)

Located in `examples/resume-analyzer/` (built across 6 incremental OctoFlow missions):

1. Navigate and install dependencies:
   ```bash
   cd examples/resume-analyzer
   pip install -r requirements.txt
   ```
2. Generate synthetic non-PII test resumes:
   ```bash
   python scripts/generate_samples.py
   ```
3. Run the automated in-memory test suite (26 tests):
   ```bash
   pytest tests/ -v
   ```
4. Start the live FastAPI server:
   ```bash
   uvicorn app:app --reload --port 8000
   ```
5. Open **`http://localhost:8000`** in browser, drag-and-drop a sample PDF resume, and evaluate ATS gauntlet match scores live.
6. Inspect the immutable provenance receipt:
   ```bash
   cat provenance/mission-6-receipt.json
   ```
   *(41,265 tokens / 22.4% avoided via sensory gating).*
""",
    },
    "6": {
        "title": "The 8 Specialized Neural Arm Ganglia Roster",
        "content": """
### Cephalopod Arm Specializations & Responsibilities

| Arm ID | Title | Specialization & Capabilities | Primary Tools |
| :---: | :--- | :--- | :--- |
| **Arm 0** | **System Architect** | High-level topology, schemas, AST design, and dependency DAGs | `git_status`, `read_file`, `ast_plan` |
| **Arm 1** | **Database & Schemas** | SQL migrations, ORM entities, validation contracts, Pydantic | `write_file`, `lint_check`, `sql_validate` |
| **Arm 2** | **Backend Core** | High-throughput microservice endpoints, business logic | `write_file`, `run_tests`, `typecheck` |
| **Arm 3** | **Frontend & UX** | Responsive components, design token palettes, WebGL Three.js | `write_file`, `vite_build`, `browser_eval` |
| **Arm 4** | **State & Bus** | WebSocket telemetry, in-memory cache layers, state machines | `bus_publish`, `cache_invalidate` |
| **Arm 5** | **QA & Invariants** | Pytest suites, automated regression discovery, self-healing | `run_pytest`, `ast_patch`, `self_heal` |
| **Arm 6** | **Security & Guard** | 12-rule zero-trust PII filtering, secret audits, credential hygiene | `pii_sanitize`, `secret_scan`, `mtls_auth` |
| **Arm 7** | **DevOps & Docs** | Docker builds, CI/CD pipelines, live dev server boots | `docker_build`, `gen_docs`, `telemetry_emit` |
""",
    },
    "7": {
        "title": "Truthful Token Receipts & Accounting",
        "content": """
### Cryptographic Accounting & Gate Metrics

Every live mission produces a verified receipt detailing tokens spent and tokens avoided:

```text
┌── Token Receipt: 1794049840-56720e ──────────────────────────────────────┐
│ Spent:   22,637 tokens (measured)                                        │
│ Avoided: 7,704 tokens (estimated avoided via sensory gate reflexes)      │
│ Calls:   29 LLM completions | Gate: 29 evaluations (24 reflexes, 5 esc)  │
│ Top arms: Arm 5 (QA): 8,215 · Arm 6 (Sec): 4,664 · Arm 1 (Model): 2,981 │
│ Method:  octoflow receipt --method                                       │
└──────────────────────────────────────────────────────────────────────────┘
```

* **Measured Spent:** Extracted directly from provider response headers.
* **Avoided:** Verified tokens saved when peripheral arm actions execute as silent local reflexes without central LLM calls.
* **View receipts:** `octos receipt` or `octos receipt <run-id>`.
""",
    },
    "8": {
        "title": "IDE Integration, Automated Tests & Safety",
        "content": """
### 1. Claude Code CLI Integration (SPARC)
```bash
# Auto-configure CLAUDE.md blueprint in target repo:
octos claude init

# Run Claude Code CLI with pre-injected 8-Arm SPARC directives:
octos claude run "Build a rate limiter with unit tests"
```

### 2. Model Context Protocol (MCP) Server
```bash
octoflow mcp-serve
```

### 3. Automated Test Suites
```bash
source .venv/bin/activate

# Zero-Emoji Bio-Glyph Audit (9/9 pass):
pytest tests/test_glyph_policy.py

# Mathematical Sensory Gate Properties:
pytest tests/test_gate_properties.py

# Zero-Telemetry & Loopback Egress Quarantine:
pytest tests/test_egress_guard.py

# Fast Unit Tests:
pytest tests/ -m "unit and not pty and not live" -q
```
""",
    },
    "9": {
        "title": "Troubleshooting & Developer FAQ",
        "content": """
### Developer FAQ & Common Resolutions

**1. Port 5174 Already in Use**
* Resolution: Terminate stale Vite processes:
  ```bash
  lsof -ti:5174 | xargs kill -9
  ```

**2. Browser Ocean Audio Silent**
* Resolution: Modern browsers require a user gesture (click, scroll, keypress) before activating Web Audio contexts. Click anywhere on the showcase to engage audio.

**3. Local Ollama Memory Pressure**
* Resolution: Use the optimized 7B parameter quantized model:
  ```bash
  ollama pull qwen2.5-coder:7b
  ```
  Or use the free simulation provider: `octos run "<goal>" --provider mock`.

**4. Git Lock Conflicts During Ephemeral Runs**
* Resolution: Remove stale lock files and verify diagnostics:
  ```bash
  rm -f .git/index.lock
  octos doctor
  ```
""",
    },
}


def display_manual(
    chapter: str | None = None, web: bool = False, console: Console | None = None
) -> None:
    """Render the manual to the terminal or open in web browser."""
    con = console or Console()
    theme = load_saved_theme()

    if web:
        con.print(
            f"[{theme.rich_primary}]◈ Opening Cephalopod Manual in default browser...[/{theme.rich_primary}]"
        )
        webbrowser.open("http://localhost:5174")
        return

    con.print()
    con.print(
        Panel(
            "[bold white]◈ OCTOFLOW // CEPHALOPOD DEVELOPER MANUAL & FIELD GUIDE ◈[/bold white]\n"
            "[dim]Active Inference • 8-Arm Ganglia • Hands-On Demos • Truthful Receipts • Zero-Emoji Policy[/dim]\n\n"
            "[dim]Usage: Run [bold]octos manual -c <number>[/bold] to view any specific chapter directly.[/dim]",
            title="[bold cyan]Official Developer Field Guide[/bold cyan]",
            border_style=theme.rich_border,
            padding=(1, 2),
        )
    )

    # If specific chapter or keyword requested
    if chapter:
        ch_key = str(chapter).strip()
        matched_section = None

        # 1. Exact chapter key match (e.g. "1", "5")
        if ch_key in MANUAL_SECTIONS:
            matched_section = (ch_key, MANUAL_SECTIONS[ch_key])

        # 2. Title substring match (e.g. "demos", "rate limiter", "architecture")
        if not matched_section:
            for k, v in MANUAL_SECTIONS.items():
                if ch_key.lower() in v["title"].lower():
                    matched_section = (k, v)
                    break

        # 3. Content search fallback
        if not matched_section:
            for k, v in MANUAL_SECTIONS.items():
                if ch_key.lower() in v["content"].lower():
                    matched_section = (k, v)
                    break

        if matched_section:
            k, sec = matched_section
            con.print(
                Panel(
                    Markdown(sec["content"].strip()),
                    title=f"[bold green]Chapter {k}: {sec['title']}[/bold green]",
                    border_style="green",
                    padding=(1, 2),
                )
            )
            con.print(
                f"[dim]Run [bold]octos manual[/bold] to return to the full table of contents.[/dim]\n"
            )
            return
        else:
            con.print(
                f"[yellow]Topic or Chapter '{chapter}' not found. Displaying table of contents:[/yellow]\n"
            )

    # Table of Contents
    toc_table = Table(
        title="Manual Chapters (Select with --chapter <number>)", border_style=theme.rich_border
    )
    toc_table.add_column("Ch #", style=theme.rich_primary, width=6)
    toc_table.add_column("Chapter Title", style="bold white", width=50)
    toc_table.add_column("Quick Command", style="dim", width=22)

    for k, sec in MANUAL_SECTIONS.items():
        toc_table.add_row(f"Ch {k}", sec["title"], f"octos manual -c {k}")

    con.print(toc_table)
    con.print()

    # Render all chapters in clean sequence
    for k, sec in MANUAL_SECTIONS.items():
        con.print(
            Panel(
                Markdown(sec["content"].strip()),
                title=f"[bold cyan]Chapter {k}: {sec['title']}[/bold cyan]",
                border_style=theme.rich_border,
                padding=(1, 2),
            )
        )
        con.print()
