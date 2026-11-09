# OctoFlow 3D Connectome Visualizer Capture Guide

This guide documents how to replay recorded swarm missions in the 3D WebGL Connectome Visualizer and capture high-fidelity 20-second screen recordings or still frames for release announcements, README showcases, and conference presentations.

---

## 1. Quick Replay Setup

OctoFlow stores complete synaptic telemetry in `~/.octoflow/runs/<run_id>/trace.jsonl` (or canonical fixtures under `tests/characterization/golden/`).

### Launch Replay via CLI
To launch the visualizer in replay mode with live telemetry:

```bash
# 1. Start the visualizer server
octoflow ui --port 8088

# 2. In another terminal, replay a canonical mission (e.g. Rate Limiter or Resume Analyzer):
octoflow replay tests/characterization/golden/replay_canonical_rate_limiter.jsonl --speed 1.5
```

Alternatively, open [`http://localhost:8088`](http://localhost:8088) in any modern Chromium- or WebKit-based browser (Chrome, Edge, Safari, Arc).

---

## 2. Recommended Screen Recording Settings

| Parameter | Recommended Specification |
| :--- | :--- |
| **Tool** | macOS QuickTime (`Cmd + Shift + 5`) or OBS Studio |
| **Resolution** | 1920x1080 (1080p) or 1280x720 (720p) |
| **Aspect Ratio** | 16:9 |
| **Target Duration**| **20 seconds** (optimal for GitHub README & social preview) |
| **Framerate** | 60 fps (or 30 fps for compact GIF export) |
| **Theme** | Abyssal (`#0b0b12` background, cyan `#00F0FF` / amber `#F59E0B` synapses) |

---

## 3. Four Key Choreographed Frames for Video / Stills

### Frame 1: Orbiting Connectome Quiescence (00:00 - 00:04)
- **Visual**: Cephalopod central soma pulsating gently at origin; 8 specialist arms positioned radially in dark space with inactive synaptic filaments.
- **Camera**: Slow 45-degree isometric orbit.
- **Key Message**: Local-first idle architecture consuming zero CPU.

### Frame 2: Objective Pulse & Ganglia Propagation (00:05 - 00:10)
- **Visual**: Conductor emits action potential wave across dorsal cord. Arm 0 (Architect) and Arm 2 (Backend) light up with bright cyan particles.
- **Camera**: Zoom in toward Arm 2 as code generation begins.
- **Key Message**: Dynamic neural attention routing.

### Frame 3: Sensory Surprise Gate & Silence Trigger (00:11 - 00:16)
- **Visual**: Arm 5 (QA) runs unit tests. Sensory surprise gauge ($\Delta S$) flashes amber ($0.65 > \theta$), then drops to low green ($0.08 \le \theta$) as tests pass cleanly. Arm transitions into translucent cyan quiescence (silent execution).
- **HUD**: Activity drawer (`L` shortcut) updates live showing token avoidance metric.
- **Key Message**: Event-triggered sensory surprise gating saves 35% tokens.

### Frame 4: Mission Quiescence & Token Receipt (00:17 - 00:20)
- **Visual**: All 8 arms achieve synchronized quiescence. HUD slides in Truthful Token Receipt showing exact measured tokens spent (3,118) and avoided (1,682).
- **HUD**: Final verdict badge: `✔ COMPLETED (100% PASS)`.
- **Key Message**: Truthful, verifiable token accounting.

---

## 4. Visualizer Keyboard Shortcuts During Capture

- `Space`: Pause / Resume telemetry timeline playback.
- `L`: Open / close accessible activity feed and HUD metrics drawer.
- `1` through `8`: Instantly snap camera focus to specific specialist arms (e.g., `2` for Backend, `5` for QA).
- `R`: Reset camera to global isometric constellation overview.
- `Esc`: Close modal inspectors and open panels.

---

## 5. Converting Video to Web-Optimized GIF / MP4

Once recorded, convert the video to a web-optimized MP4 or GIF using `ffmpeg`:

```bash
# Convert to compressed web-friendly MP4 (h264)
ffmpeg -i visualizer_capture.mov -c:v libx264 -pix_fmt yuv420p -crf 22 -preset slow -an docs/assets/visualizer_demo.mp4

# Convert to high-quality animated GIF (using custom color palette)
ffmpeg -i visualizer_capture.mov -vf "fps=15,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" -loop 0 docs/assets/visualizer_demo.gif
```
