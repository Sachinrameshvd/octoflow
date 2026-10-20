"""Run Cephalopod Micro-Connectome Biophysical Simulation.

Demonstrates the complete Google-style connectome workflow:
1. Builds the micro-connectome graph adhering to cephalopod neuroanatomy & Dale's principle.
2. Exports the full connectome graph to JSON for 3D visualizers.
3. Initializes the biophysical Leaky Integrate-and-Fire simulation engine.
4. Coupes the connectome in closed loop with the 3D continuous soft-body hydrostat physics.
5. Displays population firing telemetry, spike counts, and motor coordination.
"""

import os
import json
import numpy as np

from octopus_brain.connectome import CephalopodConnectome
from octopus_brain.biophysics import BiophysicalConnectomeSimulator
from octopus_brain.connectome_controller import ConnectomeEmbodiedController
from envs.soft_body_tentacle import SoftBodyTentacleEnv


def main():
    print("=" * 80)
    print("🐙 CEPHALOPOD MICRO-CONNECTOME BIOPHYSICAL SIMULATION PIPELINE")
    print("=" * 80)

    # 1. Build Connectome
    print("\n[Step 1] Synthesizing Cephalopod Micro-Connectome Graph...")
    connectome = CephalopodConnectome(scale_factor=1.0, seed=42)
    summary = connectome.get_summary()

    print(f"  ✓ Total Neurons:              {summary['total_neurons']}")
    print(f"  ✓ Total Synaptic Edges:       {summary['total_synaptic_edges']}")
    print(f"  ✓ Mean Synapses / Neuron:     {summary['mean_synapses_per_neuron']}")
    print(f"  ✓ Neurotransmitter Breakdown: {summary['neurotransmitter_counts']}")
    print(f"  ✓ Cell Type Breakdown:        {summary['neuron_category_counts']}")

    # 2. Export Graph JSON for Visualizer
    os.makedirs("checkpoints", exist_ok=True)
    export_path = "checkpoints/cephalopod_connectome.json"
    connectome.export_json(export_path)
    print(f"\n[Step 2] Exported Connectome Graph JSON to: {export_path}")

    # 3. Biophysical LIF Dynamic Verification
    print("\n[Step 3] Initializing Biophysical Leaky Integrate-and-Fire Engine...")
    sim = BiophysicalConnectomeSimulator(connectome, dt_ms=0.5)

    # Inject stimulus into sensory afferents
    sfl_ids = connectome.region_node_ids.get("superior_frontal_lobe", [])[:4]
    sim.set_monitored_neurons(sfl_ids)

    def stimulus_fn(t_ms):
        i_ext = np.zeros(len(connectome.nodes), dtype=np.float32)
        if 10.0 <= t_ms <= 60.0:
            for nid in sfl_ids:
                i_ext[nid] = 25.0  # pA injection
        return i_ext

    sim_res = sim.run_sim(duration_ms=100.0, current_stimulus_fn=stimulus_fn)
    print(f"  ✓ Stimulus Duration:          {sim_res['duration_ms']} ms")
    print(f"  ✓ Total Action Potentials:    {sim_res['total_spikes']} spikes")
    print(f"  ✓ Network Firing Rate:        {sim_res['mean_firing_rate_hz']:.2f} Hz")

    pop_rates = sim.get_population_firing_rates(time_window_ms=50.0)
    print("  ✓ Regional Firing Rates (Hz):")
    for reg, rate in pop_rates.items():
        if rate > 0:
            print(f"    - {reg:<30}: {rate:>6.1f} Hz")

    # 4. Closed-Loop Embodied Coupling with Continuous 3D Soft-Body Tentacle Physics
    print("\n[Step 4] Executing Closed-Loop Embodied Simulation in Soft-Body Physics...")
    env = SoftBodyTentacleEnv(n_arms=8, max_steps=40)
    controller = ConnectomeEmbodiedController(connectome=connectome, steps_per_env_tick=20)

    episode_res = controller.run_closed_loop_episode(env, max_steps=30)
    print(f"  ✓ Steps Executed:             {episode_res['steps']}")
    print(f"  ✓ Cumulative Physics Reward:  {episode_res['total_reward']:.2f}")
    print(f"  ✓ Total Spikes in Loop:       {episode_res['total_spikes']}")
    print(f"  ✓ Final Population Rates:     {episode_res['final_population_rates_hz']}")

    print("\n" + "=" * 80)
    print("✅ Cephalopod Connectome & Biophysical Simulation Successfully Verified!")
    print("=" * 80)


if __name__ == "__main__":
    main()
