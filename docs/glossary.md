# OctoFlow Architecture Glossary

This glossary provides an authoritative cross-reference mapping biological cephalopod concepts to standard software engineering terminology and exact Python code identifiers.

---

## Cephalopod Anatomy to Software Architecture Mapping

| Anatomical Metaphor | Plain Software Term | Exact Code Identifier | Module File | Description & Operational Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Supraesophageal Ganglion** | Central Planner / Swarm Conductor | `SupraesophagealConductor` | `octoflow/conductor.py` | Top-level coordinator that decomposes objectives into DAG tasks, manages goal status, and binds arm coalitions. |
| **Brachial Axial Nerve Cord** | Autonomous Specialist Agent | `ArmAgent` | `octoflow/arm.py` | Peripheral worker agent executing tool loops, local reflex decisions, and file modifications in an assigned domain. |
| **Sensory Surprise Gating** | Change Detector & Reflex Router | `SurpriseGate` | `octoflow/gate.py` | Evaluates predictive observation error ($\Delta S$) against an adaptive threshold ($\theta$) to suppress redundant LLM calls. |
| **Gate Evaluation Record** | Decision Ledger Entry | `GateDecision` | `octoflow/gate.py` | Dataclass recording arm ID, cycle index, $\Delta S$, threshold $\theta$, decision (`reflex` vs `escalate`), and avoided token metrics. |
| **Inter-Brachial Nerve Ring** | Lateral Peer Event Bus | `InterBrachialBus` | `octoflow/bus.py` | Ring-topology lateral message bus enabling low-latency communication between adjacent arms without conductor intervention. |
| **Vertical Lobe (VL)** | Associative Memory & Cache | `VerticalLobeMemory` | `octoflow/memory.py` | Long-term Hebbian memory system storing learned codebase heuristics, successful tool patterns, and syntactic AST structures. |
| **Coalition Binding** | Dynamic Task Force Matrix | `extract_coalitions_from_matrix` | `octoflow/coalition.py` | Matrix factorization extracting temporary multi-arm coalitions (e.g. Architect + Backend + QA) based on cross-attention weights. |
| **Sensory Receptive Field** | Sensory Observation Encoder | `CodeSensoryEncoder` | `octoflow/encoder.py` | Vectorizes discrete execution signals (exit codes, stderr, diff length, latency, error keywords) into continuous 16D observation vectors. |
| **Sensory Surprise ($\Delta S$)** | Mean Squared Prediction Error | `SurpriseGate.compute_surprise` | `octoflow/gate.py` | Normalized error metric $\Delta S_i = \min(1.0, 4 \times \frac{1}{D}\|o_t - \hat{o}_t\|^2)$ measuring divergence from expected tool results. |
| **Adaptive Threshold ($\theta$)** | Escalation Decision Boundary | `SurpriseGate.threshold` | `octoflow/gate.py` | Dynamic cutoff $\theta \in [0.25, 0.90]$; adapts downward on routine reflexes and upward on escalations to prevent panic loops. |
| **Reflex Action** | Silent Local Tool Execution | `GateDecision(decision="reflex")` | `octoflow/gate.py` | Arm executes autonomously without central LLM escalation ($\Delta S \le \theta$), recording avoided prompt tokens. |
| **Sensory Escalation** | Central Attention Delegation | `GateDecision(decision="escalate")` | `octoflow/gate.py` | Arm escalates unexpected errors ($\Delta S > \theta$) to the Conductor with focused context to trigger replanning. |
| **Quiescence** | Arm Task Completion State | `ArmAgent.is_quiescent` | `octoflow/arm.py` | Boolean flag indicating an arm has satisfied all domain objectives for the current cycle phase and can sleep. |
| **Subesophageal Motor Center** | Sandboxed Tool Execution Engine | `WorkspaceSandbox` | `octoflow/tools.py` | Security-enforcing workspace execution layer managing advisory path locks, path traversal validation, and command allowlists. |
| **Multi-Octopus Consortium** | Distributed Multi-Swarm Scaling | `OctosConsortium` | `octoflow/consortium.py` | Orchestrates 3 octopuses (24 arms, Triad) or 8 octopuses (64 arms, Octopolis) across decoupled functional domains. |
| **Cockpit** | Interactive Terminal REPL & TUI | `CockpitSession` | `octoflow/cockpit/app.py` | Non-blocking 20 FPS terminal interface rendering the live ASCII status HUD, runner animation, and safe shell router. |
| **Benthic Dot Runner** | Status Animation / Screensaver | `play_runner_animation` | `octoflow/runner.py` | ASCII animation engine displaying the swimming cephalopod status glyph during active swarm missions and idle screensaver. |
| **Inter-Brachial Lexicon** | Semantic Intent Protocol | `InterBrachialLexiconDecoder` | `octopus_brain/lexicon.py` | Decodes high-dimensional arm communication vectors into human-interpretable intents (`AUTONOMOUS_EXPLORE`, `TARGET_DETECTED`, etc.). |
| **Muscular Hydrostat** | Continuum Soft-Body Physics | `SoftBodyTentacleEnv` | `envs/soft_body_tentacle.py` | Biophysical 3D simulation of constant-volume tentacle elongation, radial contraction, and hydrodynamic fluid resistance. |
| **Truthful Token Receipt** | Execution Accounting Summary | `TokenReceipt` | `octoflow/receipt.py` | Post-mission receipt aggregating measured LLM completions, prompt tokens, and gate-avoided tokens without synthetic multipliers. |
| **Deterministic Replay** | Trace Event Playback Engine | `replay_trace` | `octoflow/trace.py` | Sequentially streams recorded JSONL execution traces to terminal lines and the WebSocket visualizer bridge at variable speed. |

