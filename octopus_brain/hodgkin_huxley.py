"""Cephalopod Hodgkin-Huxley Multi-Channel Electrophysiology Engine.

Calibrated to squid and octopus giant axon electrophysiological recordings
(Hodgkin & Huxley 1952; Rosenthal & Gilly 1996):
- Fast voltage-gated inward Sodium channel (I_Na) with activation (m) and inactivation (h).
- Delayed-rectifier outward Potassium channel (I_K) with activation (n).
- Molluscan transient A-type Potassium channel (I_A) with activation (a) and inactivation (b)
  conferring spike-frequency adaptation and delay firing.
- Invertebrate temperature Q10 scaling factor adjusted for marine seawater (15°C - 18°C).
- Generates true biological continuous action potential waveforms (~100 mV peak-to-peak).
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np


class CephalopodHodgkinHuxley:
    """Multi-channel Hodgkin-Huxley electrophysiological simulator for cephalopod neurons."""

    def __init__(
        self,
        n_neurons: int,
        c_m_uf: float = 1.0,           # Membrane capacitance (uF/cm^2)
        g_na_max: float = 120.0,       # Maximal Sodium conductance (mS/cm^2)
        g_k_max: float = 36.0,         # Maximal Delayed Rectifier Potassium conductance (mS/cm^2)
        g_a_max: float = 20.0,         # Maximal A-type Potassium conductance (mS/cm^2)
        g_l: float = 0.3,              # Leak conductance (mS/cm^2)
        e_na_mv: float = 55.0,         # Sodium reversal potential (mV)
        e_k_mv: float = -77.0,         # Potassium reversal potential (mV)
        e_l_mv: float = -65.0,         # Leak reversal potential (mV)
        temp_celsius: float = 16.0,    # Seawater temperature (°C)
        dt_ms: float = 0.025,          # Integration time step (ms)
    ):
        self.n = n_neurons
        self.c_m = c_m_uf
        self.g_na_max = g_na_max
        self.g_k_max = g_k_max
        self.g_a_max = g_a_max
        self.g_l = g_l
        self.e_na = e_na_mv
        self.e_k = e_k_mv
        self.e_l = e_l_mv
        self.dt = dt_ms

        # Q10 temperature coefficient (base temp: 6.3°C from original squid axon data)
        self.phi = 3.0 ** ((temp_celsius - 6.3) / 10.0)

        # State vectors (resting initialization around -65 mV)
        self.v = np.full(self.n, -65.0, dtype=np.float32)
        self.m = np.zeros(self.n, dtype=np.float32)
        self.h = np.zeros(self.n, dtype=np.float32)
        self.n_gate = np.zeros(self.n, dtype=np.float32)
        self.a = np.zeros(self.n, dtype=np.float32)
        self.b = np.zeros(self.n, dtype=np.float32)

        # Initialize gating variables to resting steady-state
        self._init_steady_state()

        # Telemetry
        self.time_ms: float = 0.0
        self.spike_threshold_mv: float = 0.0
        self.last_v = self.v.copy()
        self.spike_history: List[Tuple[float, int]] = []

    def _alpha_m(self, v: np.ndarray) -> np.ndarray:
        v_diff = -(v + 40.0)
        return self.phi * np.where(np.abs(v_diff) < 1e-4, 1.0, 0.1 * v_diff / (np.exp(v_diff / 10.0) - 1.0))

    def _beta_m(self, v: np.ndarray) -> np.ndarray:
        return self.phi * 4.0 * np.exp(-(v + 65.0) / 18.0)

    def _alpha_h(self, v: np.ndarray) -> np.ndarray:
        return self.phi * 0.07 * np.exp(-(v + 65.0) / 20.0)

    def _beta_h(self, v: np.ndarray) -> np.ndarray:
        return self.phi / (np.exp(-(v + 35.0) / 10.0) + 1.0)

    def _alpha_n(self, v: np.ndarray) -> np.ndarray:
        v_diff = -(v + 55.0)
        return self.phi * np.where(np.abs(v_diff) < 1e-4, 0.1, 0.01 * v_diff / (np.exp(v_diff / 10.0) - 1.0))

    def _beta_n(self, v: np.ndarray) -> np.ndarray:
        return self.phi * 0.125 * np.exp(-(v + 65.0) / 80.0)

    # Invertebrate A-type transient Potassium channel gates
    def _a_inf(self, v: np.ndarray) -> np.ndarray:
        return (0.0761 * np.exp((v + 94.22) / 31.84) / (1.0 + np.exp((v + 1.17) / 28.93))) ** (1.0 / 3.0)

    def _b_inf(self, v: np.ndarray) -> np.ndarray:
        return (1.0 / (1.0 + np.exp((v + 53.3) / 14.54))) ** 4.0

    def _tau_a(self, v: np.ndarray) -> np.ndarray:
        return 0.3632 + 1.158 / (1.0 + np.exp((v + 55.96) / 20.12))

    def _tau_b(self, v: np.ndarray) -> np.ndarray:
        return 1.24 + 2.678 / (1.0 + np.exp((v + 50.0) / 16.027))

    def _init_steady_state(self):
        v = self.v
        am, bm = self._alpha_m(v), self._beta_m(v)
        ah, bh = self._alpha_h(v), self._beta_h(v)
        an, bn = self._alpha_n(v), self._beta_n(v)

        self.m = am / (am + bm)
        self.h = ah / (ah + bh)
        self.n_gate = an / (an + bn)
        self.a = self._a_inf(v)
        self.b = self._b_inf(v)

    def reset(self):
        """Resets membrane potential and gating states."""
        self.v.fill(-65.0)
        self._init_steady_state()
        self.last_v = self.v.copy()
        self.time_ms = 0.0
        self.spike_history.clear()

    def step(self, i_inj_ua: Optional[np.ndarray] = None) -> np.ndarray:
        """Advances membrane potentials and gating states by dt_ms.

        Args:
            i_inj_ua: Injected current per neuron in uA/cm^2.

        Returns:
            spikes: Boolean array of shape (N,) indicating action potential peaks.
        """
        if i_inj_ua is None:
            i_inj_ua = np.zeros(self.n, dtype=np.float32)

        v = self.v

        # Rate constants
        am, bm = self._alpha_m(v), self._beta_m(v)
        ah, bh = self._alpha_h(v), self._beta_h(v)
        an, bn = self._alpha_n(v), self._beta_n(v)

        # Update gating variables via exponential Euler
        dm = am * (1.0 - self.m) - bm * self.m
        dh = ah * (1.0 - self.h) - bh * self.h
        dn = an * (1.0 - self.n_gate) - bn * self.n_gate

        a_inf = self._a_inf(v)
        b_inf = self._b_inf(v)
        tau_a = self._tau_a(v)
        tau_b = self._tau_b(v)
        da = (a_inf - self.a) / tau_a
        db = (b_inf - self.b) / tau_b

        self.m += self.dt * dm
        self.h += self.dt * dh
        self.n_gate += self.dt * dn
        self.a += self.dt * da
        self.b += self.dt * db

        # Compute ionic currents
        i_na = self.g_na_max * (self.m ** 3) * self.h * (v - self.e_na)
        i_k = self.g_k_max * (self.n_gate ** 4) * (v - self.e_k)
        i_a = self.g_a_max * (self.a ** 3) * self.b * (v - self.e_k)
        i_leak = self.g_l * (v - self.e_l)

        # Membrane potential integration
        dv = (self.dt / self.c_m) * (i_inj_ua - i_na - i_k - i_a - i_leak)
        self.v += dv

        # Spike detection: positive crossing of threshold 0 mV
        spikes = (self.last_v < self.spike_threshold_mv) & (self.v >= self.spike_threshold_mv)
        self.last_v = self.v.copy()
        self.time_ms += self.dt

        for nid in np.where(spikes)[0]:
            self.spike_history.append((self.time_ms, int(nid)))

        return spikes
