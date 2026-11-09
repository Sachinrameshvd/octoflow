# Tutorial 7: Watching a Run in the 3D Connectome Visualizer

**Estimated Duration:** 6 minutes  
**Verification:** Verified on 2026-11-09, OctoFlow v0.2.0  

This tutorial demonstrates how to launch OctoFlow's real-time WebGL 3D Benthic Connectome, observe synaptic transmission between specialist arms, and replay past missions.

---

## What is the 3D Visualizer?

OctoFlow includes an offline, browser-based WebGL interface powered by Three.js. It visualizes:
- The central Supraesophageal Ganglion and 8 peripheral brachial arm nodes.
- Real-time sensory surprise meters ($\Delta S_i$ vs. $\theta$) animating reflex vs. escalation states.
- Synaptic particle flows representing neurotransmitters (ACh, GABA, Glutamate).
- Dynamic coalition binding linking collaborative arms.

---

## Step 1: Start the Local Telemetry Bridge

Launch the visualizer bridge directly from the command line:

```bash
octoflow ui
```

### Expected Output

```text
◈ OctoFlow 3D Benthic Connectome Bridge v1.0.0
• Local WebSocket Server: ws://127.0.0.1:8088/ws/telemetry
• Web Visualizer URL: http://127.0.0.1:8088

Opening WebGL Connectome in your default browser...
Press Ctrl+C to terminate the bridge.
```

The browser automatically opens to `http://127.0.0.1:8088`.

---

## Step 2: Run a Swarm Mission in Parallel

In a second terminal window, run a swarm mission:

```bash
octoflow run "Build a thread-safe token bucket rate limiter" --dry-run
```

Watch the 3D constellation in your browser:
- Arm nodes illuminate as actions dispatch.
- When an arm enters a local reflex ($\Delta S_i \le \theta$), green pulse waves circle the arm ganglion.
- When an arm escalates to the central brain ($\Delta S_i > \theta$), bright particle packets shoot inward toward the central ganglion.

---

## Step 3: Keyboard Shortcuts in the Visualizer

With the browser window focused:
- `1` through `8`: Focus camera on Arm 0 through Arm 7.
- `Space`: Pause / resume synaptic particle animation.
- `C`: Reset camera to orbital constellation view.
- `T`: Start an interactive anatomical tour.
- `?` or `M`: Open the developer field manual drawer.

---

## Step 4: Replaying a Historical Run

You can replay any past mission into the 3D visualizer at variable speeds using `octoflow replay`:

```bash
# Replay run at 2x speed while broadcasting to the visualizer
octoflow replay run-1794149809 --speed 2.0
```

To replay headlessly in the terminal without broadcasting over WebSockets:
```bash
octoflow replay run-1794149809 --no-visualizer
```

---

## Step 5: Contributor Inner-Loop Stack (`make dev`)

For contributors modifying the visualizer TypeScript code (`visualizer/`):

```bash
# Start both Python telemetry server and Vite dev server with hot reload
make dev

# Cleanly stop both servers
make dev-stop
```

---

## Next Steps

- Learn how to run the algorithmic benchmark suite: [Tutorial 8: Running Benchmarks](08-running-benchmarks.md)
- Complete debugging and replay field guide: [docs/debugging.md](../debugging.md)

