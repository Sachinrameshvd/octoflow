# Add Interactive Keyboard Shortcut Help Overlay to 3D Connectome Visualizer

**Difficulty:** Intermediate  
**Labels:** `visualizer`, `enhancement`  
**Mentoring Pointer:** Check out [`visualizer/src/main.ts`](../../visualizer/src/main.ts) and [`visualizer/src/ui/hud.ts`](../../visualizer/src/) to see how HUD panels and modals are mounted.

---

## Context
OctoFlow's 3D Connectome Visualizer features rich camera controls, orbital views, arm focus triggers, and stimulus injection shortcuts.

However, users currently have to remember keybindings (e.g. `1`-`8` to focus arms, `0` for central brain, `Space` to pause signal cascade, `M` to open manual) or consult documentation. An interactive modal overlay displaying all keyboard shortcuts will dramatically improve discoverability and accessibility.

---

## Objectives & Requirements
1. In the WebGL visualizer frontend source, add an accessible modal container `#shortcuts-modal` in `visualizer/index.html` or dynamically created in `visualizer/src/ui/hud.ts`.
2. Bind the `?` and `h` keys to toggle the shortcuts modal.
3. List all visualizer hotkeys clearly in a clean table:
   - `0`: Focus on Central Supraesophageal Brain
   - `1` - `8`: Focus on Specialist Brachial Arm 1 through 8
   - `C`: Orbiting Constellation View
   - `Space`: Pause / Resume live signal propagation
   - `M`: Open Cephalopod Master Manual
   - `Esc`: Close open modal / Deselect active arm
4. Style the modal to match OctoFlow's high-contrast dark cyberpunk theme with single-width glyphs.
5. Close the modal on `Esc` or clicking outside the container.
6. Run `bash scripts/sync_visualizer.sh` and verify tests.

---

## Files to Touch
- `visualizer/src/ui/hud.ts`: Implement keyboard listener and toggle logic.
- `visualizer/src/main.ts`: Wire shortcut listener.
- `visualizer/index.html`: Add semantic modal structure with `role="dialog"` and `aria-label`.
- `tests/test_visualizer_accessibility.py`: Add test asserting presence of the modal in distribution.

---

## Acceptance Criteria
- [ ] Pressing `?` or `h` in the visualizer opens the shortcut help modal.
- [ ] Pressing `Esc` or clicking close dismisses the modal.
- [ ] Accessible semantics (`role="dialog"`, `aria-modal="true"`) pass accessibility audits.
- [ ] Running `cd visualizer && npm test` and `npm run build` succeeds.
- [ ] `bash scripts/sync_visualizer.sh` syncs cleanly to `octoflow/dist`.

