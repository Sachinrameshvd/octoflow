"""Stereotypic Bend Propagation Motor Wave Controller.

Implements the biological cephalopod reaching mechanics discovered by
Y. Gutfreund, T. Flash, and B. Hochner (1996, 1998, 2005):
- Octopuses do not solve multi-joint inverse kinematics centrally.
- Instead, the central brain sends a single trigger command: (target_heading, bend_amplitude).
- The arm's brachial axial nerve cord generates an autonomous traveling muscle contraction wave
  propagating from base to tip at an invariant velocity (~1.5 to 3.0 m/s).
- The traveling bend stiffens the arm dynamically and pushes the arm tip directly toward the target
  while satisfying the muscular hydrostat constant-volume constraint: V = pi * r^2 * L = const.
"""

import numpy as np


class StereotypicBendWaveController:
    """Simulates biological traveling bend waves along cephalopod muscular hydrostat tentacles."""

    def __init__(
        self,
        n_segments: int = 5,
        conduction_velocity_ms: float = 2.2,  # Biological wave speed (~2.2 m/s)
        arm_nominal_length_m: float = 0.5,  # 50 cm arm
        dt_sec: float = 0.02,  # Physics tick (20 ms)
    ):
        self.n_segments = n_segments
        self.v_wave = conduction_velocity_ms
        self.arm_length = arm_nominal_length_m
        self.dt = dt_sec
        self.seg_spacing = arm_nominal_length_m / n_segments

        # Wave propagation state per arm
        # wave_progress: distance traveled by the bend wave peak along the arm (meters)
        self.wave_progress = np.full(8, -1.0, dtype=np.float32)  # -1.0 = quiescent
        self.wave_active = np.zeros(8, dtype=bool)
        self.wave_heading_theta = np.zeros(8, dtype=np.float32)
        self.wave_heading_phi = np.zeros(8, dtype=np.float32)
        self.wave_amplitude = np.zeros(8, dtype=np.float32)

    def trigger_reach(
        self,
        arm_idx: int,
        target_pitch_theta: float,
        target_yaw_phi: float,
        amplitude: float = 1.0,
    ):
        """Triggers an autonomous reaching bend wave on a specific arm.

        Args:
            arm_idx: Index of the arm (0 to 7).
            target_pitch_theta: Heading pitch angle (-1.0 to 1.0).
            target_yaw_phi: Heading yaw angle (-1.0 to 1.0).
            amplitude: Strike intensity (0.2 to 1.0).
        """
        self.wave_active[arm_idx] = True
        self.wave_progress[arm_idx] = 0.0  # Starts at arm base
        self.wave_heading_theta[arm_idx] = np.clip(target_pitch_theta, -1.0, 1.0)
        self.wave_heading_phi[arm_idx] = np.clip(target_yaw_phi, -1.0, 1.0)
        self.wave_amplitude[arm_idx] = np.clip(amplitude, 0.2, 1.0)

    def step(self) -> np.ndarray:
        """Advances wave propagation across all 8 arms by dt and calculates muscle activation deltas.

        Returns:
            actions: Array of shape (8, 4) continuous controls (d_theta, d_phi, d_elongate, suction).
        """
        actions = np.zeros((8, 4), dtype=np.float32)

        for arm_idx in range(8):
            if not self.wave_active[arm_idx]:
                continue

            # Advance bend peak along the arm
            self.wave_progress[arm_idx] += self.v_wave * self.dt
            current_dist = self.wave_progress[arm_idx]

            # Check if wave has reached the arm tip
            if current_dist > self.arm_length:
                self.wave_active[arm_idx] = False
                self.wave_progress[arm_idx] = -1.0
                # Arm tip reaches target; brief terminal suction activation
                actions[arm_idx, 3] = 1.0
                continue

            # Normalized position of the wave peak along the arm [0.0, 1.0]
            norm_pos = current_dist / self.arm_length

            # Spatial bell-shaped muscle contraction profile (Gaussian wave packet)
            # Produces the characteristic whip-like bend propagation
            wave_profile = float(np.exp(-((norm_pos - 0.5) ** 2) / 0.15))
            amp = self.wave_amplitude[arm_idx] * wave_profile

            # Directed bending commands
            d_th = float(self.wave_heading_theta[arm_idx] * amp)
            d_ph = float(self.wave_heading_phi[arm_idx] * amp)

            # Muscular hydrostat elongation wave: transverse muscle contraction causes
            # longitudinal elongation at the wave front
            d_elongate = float(amp * 0.8)

            actions[arm_idx] = [d_th, d_ph, d_elongate, 0.0]

        return actions
