"""OctoFlow Terminal Cast & Session Recorder.

Records terminal cockpit interactions into standard Asciinema v2 (.cast) files
for sharing in GitHub pull requests, READMEs, and team documentation.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class TerminalRecorder:
    """Asciinema v2 format terminal session recorder."""

    def __init__(self, width: int = 120, height: int = 36, title: str = "OctoFlow Swarm Session"):
        self.width = width
        self.height = height
        self.title = title
        self.start_time: Optional[float] = None
        self.events: List[List[Any]] = []
        self.is_recording = False

    def start(self) -> None:
        """Start recording session timestamps."""
        self.start_time = time.time()
        self.events = []
        self.is_recording = True

    def record_output(self, text: str) -> None:
        """Record standard output text chunk."""
        if not self.is_recording or self.start_time is None:
            return
        elapsed = round(time.time() - self.start_time, 3)
        self.events.append([elapsed, "o", text])

    def record_input(self, text: str) -> None:
        """Record user input keystrokes."""
        if not self.is_recording or self.start_time is None:
            return
        elapsed = round(time.time() - self.start_time, 3)
        self.events.append([elapsed, "i", text])

    def stop(self) -> None:
        """Stop active recording."""
        self.is_recording = False

    def export_cast(self, output_path: str) -> Path:
        """Export session to Asciinema v2 format file."""
        out_p = Path(output_path).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)

        header = {
            "version": 2,
            "width": self.width,
            "height": self.height,
            "timestamp": int(self.start_time or time.time()),
            "title": self.title,
            "env": {"TERM": "xterm-256color", "SHELL": "octos"},
        }

        lines = [json.dumps(header)]
        for evt in self.events:
            lines.append(json.dumps(evt))

        out_p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return out_p


_GLOBAL_RECORDER: Optional[TerminalRecorder] = None


def get_global_recorder() -> TerminalRecorder:
    """Retrieve or initialize singleton session recorder."""
    global _GLOBAL_RECORDER
    if _GLOBAL_RECORDER is None:
        _GLOBAL_RECORDER = TerminalRecorder()
    return _GLOBAL_RECORDER
