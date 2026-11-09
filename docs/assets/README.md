# OctoFlow Media & Launch Assets

This directory contains public demonstration casts, screen recording guides, and social preview specifications for OctoFlow releases.

---

## 1. Quickstart Demo Cast (`demo.cast`)

The primary terminal demonstration is stored in [`demo.cast`](demo.cast) using the standard [Asciinema v2 format](https://docs.asciinema.org/manual/cli/format/v2/).

### Playback in Terminal
You can inspect and replay the recording directly in your terminal:

```bash
# If asciinema is installed:
asciinema play docs/assets/demo.cast

# Or replay via Python runner:
python scripts/record_demo_session.py
```

### Reproducing the Recording
To regenerate [`demo.cast`](demo.cast) from scratch:

```bash
bash scripts/record_demo.sh
```

### Converting to Animated GIF or SVG
If you have `agg` or `svg-term` installed, `scripts/record_demo.sh` automatically compiles the `.cast` file into `.gif` and `.svg`.

To convert manually:

```bash
# Using agg (Rust Asciinema GIF generator)
brew install agg
agg --theme monokai --speed 1.2 --font-size 14 docs/assets/demo.cast docs/assets/demo.gif

# Using svg-term (SVG animated terminal renderer)
npm install -g svg-term-cli
svg-term --in docs/assets/demo.cast --out docs/assets/demo.svg --window --width 110 --height 32
```

---

## 2. 3D WebGL Connectome Visualizer Capture

For guidelines on capturing 20-second screen recordings or still frames of replayed swarm missions in the browser visualizer, see:
[`docs/assets/VISUALIZER_CAPTURE.md`](VISUALIZER_CAPTURE.md).

---

## 3. Social Preview & Announcement Assets

- **Announcement Drafts**: [`docs/launch/announcement.md`](../launch/announcement.md)
- **Social Preview Image Brief**: Specified in [`docs/launch/announcement.md`](../launch/announcement.md) (1280x640px text-only template).
