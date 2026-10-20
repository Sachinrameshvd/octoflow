"""Cephalopod Neuromodulation and Neuropeptide System.

Simulates key molluscan neuromodulators and neuropeptides governing brain state
and behavioral thresholds (Octopamine, FMRFamide, Dopamine, Serotonin):
- Octopamine: Invertebrate adrenergic analog; drives hunting arousal, alertness, and strike speed.
- FMRFamide: Key molluscan cardioactive/muscular peptide; modulates muscle tone and sucker grip force.
- Dopamine: Appetitive reinforcement; gates presynaptic Long-Term Potentiation (LTP) in the Vertical Lobe.
- Serotonin (5-HT): Defensive withdrawal, nociception, and synaptic depression (LTD).
"""

from typing import Dict, Any
import numpy as np


class CephalopodNeuromodulation:
    """Manages global and regional neuromodulatory states."""

    def __init__(
        self,
        decay_tau_sec: float = 5.0,
        dt_sec: float = 0.05,
    ):
        self.decay = float(np.exp(-dt_sec / decay_tau_sec))

        # Basal concentrations [0.0 to 1.0]
        self.octopamine: float = 0.1     # Arousal / hunting tone
        self.fmrfamide: float = 0.2      # Muscle contraction gain
        self.dopamine: float = 0.05      # Reward / LTP gate
        self.serotonin: float = 0.05     # Nociception / defensive withdrawal

    def update(self):
        """Decays transient surges back to basal levels."""
        self.octopamine = max(0.1, self.octopamine * self.decay)
        self.fmrfamide = max(0.2, self.fmrfamide * self.decay)
        self.dopamine = max(0.05, self.dopamine * self.decay)
        self.serotonin = max(0.05, self.serotonin * self.decay)

    def trigger_prey_detected(self, cue_strength: float = 0.8):
        """Surges octopamine and FMRFamide upon detecting edible prey."""
        self.octopamine = min(1.0, self.octopamine + 0.4 * cue_strength)
        self.fmrfamide = min(1.0, self.fmrfamide + 0.3 * cue_strength)

    def trigger_food_reward(self, reward_amplitude: float = 1.0):
        """Surges dopamine upon successfully ingesting food (triggers Vertical Lobe LTP)."""
        self.dopamine = min(1.0, self.dopamine + 0.6 * reward_amplitude)

    def trigger_predator_shock(self, shock_intensity: float = 1.0):
        """Surges serotonin upon predator contact (triggers withdrawal & LTD)."""
        self.serotonin = min(1.0, self.serotonin + 0.7 * shock_intensity)

    def get_motor_gain(self) -> float:
        """Returns muscular force multiplier modulated by FMRFamide and octopamine."""
        return float(1.0 + 0.8 * self.fmrfamide + 0.5 * (self.octopamine - 0.1))

    def get_state_dict(self) -> Dict[str, float]:
        """Returns current neuromodulatory profile."""
        return {
            "octopamine": round(self.octopamine, 3),
            "fmrfamide": round(self.fmrfamide, 3),
            "dopamine": round(self.dopamine, 3),
            "serotonin": round(self.serotonin, 3),
            "motor_gain": round(self.get_motor_gain(), 3),
        }
