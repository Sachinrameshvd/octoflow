"""Closed-Loop Connectome Embodied Controller.

Bridges the biophysical Leaky Integrate-and-Fire connectome simulator with
the 3D continuous soft-body muscular hydrostat tentacle environment:
- Injects sensory currents into identified Chemotactile and Mechanoreceptive afferents.
- Integrates biophysical spikes through Central (Vertical Lobe + Subesophageal) and
  Brachial Axial reflex circuits.
- Decodes continuous motor command actuation (pitch bending, yaw bending, elongation)
  from Brachial Axial Motoneuron population spike rates.
- Closes the real-time sensorimotor loop in 3D physics.
"""

from typing import Any

import numpy as np
from envs.soft_body_tentacle import SoftBodyTentacleEnv

from octopus_brain.biophysics import BiophysicalConnectomeSimulator
from octopus_brain.connectome import CephalopodConnectome, NeuronCategory


class ConnectomeEmbodiedController:
    """Embodied controller coupling biophysical connectome spiking dynamics to continuous soft-body physics."""

    def __init__(
        self,
        connectome: CephalopodConnectome | None = None,
        dt_sim_ms: float = 0.5,
        steps_per_env_tick: int = 20,  # 20 * 0.5ms = 10ms neural integration per physics tick
    ):
        self.connectome = connectome or CephalopodConnectome(scale_factor=1.0)
        self.sim = BiophysicalConnectomeSimulator(self.connectome, dt_ms=dt_sim_ms)
        self.steps_per_env_tick = steps_per_env_tick
        self.n_neurons = len(self.connectome.nodes)

        # Cache arm sensory and motor neuron IDs
        self.arm_sensory_chemo: dict[int, list[int]] = {i: [] for i in range(8)}
        self.arm_sensory_mech: dict[int, list[int]] = {i: [] for i in range(8)}
        self.arm_motoneurons: dict[int, list[int]] = {i: [] for i in range(8)}

        for node in self.connectome.nodes:
            if node.arm_index >= 0:
                if node.category == NeuronCategory.SENSORY_CHEMO:
                    self.arm_sensory_chemo[node.arm_index].append(node.id)
                elif node.category == NeuronCategory.SENSORY_MECHANO:
                    self.arm_sensory_mech[node.arm_index].append(node.id)
                elif node.category == NeuronCategory.MOTOR_BRACHIAL:
                    self.arm_motoneurons[node.arm_index].append(node.id)

    def reset(self):
        """Resets biophysical simulator states."""
        self.sim.reset(randomize_v=True)

    def step(self, observations: np.ndarray) -> np.ndarray:
        """Translates environment observations into sensory currents, runs biophysical

        spiking integration, and decodes continuous motor actuation per arm.

        Args:
            observations: Shape (8, 16) array of local sensory patches per arm
                          (e.g. from SoftTentacleMuscularHydrostatEnv or ReachAndAvoid).

        Returns:
            actions: Shape (8, 4) continuous action array per arm:
                     (d_theta pitch, d_phi yaw, d_elongation, suction_toggle).
        """
        # 1. Map continuous sensory observations into injected synaptic currents (pA)
        i_ext = np.zeros(self.n_neurons, dtype=np.float32)

        for arm_idx in range(8):
            obs_arm = observations[arm_idx]
            # Sucker contact / chemotactile proximity (first 4 elements)
            chemo_cue = float(np.linalg.norm(obs_arm[0:4]))
            # Proprioceptive curvature / stretch (elements 4:8)
            mech_cue = float(np.linalg.norm(obs_arm[4:8]))

            # Inject current into chemo afferents
            for nid in self.arm_sensory_chemo[arm_idx]:
                i_ext[nid] = chemo_cue * 15.0  # Injected current amplitude

            # Inject current into mechano afferents
            for nid in self.arm_sensory_mech[arm_idx]:
                i_ext[nid] = mech_cue * 12.0

        # 2. Advance biophysical connectome across internal time steps
        spike_accumulator = np.zeros(self.n_neurons, dtype=np.int32)
        for _ in range(self.steps_per_env_tick):
            spikes = self.sim.step(i_ext)
            spike_accumulator += spikes.astype(np.int32)

        # 3. Population Rate Decoding: Convert Motoneuron Spikes into 3D Continuum Commands
        actions = np.zeros((8, 4), dtype=np.float32)
        total_time_sec = (self.steps_per_env_tick * self.sim.dt) / 1000.0

        for arm_idx in range(8):
            m_ids = self.arm_motoneurons[arm_idx]
            if len(m_ids) == 0:
                continue

            # Firing rates of segmental motoneurons
            segment_rates = [spike_accumulator[nid] / total_time_sec for nid in m_ids]
            mean_rate = float(np.mean(segment_rates))
            rate_gradient = (
                float(segment_rates[-1] - segment_rates[0]) if len(segment_rates) > 1 else 0.0
            )

            # Decode pitch (d_theta) from basal vs distal motoneuron balance
            d_theta = np.clip(rate_gradient / 20.0, -1.0, 1.0)

            # Decode yaw (d_phi) from lateral interbrachial asymmetry
            left_arm = (arm_idx - 1) % 8
            right_arm = (arm_idx + 1) % 8
            left_rate = float(
                np.mean([spike_accumulator[nid] for nid in self.arm_motoneurons[left_arm]])
            )
            right_rate = float(
                np.mean([spike_accumulator[nid] for nid in self.arm_motoneurons[right_arm]])
            )
            d_phi = np.clip((right_rate - left_rate) / 15.0, -1.0, 1.0)

            # Decode elongation from overall axial motoneuron drive
            d_elongate = np.clip((mean_rate - 10.0) / 25.0, -1.0, 1.0)

            # Suction toggle activated when proximal suckers detect target contact
            suction = 1.0 if chemo_cue > 0.5 else 0.0

            actions[arm_idx] = [d_theta, d_phi, d_elongate, suction]

        return actions

    def run_closed_loop_episode(
        self,
        env: SoftBodyTentacleEnv,
        max_steps: int = 50,
    ) -> dict[str, Any]:
        """Runs a complete closed-loop sensorimotor episode in 3D soft-body physics."""
        self.reset()
        reset_res = env.reset()
        obs = reset_res[0] if isinstance(reset_res, tuple) else reset_res
        total_reward = 0.0
        trajectory = []
        firing_telemetry = []

        for step_idx in range(max_steps):
            actions = self.step(obs)
            step_res = env.step(actions)
            if len(step_res) == 5:
                next_obs, rewards, term, trunc, info = step_res
                done = term or trunc
            else:
                next_obs, rewards, done, info = step_res

            total_reward += float(np.sum(rewards))

            pop_rates = self.sim.get_population_firing_rates(time_window_ms=20.0)
            firing_telemetry.append(pop_rates)

            trajectory.append(
                {
                    "step": step_idx,
                    "reward": float(np.sum(rewards)),
                    "actions_mean": float(np.mean(actions)),
                }
            )
            obs = next_obs
            if done:
                break

        return {
            "total_reward": total_reward,
            "steps": len(trajectory),
            "total_spikes": len(self.sim.spike_history),
            "final_population_rates_hz": firing_telemetry[-1] if firing_telemetry else {},
            "trajectory": trajectory,
        }
