# OctoFlow: System Architecture & Cephalopod Neural Foundations

This document provides the complete technical and biophysical architectural reference for OctoFlow (OctopusBrain), previously maintained in the primary repository manual.

---

## Table of Contents

1. [Architectural Overview & Biological Foundations](#1-architectural-overview--biological-foundations)
2. [Reinforcement Learning Benchmarks & Policy Milestones](#2-reinforcement-learning-benchmarks--policy-milestones)
3. [The 5-Stage Cognitive Problem-Solving Pipeline](#3-the-5-stage-cognitive-problem-solving-pipeline)
4. [3D Continuous Soft-Body Muscular Hydrostat Physics](#4-3d-continuous-soft-body-muscular-hydrostat-physics)
5. [Cephalopod Micro-Connectome & Biophysical Simulation](#5-cephalopod-micro-connectome--biophysical-simulation)
6. [ONNX Export & In-Browser WebAssembly Inference](#6-onnx-export--in-browser-webassembly-inference)
7. [Universal Gymnasium Adapter](#7-universal-gymnasium-adapter)
8. [Complete Repository Structure](#8-complete-repository-structure)

---

## 1. Architectural Overview & Biological Foundations

OctoFlow models its software engineering swarm and coordination fabric on the decentralized-centralized organization of the cephalopod nervous system (*Octopus vulgaris*):

* **Decentralized Peripheral Ganglia (8 Arms):** Two-thirds of an octopus's ~500 million neurons are located in the brachial axial nerve cords of its eight arms, allowing each arm to sense, process, and actuate movements semi-autonomously.
* **Central Coordination (Supraesophageal Ganglion):** The central brain does not micromanage fine motor movements; instead, it issues high-level directives, binds arms into dynamic coalitions, and resolves unexpected novel situations.
* **Lateral Inter-Brachial Ring:** An inter-brachial commissure encircles the base of the arms, enabling low-latency lateral signal passing between adjacent arms without routing through the central conductor.
* **Sensory Surprise Gating:** Predictive forward models at each peripheral arm estimate incoming sensory states. Only when prediction error ($\Delta S$) exceeds an adaptive threshold $\theta$ does the arm escalate to the central conductor.

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

---

## 2. Reinforcement Learning Benchmarks & Policy Milestones

Following curriculum-based reinforcement learning with Generalized Advantage Estimation (GAE), predictive forward models, and Lagrangian dual adaptive gating budgets, the simulated cephalopod neural policy achieved the following coordination milestones:

| Metric | Baseline Initial | Top 1% Trained Policy | Improvement |
| :--- | :--- | :--- | :--- |
| **Mean Evaluation Reward** | $+12.60 \pm 1.8$ | **$+42.10 \pm 4.2$** (Peak $+54.95$) | **$+234\%$ Surge** |
| **Joint Multi-Arm Task Success** | $14.2\%$ | **$+77.4\%$** | **$+5.4\times$ Multi-Arm Lock** |
| **Hazard Avoidance Rate** | $62.0\%$ | **$98.5\%$** ($0.1$ hits/ep) | **Near-Zero Contact** |
| **Communication Budget** | $100.0\%$ (Dense) | **$18.4\%$** (Target $\le 22\%$) | **$81.6\%$ Bandwidth Savings** |
| **Token Reduction (Simulated Swarm)** | $0.0\%$ (Chatty Baseline) | **$93.3\%$ Savings (Theoretical)** | **Target Cost Cut** |
| **Amputation Resilience** | Severe Collapse | **$82.5\%$ Reward Retained** | **Decentralized Fault-Tolerance** |
| **Test Suite Coverage** | $25/25$ Passing | **$73/74$ Passing (1 skipped)** | **System Verification** |

*Note on Token Reduction:* The $93.3\%$ theoretical reduction reflects dense communication suppression in the biophysical simulation; real-world software engineering swarm token reductions are measured via `octoflow receipt` and benchmarked in [docs/benchmarks.md](docs/benchmarks.md).

---

## 3. The 5-Stage Cognitive Problem-Solving Pipeline

When the architecture processes an environmental task or software engineering mission, computation progresses through five stages:

```text
+---------------------------------------------------------------------------------------------------+
|                                  5-STAGE COGNITIVE FLOW PIPELINE                                  |
+---------------------------------------------------------------------------------------------------+
  Stage 1: Sensory Perception          --> 8 Egocentric Patches (Targets, Hazards, Joint Positions)
  Stage 2: Local Predictive Coding     --> Sensory Surprise Metric: Delta S_i = (1/D) ||o_t - o_hat_t||^2
  Stage 3: Event-Triggered Gating      --> Adaptive Sigmoid Threshold theta (Sparse Budget <= 22%)
  Stage 4: Coalition & Semantic Chatter--> Supraesophageal Ganglion Binding + Inter-Brachial Lexicon
  Stage 5: Motor Solution & Evaluation --> Discrete / Continuous Actuation + Actor-Critic V(s) Value
+---------------------------------------------------------------------------------------------------+
```

1. **Stage 1: Sensory Perception**
   Each of the 8 peripheral brachial ganglia captures egocentric sensory patches (joint proprioception, chemical target cues, predator vectors, substrate contact).
2. **Stage 2: Local Predictive Coding & Sensory Surprise**
   Peripheral forward models continuously predict the next observation state $\hat{o}_{t+1}$. Prediction error calculates sensory surprise: $\Delta S_t = \frac{1}{D} \|o_t - \hat{o}_t\|_2^2$.
3. **Stage 3: Event-Triggered Gating Decision**
   An adaptive sigmoid gating threshold $\theta$ decides whether to handle the situation locally or send an urgent report to the central brain.
4. **Stage 4: Central Multi-Head Coalition Binding & Semantic Chatter**
   The central *Supraesophageal Ganglion* computes multi-head attention over reporting arms, binding them into temporary cooperative task forces (e.g. Arms 2 and 3 for dual-arm prey capture).
   Communication vectors map to the **Inter-Brachial Message Lexicon**:
   * `AUTONOMOUS_EXPLORE`: Routine local sensory sweep.
   * `TARGET_DETECTED`: Chemosensory verification of edible food item.
   * `COOPERATIVE_PULL`: Bilateral joint force synchronization.
   * `HAZARD_WARNING`: Defensive predator avoidance.
   * `REACH_ELONGATION`: Muscular hydrostat extension.
5. **Stage 5: Solution Generation & Evaluation**
   Discrete or continuous motor commands are executed per arm, while decentralized critics output state-value baselines $V(s)$.

---

## 4. 3D Continuous Soft-Body Muscular Hydrostat Physics

Implemented in `envs/soft_body_tentacle.py`, the physical tentacle model simulates continuum mechanics:

* **Muscular Hydrostat Constant-Volume Invariant:**
  $$V = \pi \cdot r^2 \cdot L = \text{const}$$
  Elongation along the longitudinal muscle layer causes proportional radial contraction; transverse muscle activation expands radial cross-section.
* **Continuum 3D Curvature:** Pitch ($\theta$), yaw ($\phi$), and elongation ($L$) across multiple continuum segments per arm.
* **Hydrodynamic Viscous Drag:** Quadratic ocean fluid resistance ($F_d = \frac{1}{2} C_d \rho v^2$) and buoyancy damping in oceanic columns.

---

## 5. Cephalopod Micro-Connectome & Biophysical Simulation

OctoFlow includes an explicit micro-connectome generator and biophysical simulation engine inspired by Google Connectomics and FlyWire methodology:

* **Biological Dale's Principle & Polarity:** Enforces strict neurotransmitter identities per cell:
  * Excitatory: **Acetylcholine (ACh)** ($\mathbf{W} > 0$)
  * Inhibitory: **GABA** and **Glutamate** ($\mathbf{W} < 0$)
  * Neuromodulatory: **Dopamine** and **Octopamine**
* **Cephalopod Microcircuits:**
  * **Vertical Lobe (VL) System:** Parallel amacrine matrix with long-term potentiation (LTP) capability.
  * **Subesophageal Motor Centers:** Anterior/posterior basal descending command tracts.
  * **Interbrachial Nerve Ring:** 8-arm recurrent coordination ring.
  * **8 Brachial Axial Cords:** Segmental chemotactile receptors, mechanoreceptive stretch sensors, and axial motoneurons.
* **Leaky Integrate-and-Fire (LIF) Biophysics:** Conductance-based synaptic dynamics ($\tau_m = 20\text{ ms}$, $\tau_{exc} = 5\text{ ms}$, $\tau_{inh} = 10\text{ ms}$) with absolute refractory periods.
* **Embodied Closed-Loop Coupling:** Injects continuous marine cues into sensory afferents and decodes motoneuron population spikes to actuate the 3D soft-body muscular hydrostats.
* **Simulation Scripts:**
  * Connectome baseline: `python experiments/run_connectome_sim.py`
  * Hodgkin-Huxley & bend waves: `python experiments/run_accurate_octopus_brain.py`
  * Adult 500M connectomics: `python experiments/run_blue_brain_octopus.py`

---

## 6. ONNX Export & In-Browser WebAssembly Inference

The trained neural network exports to a standalone ONNX model graph (`checkpoints/octopus_brain.onnx`, ~1.9 MB), verified for action parity:

```python
import onnxruntime as ort

session = ort.InferenceSession("checkpoints/octopus_brain.onnx")
# Runs on CPU, C++, ROS2 robots, or in WebAssembly inside modern browsers
```

In the interactive visualizer (`visualizer/`), the neural network can run directly in the client browser via `onnxruntime-web`, enabling offline client-side evaluation without a running Python backend.

---

## 7. Universal Gymnasium Adapter

Connect the cephalopod brain to standard Gymnasium environments (`CartPole-v1`, `LunarLander-v2`, `Acrobot-v1`) via `octopus_brain.adapter.OctopusGymAdapter`:

```python
import gymnasium as gym
from octopus_brain.brain import OctopusBrain
from octopus_brain.adapter import OctopusGymAdapter

# Load trained brain checkpoint
brain = OctopusBrain.load_top1("checkpoints/top1_octopus_brain.pt")

# Wrap external environment
env = gym.make("CartPole-v1")
adapter = OctopusGymAdapter(brain=brain, env=env)

# Evaluate
results = adapter.evaluate(episodes=5)
print("Mean Reward:", results["mean_reward"])
```

---

## 8. Complete Repository Structure

```text
Octoflow/
├── octoflow/                  # Multi-Agent Swarm Orchestrator & CLI
│   ├── cli.py                 # CLI entrypoint and subcommand registration
│   ├── conductor.py           # SupraesophagealConductor & dynamic coalition attention
│   ├── arm.py                 # ArmAgent: autonomous worker with Saccade Buffer pruning
│   ├── gate.py                # SurpriseGate: event-triggered sensory surprise (Delta S <= theta)
│   ├── encoder.py             # CodeSensoryEncoder (maps stdout/diff -> 16-dim obs)
│   ├── bus.py                 # InterBrachialBus: ring-topology lateral communication
│   ├── memory.py              # VerticalLobeMemory: Hebbian associative LTP cache
│   ├── tools.py               # WorkspaceSandbox with path security & advisory locks
│   ├── provider.py            # Pluggable LLM interface (Mock, Anthropic, OpenAI, Ollama)
│   ├── server.py              # Telemetry WebSocket broadcaster for 3D visualizer
│   ├── trace.py               # Execution trace recording & replay engine
│   └── cockpit/               # Terminal TUI, runner animation, and interactive REPL
├── octopus_brain/             # Cephalopod Neural Network Architecture
│   ├── brain.py               # OctopusBrain (ring topology, step & diagnostics)
│   ├── modules.py             # PeripheralModule (local GRU, policy, surprise, gate)
│   ├── central.py             # CentralSystem (multi-head coalition attention)
│   ├── lexicon.py             # InterBrachialLexiconDecoder (semantic intent clustering)
│   ├── adapter.py             # OctopusGymAdapter (Gymnasium environment wrapper)
│   ├── losses.py              # OctopusLoss & AdaptiveGateBudgeter (Lagrangian dual)
│   ├── config.py              # Configuration dataclasses
│   └── trainer.py             # Multi-step PPO/GAE reinforcement learning trainer
├── envs/                      # Biophysical & Continuum Simulation Environments
│   ├── reach_and_avoid.py     # Reach & Avoid environment with joint cooperative tasks
│   ├── hunting_env.py         # Multi-prey hunting & bilateral encirclement
│   ├── soft_body_tentacle.py  # 3D continuous muscular hydrostat continuum physics
│   ├── curriculum.py          # Adaptive curriculum manager
│   └── render_env.py          # ASCII & Matplotlib animation renderer
├── experiments/               # Training, simulation, and export launchers
│   ├── live_bridge.py         # HTTP cognitive telemetry bridge for 3D visualizer
│   ├── export_onnx.py         # Standalone zero-dependency ONNX exporter
│   ├── run_external_env.py    # Universal external Gymnasium runner
│   ├── train.py               # CLI end-to-end training launcher
│   └── infer.py               # Standalone inference runner
├── checkpoints/               # Neural checkpoints and connectome topologies
│   ├── top1_octopus_brain.pt  # Trained top 1% model weights (+42.10 reward)
│   └── octopus_brain.onnx     # Standalone 1.9 MB ONNX model
├── visualizer/                # 3D WebGL Three.js Visualizer & WASM Engine
│   ├── src/core/onnx-brain.ts # In-browser WebAssembly ONNX inference engine
│   ├── src/ui/                # HUD and cognitive flow inspector
│   └── index.html             # Interface template
├── examples/                  # Verified end-to-end applications
│   ├── resume-analyzer/       # AI Resume Analyzer built by OctoFlow (P7.2 showcase)
│   ├── custom_provider/       # LM Studio / custom provider template (P8.1)
│   └── guilds/                # Custom 8-arm specialist rosters (P8.2)
├── docs/                      # Comprehensive documentation and field guides
└── tests/                     # Unit, integration, security, and contract test suites
```
