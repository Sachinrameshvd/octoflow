"""Run Blue Brain 500,000,000-Neuron Adult Cephalopod Connectomics Pipeline.

Demonstrates the full-scale algorithmic synthesis and multi-scale simulation:
1. Adult Octopus vulgaris whole-brain 3D atlas (500,000,000 neurons, ~62.5 billion synapses).
2. Canonical microcircuit instantiation using Peter's rule distance kernels.
3. Macro-scale inter-lobe tractography connecting all 30+ brain lobes.
4. Closed-loop multi-scale hybrid simulation in 3D soft-body muscular hydrostat physics.
"""

from envs.soft_body_tentacle import SoftBodyTentacleEnv
from octopus_brain.blue_brain.atlas import AdultOctopusAtlas
from octopus_brain.blue_brain.hybrid_simulator import AdultOctopusHybridSimulator
from octopus_brain.blue_brain.sparse_synthesizer import AdultOctopusConnectomeSynthesizer


def main():
    print("=" * 80)
    print("🐙 BLUE BRAIN FULL-SCALE ADULT CEPHALOPOD CONNECTOMICS SYNTHESIS")
    print("   Total Modeled Neurons:  500,000,000  |  Est. Synapses: ~62.5 Billion")
    print("=" * 80)

    # 1. Atlas & Morphometric Volumetric Summary
    print("\n[Step 1] Loading Adult Octopus vulgaris 3D Anatomical Atlas...")
    atlas = AdultOctopusAtlas()
    summary = atlas.get_summary()

    print(f"  ✓ Species:                     {summary['species']}")
    print(f"  ✓ Total Adult Neurons:         {summary['total_neurons']:,}")
    print(f"  ✓ Total Brain Volume:          {summary['total_volume_mm3']} mm³")
    print(f"  ✓ Lobe Count:                  {summary['lobes_count']} anatomical lobes")
    print(f"  ✓ Distribution Ratio:          {summary['central_to_peripheral_ratio']}")
    print(
        f"  ✓ Supraesophageal Mass:        {summary['neuron_distribution_by_mass']['supraesophageal_mass']:,} neurons"
    )
    print(
        f"  ✓ Subesophageal Mass:          {summary['neuron_distribution_by_mass']['subesophageal_mass']:,} neurons"
    )
    print(
        f"  ✓ Bilateral Optic Lobes:       {summary['neuron_distribution_by_mass']['optic_lobes']:,} neurons"
    )
    print(
        f"  ✓ 8 Distributed Arm Cords:     {summary['neuron_distribution_by_mass']['brachial_arms_total']:,} neurons"
    )

    # 2. Algorithmic Connectome Synthesizer
    print("\n[Step 2] Synthesizing Micro-Connectome Rules via Peter's Rule...")
    synthesizer = AdultOctopusConnectomeSynthesizer(atlas=atlas, seed=42)
    syn_summary = synthesizer.summary

    print(f"  ✓ Total Biological Synapses:   {syn_summary['total_estimated_synapses']:,}")
    print(
        f"  ✓ Mean Synapses per Neuron:    {syn_summary['mean_synapses_per_neuron']} synapses/cell"
    )

    # 3. Microcircuit Chunk Extraction
    print("\n[Step 3] Procedurally Instantiating Sample Microcircuit Chunks...")
    chunk_vl = synthesizer.synthesize_microcircuit_chunk(
        lobe_id="vertical_lobe", n_sample_neurons=250
    )
    print(
        f"  ✓ Vertical Lobe Sample Chunk:  {chunk_vl['chunk_neuron_count']} cells -> {chunk_vl['edges_count']} synapses (Peter's Rule P(d))"
    )

    chunk_arm = synthesizer.synthesize_microcircuit_chunk(
        lobe_id="brachial_arm_0", n_sample_neurons=250
    )
    print(
        f"  ✓ Arm #1 Neuromere Chunk:     {chunk_arm['chunk_neuron_count']} cells -> {chunk_arm['edges_count']} synapses"
    )

    # 4. Multi-Scale Hybrid Simulation in 3D Soft-Body Physics
    print("\n[Step 4] Launching 500M Neural Mass Continuum in 3D Soft-Body Physics...")
    sim = AdultOctopusHybridSimulator(synthesizer=synthesizer, dt_sec=0.01)
    env = SoftBodyTentacleEnv(n_arms=8, max_steps=20)

    episode_res = sim.run_embodied_episode(env=env, max_steps=20)
    print(f"  ✓ Steps Executed:              {episode_res['steps_executed']}")
    print(f"  ✓ Cumulative Physics Reward:   {episode_res['total_reward']}")
    print(f"  ✓ Represented Living Neurons:  {episode_res['total_represented_neurons']:,}")
    print("  ✓ Active Macro Firing Rates (Hz):")
    for lid, rate in list(episode_res["final_macro_rates"].items())[:6]:
        print(f"    - {lid:<30}: {rate:>5.1f} Hz")

    print("\n" + "=" * 80)
    print("✅ BLUE BRAIN 500,000,000-NEURON ADULT CEPHALOPOD PIPELINE COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
