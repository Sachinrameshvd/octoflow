"""Tests for Blue Brain 500M-Neuron Adult Cephalopod Connectomics Pipeline."""

import numpy as np
from envs.soft_body_tentacle import SoftBodyTentacleEnv
from octopus_brain.blue_brain.atlas import AdultOctopusAtlas
from octopus_brain.blue_brain.hybrid_simulator import AdultOctopusHybridSimulator
from octopus_brain.blue_brain.microcircuits import CephalopodMicrocircuitLibrary
from octopus_brain.blue_brain.sparse_synthesizer import AdultOctopusConnectomeSynthesizer


class TestAdultOctopusAtlas:
    """Test suite for whole-brain 500M adult cephalopod atlas."""

    def test_atlas_total_neuron_count(self):
        atlas = AdultOctopusAtlas()
        summary = atlas.get_summary()

        assert summary["total_neurons"] == 500_000_000
        assert summary["total_volume_mm3"] > 1000.0
        assert summary["lobes_count"] >= 15

        # Check 1/3 Central vs 2/3 Peripheral distribution ratio
        periph = summary["neuron_distribution_by_mass"]["brachial_arms_total"]
        assert periph == 300_000_000  # Exactly 60% in arms
        assert summary["neuron_distribution_by_mass"]["supraesophageal_mass"] == 45_000_000
        assert summary["neuron_distribution_by_mass"]["optic_lobes"] == 130_000_000


class TestMicrocircuitsAndPetersRule:
    """Test suite for canonical microcircuit templates and Peter's Rule."""

    def test_peters_rule_distance_decay(self):
        library = CephalopodMicrocircuitLibrary()

        # At distance 0 um, connection probability should be near base P_0
        p_close = library.calculate_connection_probability("vertical_lobe", distance_um=10.0)
        p_mid = library.calculate_connection_probability("vertical_lobe", distance_um=100.0)
        p_far = library.calculate_connection_probability("vertical_lobe", distance_um=500.0)

        assert p_close > p_mid > 0.0
        assert p_far == 0.0  # Outside receptive field


class TestConnectomeSynthesizer:
    """Test suite for full-scale connectome synthesizer."""

    def test_full_scale_metrics(self):
        synthesizer = AdultOctopusConnectomeSynthesizer()
        summary = synthesizer.summary

        assert summary["total_adult_neurons"] == 500_000_000
        assert summary["total_estimated_synapses"] > 50_000_000_000  # Over 50 billion synapses
        assert summary["mean_synapses_per_neuron"] > 100

    def test_procedural_chunk_generation(self):
        synthesizer = AdultOctopusConnectomeSynthesizer(seed=123)
        chunk = synthesizer.synthesize_microcircuit_chunk("vertical_lobe", n_sample_neurons=100)

        assert chunk["chunk_neuron_count"] == 100
        assert len(chunk["nodes"]) == 100
        assert chunk["edges_count"] > 0
        assert "position_mm" in chunk["nodes"][0]

        # Verify reproducibility with same seed
        chunk_repeat = synthesizer.synthesize_microcircuit_chunk(
            "vertical_lobe", n_sample_neurons=100, chunk_seed=123
        )
        assert chunk["edges_count"] == chunk_repeat["edges_count"]
        assert np.allclose(
            chunk["nodes"][0]["position_mm"], chunk_repeat["nodes"][0]["position_mm"]
        )


class TestHybridSimulator:
    """Test suite for 500M neural mass & embodied hybrid simulator."""

    def test_simulator_step(self):
        sim = AdultOctopusHybridSimulator()
        sim.reset()

        res = sim.step({"optic_lobe_left": 10.0})
        assert "macro_firing_rates" in res
        assert res["total_adult_represented_neurons"] == 500_000_000
        assert res["actions"].shape == (8, 4)
        assert res["mean_macro_rate_hz"] > 0.0

    def test_embodied_episode(self):
        sim = AdultOctopusHybridSimulator()
        env = SoftBodyTentacleEnv(n_arms=8, max_steps=10)

        res = sim.run_embodied_episode(env=env, max_steps=10)
        assert res["steps_executed"] == 10
        assert res["total_represented_neurons"] == 500_000_000
        assert "final_macro_rates" in res
