"""OctoFlow Dedicated Cockpit Package.

Modularized interactive cephalopod terminal cockpit TUI:
- input: non-blocking 20 FPS keyboard polling, bracketed paste detection, clean terminal restoration
- render: HUD panels, ring topology, frame composition, 3D banner animations
- session: encapsulates mutable session state without module-level globals
- shell: shell route execution, in-process cd navigation, non-blocking confirmation
- app: main interactive cockpit REPL loop
"""

from octoflow.cockpit.app import (
    interactive_cockpit,
    run_cockpit,
)
from octoflow.cockpit.input import (
    CockpitInput,
    clean_bracketed_paste,
    get_live_cockpit_input,
    get_live_cockpit_keys,
    get_live_wizard_input,
    get_live_wizard_keys,
    raw_terminal_mode,
    restore_terminal_mode,
)
from octoflow.cockpit.render import (
    build_cockpit_grid,
    build_confirm_grid,
    build_hud_panel,
    build_prompt_text,
    build_topology_text,
    print_welcome,
    print_welcome_banner,
)
from octoflow.cockpit.session import CockpitSession
from octoflow.cockpit.shell import (
    confirm_live_cockpit,
    execute_cockpit_shell,
)

__all__ = [
    "CockpitSession",
    "CockpitInput",
    "clean_bracketed_paste",
    "raw_terminal_mode",
    "restore_terminal_mode",
    "get_live_cockpit_input",
    "get_live_cockpit_keys",
    "get_live_wizard_input",
    "get_live_wizard_keys",
    "build_hud_panel",
    "build_topology_text",
    "build_prompt_text",
    "build_cockpit_grid",
    "build_confirm_grid",
    "print_welcome_banner",
    "print_welcome",
    "confirm_live_cockpit",
    "execute_cockpit_shell",
    "run_cockpit",
    "interactive_cockpit",
]
