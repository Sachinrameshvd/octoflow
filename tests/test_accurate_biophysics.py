"""Tests for 99% Accurate Cephalopod Electrophysiology and Neuroscience Modules."""

import numpy as np
from octopus_brain.bend_propagation import StereotypicBendWaveController
from octopus_brain.hodgkin_huxley import CephalopodHodgkinHuxley
from octopus_brain.neuromodulation import CephalopodNeuromodulation
from octopus_brain.vertical_lobe_ltp import VerticalLobeAssociativeMemory


class TestCephalopodHodgkinHuxley:
    """Test suite for Hodgkin-Huxley multi-channel electrophysiology."""

    def test_resting_stability(self):
        hh = CephalopodHodgkinHuxley(n_neurons=2, temp_celsius=16.0, dt_ms=0.025)
        # Step without injection
        for _ in range(100):
            spikes = hh.step(None)
            assert not spikes.any(), "Should not spontaneously spike at rest"
        # Invertebrate resting potential settles near -74 mV due to A-type potassium conductance
        assert -76.0 <= float(hh.v[0]) <= -65.0
        assert np.isclose(hh.v[0], hh.v[1], atol=1e-3)

    def test_action_potential_generation(self):
        hh = CephalopodHodgkinHuxley(n_neurons=1, temp_celsius=16.0, dt_ms=0.01)
        inj = np.array([45.0], dtype=np.float32)

        peak_v = -65.0
        spiked = False
        for _ in range(800):
            spikes = hh.step(inj)
            peak_v = max(peak_v, float(hh.v[0]))
            if spikes[0]:
                spiked = True

        assert spiked, "Depolarizing current must trigger an action potential"
        assert peak_v > 0.0, f"Action potential peak should overshoot 0 mV, got {peak_v:.1f} mV"


class TestVerticalLobeLTP:
    """Test suite for Vertical Lobe presynaptic LTP associative memory."""

    def test_ltp_reinforcement_potentiation(self):
        vl = VerticalLobeAssociativeMemory(
            n_sfl_inputs=8, n_amacrine_fibers=64, n_efferent_outputs=2
        )
        cues = np.zeros(8, dtype=np.float32)
        cues[0:2] = 1.0

        initial_drive = float(vl.forward(cues)[0])

        # Apply dopaminergic reward
        for _ in range(5):
            vl.forward(cues)
            vl.apply_reinforcement(reward_dopamine=0.8, target_action_idx=0)

        post_drive = float(vl.forward(cues)[0])
        assert post_drive > initial_drive, (
            "Vertical Lobe efferent drive must potentiate after dopaminergic pairing"
        )
        assert vl.ltp_event_count == 5

    def test_ltd_punishment_depression(self):
        vl = VerticalLobeAssociativeMemory(
            n_sfl_inputs=8, n_amacrine_fibers=64, n_efferent_outputs=2, initial_weight=1.0
        )
        cues = np.ones(8, dtype=np.float32)

        initial_drive = float(vl.forward(cues)[1])

        # Apply serotonergic shock
        for _ in range(5):
            vl.forward(cues)
            vl.apply_reinforcement(punishment_serotonin=0.8, target_action_idx=1)

        depressed_drive = float(vl.forward(cues)[1])
        assert depressed_drive < initial_drive, (
            "Vertical Lobe efferent drive must depress after punishment"
        )
        assert vl.ltd_event_count == 5


class TestStereotypicBendWave:
    """Test suite for stereotypic bend propagation traveling waves."""

    def test_wave_propagation_along_arm(self):
        controller = StereotypicBendWaveController(
            n_segments=5, conduction_velocity_ms=2.0, arm_nominal_length_m=0.5, dt_sec=0.02
        )
        controller.trigger_reach(
            arm_idx=0, target_pitch_theta=0.7, target_yaw_phi=-0.5, amplitude=1.0
        )

        assert controller.wave_active[0]

        has_moved = False
        for _ in range(20):
            actions = controller.step()
            if actions[0, 0] > 0.1:  # Pitch bending active
                has_moved = True

        assert has_moved, "Bend wave must activate muscle deltas during propagation"


class TestNeuromodulation:
    """Test suite for molluscan neuromodulators and neuropeptides."""

    def test_prey_and_reward_surges(self):
        nm = CephalopodNeuromodulation()
        init_oct = nm.octopamine
        init_dop = nm.dopamine

        nm.trigger_prey_detected(1.0)
        assert nm.octopamine > init_oct, "Octopamine should surge when detecting prey"

        nm.trigger_food_reward(1.0)
        assert nm.dopamine > init_dop, "Dopamine should surge upon food reward"
        assert nm.get_motor_gain() > 1.0, "Motor gain should increase with FMRFamide"
