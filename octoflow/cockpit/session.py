"""Cockpit Session State Management.

Maintains mutable state for the interactive cephalopod cockpit:
active workspace, theme, model selection, budget, port, and history.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING
from octoflow.themes import OctoTheme, load_saved_theme

if TYPE_CHECKING:
    from octoflow.server import TelemetryBroadcaster

Theme = OctoTheme


@dataclass
class CockpitSession:
    """Encapsulates all interactive session state without module-level globals."""
    workspace: Path = field(default_factory=lambda: Path.cwd().resolve())
    previous_workspace: Optional[Path] = None
    theme: OctoTheme = field(default_factory=load_saved_theme)
    current_model: str = "anthropic"
    current_octos: str = "auto"
    current_guild: str = "software_dev"
    current_budget: float = 10.00
    host: str = "127.0.0.1"
    port: int = 8088
    visualizer_url: str = "http://localhost:8088"
    broadcaster: Optional["TelemetryBroadcaster"] = None
    running: bool = True
    active_run: Optional[Any] = None
    history: List[str] = field(default_factory=list)
