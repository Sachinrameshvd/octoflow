"""Vertical Lobe (VL) System: Cephalopod Long-Term Potentiation (LTP) Matrix.

Implements the biological associative memory matrix discovered by
B. Hochner and T. Shomrat (2008, 2012):
- The Vertical Lobe operates as an associative memory matrix containing ~25 million parallel
  Amacrine interneuron fibers receiving afferents from the Superior Frontal Lobe (SFL).
- Amacrine cells synapse onto large Efferent neurons driving motor attack or avoidance.
- Presynaptic Long-Term Potentiation (LTP) is induced by pairing conditioned sensory cues
  (visual or chemotactile patterns) with unconditioned reinforcement (dopaminergic reward or
  serotonergic nociceptive shock).
- Enables real-time biological associative learning without backpropagation or artificial loss gradients.
"""

from typing import Any

import numpy as np


class VerticalLobeAssociativeMemory:
    """Associative memory matrix of the octopus Vertical Lobe with presynaptic LTP/LTD."""

    def __init__(
        self,
        n_sfl_inputs: int = 16,  # Superior Frontal Lobe sensory afferents (visual/chemo)
        n_amacrine_fibers: int = 128,  # Vertical Lobe parallel amacrine interneurons
        n_efferent_outputs: int = 4,  # Large efferent output neurons (e.g. Attack, Retract, Sucker Grip, Camouflage)
        initial_weight: float = 0.25,
        ltp_learning_rate: float = 0.08,
        ltd_depression_rate: float = 0.02,
        seed: int = 42,
    ):
        self.rng = np.random.RandomState(seed)
        self.n_in = n_sfl_inputs
        self.n_ama = n_amacrine_fibers
        self.n_out = n_efferent_outputs
        self.eta_ltp = ltp_learning_rate
        self.eta_ltd = ltd_depression_rate

        # 1. SFL -> Amacrine projection (Sparse, random biological expansion)
        # Each amacrine cell receives a sparse subset of SFL afferents (~4 inputs)
        self.w_sfl_ama = np.zeros((self.n_ama, self.n_in), dtype=np.float32)
        for i in range(self.n_ama):
            selected = self.rng.choice(self.n_in, size=min(4, self.n_in), replace=False)
            self.w_sfl_ama[i, selected] = self.rng.uniform(0.5, 1.0, size=len(selected))

        # 2. Amacrine -> Efferent matrix (Plastic, presynaptic LTP/LTD site)
        # Initialized with baseline synaptic weights W_ij
        self.w_ama_eff = np.full((self.n_out, self.n_ama), initial_weight, dtype=np.float32)

        # Internal state tracking
        self.last_sfl_activity = np.zeros(self.n_in, dtype=np.float32)
        self.last_amacrine_activity = np.zeros(self.n_ama, dtype=np.float32)
        self.last_efferent_activity = np.zeros(self.n_out, dtype=np.float32)

        # Plasticity history
        self.ltp_event_count: int = 0
        self.ltd_event_count: int = 0

    def reset(self):
        """Clears transient neural activities (weights remain intact)."""
        self.last_sfl_activity.fill(0.0)
        self.last_amacrine_activity.fill(0.0)
        self.last_efferent_activity.fill(0.0)

    def forward(self, sfl_cues: np.ndarray) -> np.ndarray:
        """Propagates sensory cues through the Vertical Lobe matrix.

        Args:
            sfl_cues: Array of shape (n_sfl_inputs,) representing visual and chemotactile features.

        Returns:
            efferent_activity: Array of shape (n_efferent_outputs,) driving motor decisions.
        """
        self.last_sfl_activity = np.clip(np.array(sfl_cues, dtype=np.float32), 0.0, 1.0)

        # Amacrine fiber activation with thresholding non-linearity
        raw_ama = np.dot(self.w_sfl_ama, self.last_sfl_activity)
        # Sparse Amacrine activation (k-winners-take-all / biological threshold)
        threshold = float(np.mean(raw_ama))
        self.last_amacrine_activity = np.maximum(0.0, raw_ama - threshold)
        norm = np.linalg.norm(self.last_amacrine_activity)
        if norm > 1e-6:
            self.last_amacrine_activity /= norm

        # Efferent output activation (dot product with plastic synaptic weights)
        self.last_efferent_activity = np.dot(self.w_ama_eff, self.last_amacrine_activity)
        return self.last_efferent_activity.copy()

    def apply_reinforcement(
        self,
        reward_dopamine: float = 0.0,  # Positive reward (e.g. food capture) -> LTP
        punishment_serotonin: float = 0.0,  # Negative reinforcement (e.g. predator bite/shock) -> LTD / Avoidance
        target_action_idx: int | None = None,
    ):
        """Applies Cephalopod LTP/LTD synaptic plasticity to the Vertical Lobe.

        Args:
            reward_dopamine: Amplitude of dopaminergic reinforcement [0.0, 1.0].
            punishment_serotonin: Amplitude of serotonergic nociceptive signal [0.0, 1.0].
            target_action_idx: Index of the efferent output associated with the behavior.
        """
        if target_action_idx is None:
            target_action_idx = int(np.argmax(self.last_efferent_activity))

        ama_pre = self.last_amacrine_activity

        # 1. Presynaptic Long-Term Potentiation (LTP) upon food reward
        if reward_dopamine > 0.0:
            delta_w = self.eta_ltp * reward_dopamine * ama_pre
            self.w_ama_eff[target_action_idx] += delta_w
            self.ltp_event_count += 1

        # 2. Long-Term Depression (LTD) / Avoidance remodeling upon shock
        if punishment_serotonin > 0.0:
            delta_w = self.eta_ltd * punishment_serotonin * ama_pre
            self.w_ama_eff[target_action_idx] = np.maximum(
                0.01, self.w_ama_eff[target_action_idx] - delta_w
            )
            self.ltd_event_count += 1

        # Biological upper bound saturation
        self.w_ama_eff = np.clip(self.w_ama_eff, 0.01, 2.5)

    def get_synaptic_stats(self) -> dict[str, Any]:
        """Returns statistics of the plastic Vertical Lobe matrix."""
        return {
            "mean_synaptic_strength": float(np.mean(self.w_ama_eff)),
            "max_synaptic_strength": float(np.max(self.w_ama_eff)),
            "min_synaptic_strength": float(np.min(self.w_ama_eff)),
            "total_ltp_inductions": self.ltp_event_count,
            "total_ltd_inductions": self.ltd_event_count,
        }
