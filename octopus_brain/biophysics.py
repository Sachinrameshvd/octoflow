"""Biophysical Spiking & Conductance-Based Connectome Simulation Engine.

Simulates the cephalopod connectome using biologically realistic dynamics:
- Leaky Integrate-and-Fire (LIF) equations with explicit membrane time constants (tau_m).
- Conductance-based synaptic integration with separate excitatory (AMPA/ACh) and
  inhibitory (GABA/Glutamate) reversal potentials.
- Absolute refractory period tracking preventing unphysiological high-frequency bursts.
- Synaptic transmission with Dale's principle adherence and exponential decay.
- Voltage trace, spike raster, and instantaneous population firing rate tracking.
"""

from typing import Any

import numpy as np

from octopus_brain.connectome import CephalopodConnectome


class BiophysicalConnectomeSimulator:
    """Biophysical Leaky Integrate-and-Fire (LIF) network simulator on an identified connectome."""

    def __init__(
        self,
        connectome: CephalopodConnectome,
        dt_ms: float = 0.5,
        tau_m_ms: float = 20.0,
        tau_exc_ms: float = 5.0,
        tau_inh_ms: float = 10.0,
        v_rest_mv: float = -70.0,
        v_reset_mv: float = -75.0,
        v_thresh_mv: float = -50.0,
        e_exc_mv: float = 0.0,
        e_inh_mv: float = -80.0,
        refractory_period_ms: float = 2.0,
    ):
        self.connectome = connectome
        self.dt = dt_ms
        self.tau_m = tau_m_ms
        self.tau_exc = tau_exc_ms
        self.tau_inh = tau_inh_ms
        self.v_rest = v_rest_mv
        self.v_reset = v_reset_mv
        self.v_thresh = v_thresh_mv
        self.e_exc = e_exc_mv
        self.e_inh = e_inh_mv
        self.refractory_steps = int(np.ceil(refractory_period_ms / dt_ms))

        self.n_neurons = len(connectome.nodes)
        self.W = connectome.get_adjacency_matrix()  # (N, N) where W[i, j] is source j -> target i

        # Separate excitatory and inhibitory synaptic weight matrices
        self.W_exc = np.maximum(0.0, self.W)
        self.W_inh = np.maximum(0.0, -self.W)

        # State vectors
        self.v = np.full(self.n_neurons, self.v_rest, dtype=np.float32)
        self.g_exc = np.zeros(self.n_neurons, dtype=np.float32)
        self.g_inh = np.zeros(self.n_neurons, dtype=np.float32)
        self.refractory_timer = np.zeros(self.n_neurons, dtype=np.int32)
        self.last_spikes = np.zeros(self.n_neurons, dtype=bool)

        # Telemetry and recording
        self.current_time_ms: float = 0.0
        self.spike_history: list[tuple[float, int]] = []  # (time_ms, neuron_id)
        self.voltage_traces: dict[int, list[float]] = {}  # neuron_id -> trace
        self.time_points: list[float] = []

    def reset(self, randomize_v: bool = True):
        """Resets all membrane potentials and conductance states."""
        if randomize_v:
            self.v = self.v_rest + np.random.uniform(-3.0, 3.0, size=self.n_neurons).astype(
                np.float32
            )
        else:
            self.v.fill(self.v_rest)
        self.g_exc.fill(0.0)
        self.g_inh.fill(0.0)
        self.refractory_timer.fill(0)
        self.last_spikes.fill(False)
        self.current_time_ms = 0.0
        self.spike_history.clear()
        self.voltage_traces.clear()
        self.time_points.clear()

    def set_monitored_neurons(self, neuron_ids: list[int]):
        """Selects specific neuron IDs to record continuous membrane potential traces."""
        self.voltage_traces = {nid: [] for nid in neuron_ids}

    def step(self, external_currents: np.ndarray | None = None) -> np.ndarray:
        """Advances the biophysical network by a single time step dt.

        Args:
            external_currents: Array of shape (N,) injected currents (pA/mV equivalent).

        Returns:
            Boolean array of shape (N,) indicating which neurons spiked at this step.
        """
        if external_currents is None:
            external_currents = np.zeros(self.n_neurons, dtype=np.float32)

        # 1. Decay synaptic conductances
        decay_exc = np.exp(-self.dt / self.tau_exc)
        decay_inh = np.exp(-self.dt / self.tau_inh)
        self.g_exc *= decay_exc
        self.g_inh *= decay_inh

        # 2. Transmit spikes from previous step into target conductances
        spiking_indices = np.where(self.last_spikes)[0]
        if len(spiking_indices) > 0:
            # Synaptic conductances incremented by incoming weights
            delta_g_exc = self.W_exc[:, spiking_indices].sum(axis=1) * 0.05
            delta_g_inh = self.W_inh[:, spiking_indices].sum(axis=1) * 0.05
            self.g_exc += delta_g_exc
            self.g_inh += delta_g_inh

        # 3. Integrate membrane potential for non-refractory neurons
        is_refractory = self.refractory_timer > 0
        self.refractory_timer[is_refractory] -= 1

        active_mask = ~is_refractory
        # Conductance-based synaptic currents: I_syn = g_exc * (E_exc - V) + g_inh * (E_inh - V)
        i_exc = self.g_exc[active_mask] * (self.e_exc - self.v[active_mask])
        i_inh = self.g_inh[active_mask] * (self.e_inh - self.v[active_mask])
        i_leak = self.v_rest - self.v[active_mask]
        i_ext = external_currents[active_mask]

        dv = (self.dt / self.tau_m) * (i_leak + i_exc + i_inh) + (self.dt * i_ext)
        self.v[active_mask] += dv

        # Clamp refractory neurons at reset potential
        self.v[is_refractory] = self.v_reset

        # 4. Spike threshold crossing detection
        spikes = self.v >= self.v_thresh
        spiking_ids = np.where(spikes)[0]

        # Reset spiking neurons and set refractory timer
        self.v[spikes] = self.v_reset
        self.refractory_timer[spikes] = self.refractory_steps
        self.last_spikes = spikes

        # 5. Record telemetry
        self.current_time_ms += self.dt
        for sid in spiking_ids:
            self.spike_history.append((self.current_time_ms, int(sid)))

        if len(self.voltage_traces) > 0:
            self.time_points.append(self.current_time_ms)
            for nid in self.voltage_traces:
                self.voltage_traces[nid].append(float(self.v[nid]))

        return spikes

    def run_sim(self, duration_ms: float, current_stimulus_fn: Any | None = None) -> dict[str, Any]:
        """Runs the simulation for a given duration.

        Args:
            duration_ms: Total duration to simulate in milliseconds.
            current_stimulus_fn: Callable `f(t_ms) -> np.ndarray (N,)` injecting currents.
        """
        n_steps = int(np.ceil(duration_ms / self.dt))
        all_spikes = []

        for step_idx in range(n_steps):
            t_ms = self.current_time_ms
            i_ext = current_stimulus_fn(t_ms) if current_stimulus_fn else None
            spikes = self.step(i_ext)
            all_spikes.append(spikes)

        spike_matrix = np.array(all_spikes, dtype=bool)  # (T, N)
        return {
            "duration_ms": duration_ms,
            "total_spikes": len(self.spike_history),
            "mean_firing_rate_hz": (
                len(self.spike_history) / (self.n_neurons * (duration_ms / 1000.0))
            ),
            "spike_matrix": spike_matrix,
        }

    def get_population_firing_rates(self, time_window_ms: float = 50.0) -> dict[str, float]:
        """Computes instantaneous firing rate (Hz) grouped by brain regions."""
        cutoff_time = max(0.0, self.current_time_ms - time_window_ms)
        recent_spikes = [nid for (t, nid) in self.spike_history if t >= cutoff_time]

        spike_counts: dict[str, int] = {}
        for nid in recent_spikes:
            region = self.connectome.node_by_id[nid].region
            spike_counts[region] = spike_counts.get(region, 0) + 1

        window_sec = time_window_ms / 1000.0
        rates_hz: dict[str, float] = {}
        for region, node_ids in self.connectome.region_node_ids.items():
            n_cells = len(node_ids)
            total_spikes = spike_counts.get(region, 0)
            rates_hz[region] = round(total_spikes / (n_cells * window_sec), 2)

        return rates_hz
