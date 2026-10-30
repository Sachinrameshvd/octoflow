"""Tests for Cephalopod Micro-Connectome Architecture and Biophysical Simulation Engine."""

import json

import numpy as np
from envs.soft_body_tentacle import SoftBodyTentacleEnv
from octopus_brain.biophysics import BiophysicalConnectomeSimulator
from octopus_brain.connectome import (
    CephalopodConnectome,
)
from octopus_brain.connectome_controller import ConnectomeEmbodiedController


class TestCephalopodConnectome:
    """Test suite for connectome graph construction and Dale's principle."""

    def test_connectome_creation(self):
        connectome = CephalopodConnectome(scale_factor=1.0, seed=42)
        summary = connectome.get_summary()

        assert summary["total_neurons"] > 100
        assert summary["total_synaptic_edges"] > 200
        assert summary["mean_synapses_per_neuron"] > 1.5

        # Check key cephalopod regions exist
        expected_regions = [
            "superior_frontal_lobe",
            "vertical_lobe",
            "subvertical_lobe",
            "subesophageal_mass",
            "interbrachial_nerve_ring",
            "brachial_arm_0",
            "brachial_arm_7",
        ]
        for reg in expected_regions:
            assert reg in summary["regions"]

    def test_dales_principle_integrity(self):
        """Verify that every neuron adheres to Dale's Principle: single polarity for all outgoing edges."""
        connectome = CephalopodConnectome(scale_factor=1.0, seed=123)

        for node in connectome.nodes:
            outgoing = connectome.edges_by_source[node.id]
            for edge in outgoing:
                assert edge.sign == node.sign, (
                    f"Violation of Dale's principle: Node {node.id} ({node.neurotransmitter}) "
                    f"has sign {node.sign} but outgoing edge has sign {edge.sign}"
                )

    def test_adjacency_matrix_structure(self):
        connectome = CephalopodConnectome(scale_factor=1.0, seed=42)
        W = connectome.get_adjacency_matrix()
        n = len(connectome.nodes)

        assert W.shape == (n, n)
        assert not np.isnan(W).any()
        assert not np.isinf(W).any()

        # Check positive (excitatory) and negative (inhibitory) weights both exist
        assert (W > 0).any(), "Adjacency matrix must have excitatory synaptic weights"
        assert (W < 0).any(), "Adjacency matrix must have inhibitory synaptic weights"

    def test_export_json(self, tmp_path):
        connectome = CephalopodConnectome(scale_factor=0.5, seed=42)
        export_file = tmp_path / "test_connectome.json"
        connectome.export_json(str(export_file))

        assert export_file.exists()
        with open(export_file, encoding="utf-8") as f:
            data = json.load(f)

        assert "metadata" in data
        assert "nodes" in data
        assert "edges" in data
        assert len(data["nodes"]) == len(connectome.nodes)
        assert len(data["edges"]) == len(connectome.edges)


class TestBiophysicalSimulator:
    """Test suite for Leaky Integrate-and-Fire biophysical dynamics."""

    def test_quiescent_resting_state(self):
        connectome = CephalopodConnectome(scale_factor=1.0, seed=42)
        sim = BiophysicalConnectomeSimulator(connectome, dt_ms=0.5)
        sim.reset(randomize_v=False)

        # Step without external current
        for _ in range(50):
            spikes = sim.step(external_currents=None)
            assert not spikes.any(), (
                "Neurons should not spontaneously spike without current injection"
            )

        # Membrane potential should remain at rest
        assert np.allclose(sim.v, sim.v_rest, atol=1e-3)

    def test_spiking_upon_depolarization(self):
        connectome = CephalopodConnectome(scale_factor=1.0, seed=42)
        sim = BiophysicalConnectomeSimulator(connectome, dt_ms=0.5)
        sim.reset(randomize_v=False)

        target_nid = 0
        i_ext = np.zeros(len(connectome.nodes), dtype=np.float32)
        i_ext[target_nid] = 50.0  # Strong depolarizing current

        spiked = False
        for _ in range(100):
            spikes = sim.step(i_ext)
            if spikes[target_nid]:
                spiked = True
                break

        assert spiked, f"Neuron {target_nid} should have generated an action potential"
        assert len(sim.spike_history) >= 1

    def test_population_firing_rates(self):
        connectome = CephalopodConnectome(scale_factor=1.0, seed=42)
        sim = BiophysicalConnectomeSimulator(connectome, dt_ms=0.5)
        sim.reset(randomize_v=False)

        # Stimulate superior frontal lobe neurons
        sfl_ids = connectome.region_node_ids["superior_frontal_lobe"]
        i_ext = np.zeros(len(connectome.nodes), dtype=np.float32)
        for nid in sfl_ids:
            i_ext[nid] = 30.0

        for _ in range(60):
            sim.step(i_ext)

        rates = sim.get_population_firing_rates(time_window_ms=30.0)
        assert "superior_frontal_lobe" in rates
        assert rates["superior_frontal_lobe"] > 0.0


class TestConnectomeEmbodiedController:
    """Test suite for closed-loop sensorimotor integration in 3D physics."""

    def test_controller_step_output_shape(self):
        controller = ConnectomeEmbodiedController()
        dummy_obs = np.random.uniform(-1.0, 1.0, size=(8, 16)).astype(np.float32)

        actions = controller.step(dummy_obs)
        assert actions.shape == (8, 4)
        assert np.all(actions[:, 0:3] >= -1.0) and np.all(actions[:, 0:3] <= 1.0)
        assert np.all(np.isin(actions[:, 3], [0.0, 1.0]))

    def test_closed_loop_episode(self):
        env = SoftBodyTentacleEnv(n_arms=8, max_steps=15)
        controller = ConnectomeEmbodiedController(steps_per_env_tick=10)

        result = controller.run_closed_loop_episode(env, max_steps=10)
        assert result["steps"] == 10
        assert "total_reward" in result
        assert result["total_spikes"] > 0
        assert "final_population_rates_hz" in result
