"""OctoFlow Terminal Manual & Developer Field Guide Reader.

Renders syntax-highlighted, interactive Rich documentation directly in the shell
or cockpit, with chapter navigation, search, and web-viewer launching.
"""

import sys
import webbrowser
from typing import Optional, List, Dict
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

from octoflow.themes import load_saved_theme


MANUAL_SECTIONS: Dict[str, Dict[str, str]] = {
    "1": {
        "title": "Biological Principles & Active Inference",
        "content": """
### Biological Cephalopod Architecture
Unlike monolithic prompt pipelines, OctoFlow coordinates an 8-arm lateral ganglion ring under an executive supraesophageal ganglion.

**1. Active Inference & Predictive Coding:**
Peripheral arm ganglia compute expected observations $\\hat{o}_{t+1}$. Sensory surprise is calculated as:
$$\\Delta S_t = \\frac{1}{D} \\|o_t - \\hat{o}_t\\|_2^2$$
Only when surprise exceeds the adaptive threshold $\\theta$ is an alert propagated up to the orchestrator. This reduces token calls by **>80%**.

**2. Ring-Topology Lateral Communication:**
Adjacent arms exchange semantic tokens across an inter-brachial ring bus without routing through the central conductor, preventing orchestrator context window saturation.

**3. Biophysical Connectomics:**
Biological Dale's Principle enforces strict neurotransmitter identities: Acetylcholine (ACh) for excitation, GABA/Glutamate for inhibition, and Dopamine/Octopamine for neuromodulation.
"""
    },
    "2": {
        "title": "The 8 Specialized Neural Arm Ganglia",
        "content": """
### Cephalopod Arm Specializations
Each arm operates an egocentric sensory patch and specialized tool suite:

* **Arm 0 (System Architect):** High-level topology, schemas, AST design, and dependency DAGs.
* **Arm 1 (Database & Schemas):** SQL migrations, ORM entities, validation contracts, Pydantic/Zod models.
* **Arm 2 (Backend Core):** High-throughput microservice endpoints, business logic, asynchronous tasks.
* **Arm 3 (Frontend & UX):** Responsive components, design token palettes, HTML/CSS layout, Three.js 3D.
* **Arm 4 (State & Reactive Engine):** WebSocket telemetry, in-memory cache layers, state machines.
* **Arm 5 (QA & Invariants):** Pytest/Jest suites, automated regression discovery, AST self-healing loop.
* **Arm 6 (Security & Guard):** 14-rule zero-trust PII filtering, secret audits, credential hygiene.
* **Arm 7 (DevOps & Ignition):** Docker builds, CI/CD pipelines, live dev server boots, and safe rollbacks.
"""
    },
    "3": {
        "title": "Master Command Directory",
        "content": """
### Complete Command Reference

| Command | Action Description | Example |
| :--- | :--- | :--- |
| **`/audit`** | 100-Point system readiness & security audit | `./octo audit` |
| **`/eject`** | Export standalone agent harness into any repository | `./octo eject --output ./harness` |
| **`/install-claude`** | Register Claude Code plugin manifest & slash commands | `./octo install-claude` |
| **`/federation`** | Zero-trust 14-rule PII filter & peer trust scoring | `./octo federation status` |
| **`/heal`** | Autonomous test failure triage and self-healing | `./octo heal` |
| **`/triage`** | Interactive AST-level patch inspector | `./octo triage` |
| **`/theme`** | Interactive palette selector (8 developer themes) | `./octo theme catppuccin` |
| **`/bench`** | Algorithmic benchmark challenge suite | `./octo bench --task lru_cache` |
| **`/plan`** | Preview 8-arm task allocation blueprint | `./octo plan "build auth"` |
| **`/ui`** | Open 3D WebGL Constellation in browser | `./octos ui` |
| **`/runner`** | Launch 8-bit benthic dot-matrix runner | `./octo runner` |
| **`/doctor`** | Comprehensive environment diagnostics | `./octo doctor` |
"""
    },
    "4": {
        "title": "Step-by-Step Developer Playbooks",
        "content": """
### Developer Playbooks

**Playbook A: Building a Fullstack Feature from Scratch**
1. Launch cockpit: `./octo`
2. Preview allocation: `/plan Build user authentication with JWT and bcrypt`
3. Execute mission: Enter prompt in cockpit; watch 8 arms coordinate in real time.
4. Launch dev server: `/ignite`

**Playbook B: Fixing Broken Unit Tests (`/heal`)**
1. Run `./octo heal`
2. Arm 5 runs test suites, catches errors, and pinpoints root-cause AST nodes.
3. Arm 2 writes surgical code repairs.
4. Arm 5 re-runs tests to verify convergence.

**Playbook C: Ejecting Standalone Agent Toolkit**
1. Run `./octo eject --output ./my-agent-kit`
2. Commit the zero-dependency files into your project.
3. Run directly: `python ./my-agent-kit/run.py "Deploy microservice"`
"""
    },
    "5": {
        "title": "Zero-Trust Federation & 14-Rule PII Redaction",
        "content": """
### PII & Secret Redaction Pipeline
All inter-arm, inter-octopus, and cross-machine transmissions are automatically scrubbed:

* **OpenAI / Anthropic Keys:** `sk-...` / `sk-ant-...` -> `[REDACTED_KEY]`
* **GitHub Tokens:** `ghp_...` -> `[REDACTED_GITHUB_TOKEN]`
* **AWS Keys:** `AKIA...` & `aws_secret_access_key` -> `[REDACTED_AWS_KEY]`
* **Stripe & Google Tokens:** `sk_live_...` & `AIza...` -> `[REDACTED_TOKEN]`
* **Private Keys:** `-----BEGIN PRIVATE KEY-----` -> `[REDACTED_KEY_BLOCK]`
* **Credentials & Passwords:** `password=...` -> `[REDACTED_SECRET]`
* **PII Identifiers:** Emails, IPv4 addresses, Credit card numbers -> `[REDACTED_PII]`

Action modes available: `REDACT` (default), `BLOCK` (raises PermissionError), `HASH`, `PASS`.
"""
    },
    "6": {
        "title": "Keyboard Shortcuts Cheatsheet",
        "content": """
### Interactive Controls

**In 3D WebGL Visualizer:**
* **`?` or `m`:** Open / Close Master Developer Manual Drawer
* **`1` - `8`:** Direct camera focus on Arm 0 through Arm 7
* **`Space`:** Pause / Resume synaptic transmission animation
* **`C`:** Reset camera to orbital constellation view
* **`T`:** Start interactive guided architectural tour
* **`V`:** Toggle voice synthesis audio

**In Terminal Cockpit:**
* **`/manual`:** Open interactive manual reader
* **`F1` / `/help`:** Display quick command help table
* **`k` / `j`:** Previous / Next theme in palette picker
* **`/exit` / `q`:** Exit cleanly
"""
    }
}


def display_manual(chapter: Optional[str] = None, web: bool = False, console: Optional[Console] = None) -> None:
    """Render the manual to the terminal or open in web browser."""
    con = console or Console()
    theme = load_saved_theme()

    if web:
        con.print(f"[{theme.rich_primary}]◈ Opening Cephalopod Manual in default browser...[/{theme.rich_primary}]")
        webbrowser.open("http://localhost:8088?manual=1")
        return

    con.print()
    con.print(Panel(
        "[bold white]🐙 OCTOFLOW CEPHALOPOD DEVELOPER MANUAL & FIELD GUIDE[/bold white]\n"
        "[dim]Biological Active Inference • 8 Arm Ganglia • Master Commands • Playbooks • Zero-Trust PII[/dim]\n\n"
        "[dim]Shortcut: Press [bold]? [/bold] in the 3D Web Visualizer or run [bold]./octo manual[/bold] anytime.[/dim]",
        title="[bold cyan]Official Documentation[/bold cyan]",
        border_style=theme.rich_border,
        padding=(1, 2)
    ))

    # If specific chapter requested
    if chapter:
        ch_key = str(chapter).strip()
        matched_section = None
        for k, v in MANUAL_SECTIONS.items():
            if ch_key == k or ch_key.lower() in v["title"].lower():
                matched_section = (k, v)
                break
        
        if matched_section:
            k, sec = matched_section
            con.print(Panel(
                Markdown(sec["content"].strip()),
                title=f"[bold green]Chapter {k}: {sec['title']}[/bold green]",
                border_style="green",
                padding=(1, 2)
            ))
            return
        else:
            con.print(f"[yellow]Chapter '{chapter}' not found. Displaying table of contents:[/yellow]\n")

    # Table of Contents
    toc_table = Table(title="Manual Chapters (Select with --chapter <number>)", border_style=theme.rich_border)
    toc_table.add_column("Ch #", style=theme.rich_primary, width=6)
    toc_table.add_column("Chapter Title", style="bold white", width=46)
    toc_table.add_column("Quick Command", style="dim", width=24)

    for k, sec in MANUAL_SECTIONS.items():
        toc_table.add_row(f"Ch {k}", sec["title"], f"./octo manual -c {k}")

    con.print(toc_table)
    con.print()

    # Render all chapters in clean accordion sequence
    for k, sec in MANUAL_SECTIONS.items():
        con.print(Panel(
            Markdown(sec["content"].strip()),
            title=f"[bold cyan]Chapter {k}: {sec['title']}[/bold cyan]",
            border_style=theme.rich_border,
            padding=(1, 2)
        ))
        con.print()
