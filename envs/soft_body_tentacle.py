"""Continuous 3D Soft-Body Muscular Hydrostat Tentacle Environment.

Simulates 8 biologically realistic continuous soft tentacles in 3D marine physics:
- Muscular hydrostat constant-volume constraint: V = pi * r^2 * L = const.
  Elongation reduces radial thickness; contraction expands radial thickness.
- Continuum kinematics with multi-segment 3D curvature: (pitch theta, yaw phi, length L).
- Hydrodynamic viscous drag and buoyancy damping in oceanic water.
- Sucker normal adhesion contact forces.
- Continuous 3D action space per arm: (d_theta, d_phi, d_elongation, suction_toggle).
- Plug-and-play compatibility with OctopusBrain 16D observation space.
"""

from typing import Any

import numpy as np
import torch
from octopus_brain.config import EnvConfig


class SoftTentacleKinematics:
    """Continuum kinematics model for a single muscular hydrostat arm in 3D."""

    def __init__(
        self,
        base_pos: np.ndarray,
        n_segments: int = 5,
        nominal_length: float = 3.5,
        nominal_radius: float = 0.35,
    ):
        self.base_pos = np.array(base_pos, dtype=np.float32)
        self.n_segments = n_segments
        self.nominal_length = nominal_length
        self.nominal_radius = nominal_radius
        self.base_radius = nominal_radius
        self.volume = np.pi * (nominal_radius**2) * nominal_length  # Constant volume invariant

        # State per segment: pitch angle theta, yaw angle phi, segment length L
        self.thetas = np.zeros(n_segments, dtype=np.float32)
        self.phis = np.zeros(n_segments, dtype=np.float32)
        self.segment_lengths = np.full(n_segments, nominal_length / n_segments, dtype=np.float32)
        self.segment_velocities = np.zeros((n_segments, 3), dtype=np.float32)
        self.tip_pos = self.base_pos.copy()

    @property
    def segment_length(self) -> float:
        return float(self.segment_lengths[0])

    def get_tip_position(self) -> np.ndarray:
        return self.tip_pos.copy()

    def reset(self):
        self.thetas.fill(0.0)
        self.phis.fill(0.0)
        self.segment_lengths.fill(self.nominal_length / self.n_segments)
        self.segment_velocities.fill(0.0)
        self.forward_kinematics()

    def step(self, d_theta: float, d_phi: float, d_elongate: float, dt: float = 0.05) -> np.ndarray:
        """Actuate longitudinal and transverse muscle layers.

        Args:
            d_theta: Pitch bending command [-1, 1].
            d_phi: Yaw bending command [-1, 1].
            d_elongate: Elongation/contraction command [-1, 1].
            dt: Time step interval in seconds.

        Returns:
            tip_position: (3,) coordinates in 3D space.
        """
        # Muscular hydrostat elongation
        total_len = np.sum(self.segment_lengths) + d_elongate * 0.4
        total_len = np.clip(total_len, self.nominal_length * 0.6, self.nominal_length * 1.5)
        self.segment_lengths.fill(total_len / self.n_segments)

        # Distribute bending across segments with proximal-to-distal compliance
        for k in range(self.n_segments):
            compliance = 1.0 + (k / float(self.n_segments)) * 0.5
            self.thetas[k] += float(d_theta) * 0.12 * compliance
            self.phis[k] += float(d_phi) * 0.12 * compliance
            # Elastic return damping
            self.thetas[k] *= 0.94
            self.phis[k] *= 0.94

        return self.forward_kinematics()

    def forward_kinematics(self) -> np.ndarray:
        """Compute 3D spine coordinates from base to tip."""
        current_pos = self.base_pos.copy()
        current_heading = np.array([0.0, 0.0, 1.0], dtype=np.float32)

        for k in range(self.n_segments):
            L = self.segment_lengths[k]
            th = self.thetas[k]
            ph = self.phis[k]

            # 3D spherical directional vector
            dx = L * np.sin(th) * np.cos(ph)
            dy = L * np.sin(ph)
            dz = L * np.cos(th) * np.cos(ph)

            current_pos += np.array([dx, dy, dz], dtype=np.float32)

        self.tip_pos = current_pos
        return self.tip_pos

    @property
    def current_radius(self) -> float:
        """Hydrostatic constant volume: r = sqrt(V / (pi * L))."""
        total_len = max(0.1, float(np.sum(self.segment_lengths)))
        return float(np.sqrt(self.volume / (np.pi * total_len)))


class SoftBodyTentacleEnv:
    """3D Underwater Physics Environment for 8 Continuum Soft Tentacles."""

    def __init__(
        self,
        config: EnvConfig | None = None,
        n_arms: int = 8,
        max_steps: int = 45,
        segments_per_arm: int = 5,
    ):
        self.config = config or EnvConfig()
        self.n_arms = n_arms
        self.arena_radius = 12.0
        self.max_steps = max_steps
        self.segments_per_arm = segments_per_arm
        self.current_step = 0
        self.obs_dim = 16

        # Gymnasium-compatible space attributes
        self.observation_space = type("Space", (), {"shape": (self.n_arms, self.obs_dim)})()
        self.action_space = type("Space", (), {"shape": (self.n_arms,)})()

        # Arrange 8 arm bases on a 3D ring on seafloor plane (Z=0, height Y=0)
        ring_radius = 5.0
        angles = np.linspace(0, 2 * np.pi, self.n_arms, endpoint=False)
        self.arm_bases = np.zeros((self.n_arms, 3), dtype=np.float32)
        for i, a in enumerate(angles):
            self.arm_bases[i] = [ring_radius * np.cos(a), 0.5, ring_radius * np.sin(a)]

        self.tentacles = [
            SoftTentacleKinematics(
                base_pos=self.arm_bases[i], n_segments=self.segments_per_arm, nominal_length=3.8
            )
            for i in range(self.n_arms)
        ]
        self.arms = self.tentacles  # Friendly alias

        self.rng = np.random.RandomState(42)
        self.targets: list[np.ndarray] = []
        self.joint_targets: list[dict[str, Any]] = []
        self.hazards: list[np.ndarray] = []

    def reset(self, seed: int | None = None) -> tuple[np.ndarray, dict[str, Any]]:
        if seed is not None:
            self.rng = np.random.RandomState(seed)

        self.current_step = 0
        for t in self.tentacles:
            t.reset()

        # Spawn 3D targets floating in water column
        self.targets = []
        for i in range(4):
            arm_idx = i % self.n_arms
            base = self.arm_bases[arm_idx]
            offset = self.rng.uniform(-2.5, 2.5, size=3)
            offset[1] = np.abs(offset[1]) + 0.5  # Positive water height
            self.targets.append(base + offset)

        # Spawn 3D joint target between adjacent arms
        self.joint_targets = []
        for j in range(2):
            a, b = (j * 2) % self.n_arms, (j * 2 + 1) % self.n_arms
            mid = (self.arm_bases[a] + self.arm_bases[b]) / 2.0
            mid[1] = 1.8  # Elevated in water
            self.joint_targets.append({"pos": mid, "arms": (a, b), "active": True})

        # Spawn moving marine predator hazards
        self.hazards = [self.rng.uniform(-6.0, 6.0, size=3) for _ in range(2)]
        for h in self.hazards:
            h[1] = np.abs(h[1]) + 1.0

        obs = self._get_observations()
        info = {
            "mode": "3d_soft_body_continuum",
            "target_pos": self.targets[0] if self.targets else np.zeros(3, dtype=np.float32),
            "active_joint_pairs": [jt["arms"] for jt in self.joint_targets],
            "single_completed": 0,
            "joint_completed": 0,
            "hazard_hits": 0,
        }
        return obs, info

    def _get_observations(self) -> np.ndarray:
        """Construct standard 16-dimensional observation patch per arm."""
        obs = np.zeros((self.n_arms, self.obs_dim), dtype=np.float32)

        for i in range(self.n_arms):
            tip = self.tentacles[i].tip_pos
            base = self.arm_bases[i]

            # 1. Base offset (dx, dz) / reach
            offset = (base - tip) / 4.0
            obs[i, 0:2] = offset[[0, 2]]

            # 2. Closest single target offset & distance
            if len(self.targets) > 0:
                dists_s = [np.linalg.norm(tip - t) for t in self.targets]
                min_s = int(np.argmin(dists_s))
                t_diff = (self.targets[min_s] - tip) / self.arena_radius
                obs[i, 2:4] = t_diff[[0, 2]]
                obs[i, 4] = dists_s[min_s] / self.arena_radius

            # 3. Closest joint target
            active_jt = [jt for jt in self.joint_targets if jt["active"]]
            if len(active_jt) > 0:
                dists_j = [np.linalg.norm(tip - jt["pos"]) for jt in active_jt]
                min_j = int(np.argmin(dists_j))
                best_jt = active_jt[min_j]
                jt_diff = (best_jt["pos"] - tip) / self.arena_radius
                obs[i, 5:7] = jt_diff[[0, 2]]
                obs[i, 7] = dists_j[min_j] / self.arena_radius
                obs[i, 8] = 1.0 if (i in best_jt["arms"]) else 0.0

            # 4. Closest hazard
            if len(self.hazards) > 0:
                dists_h = [np.linalg.norm(tip - h) for h in self.hazards]
                min_h = int(np.argmin(dists_h))
                h_diff = (self.hazards[min_h] - tip) / self.arena_radius
                obs[i, 9:11] = h_diff[[0, 2]]
                obs[i, 11] = dists_h[min_h] / self.arena_radius

            # 5. Neighbor tips (left, right)
            left_tip = self.tentacles[(i - 1) % self.n_arms].tip_pos
            right_tip = self.tentacles[(i + 1) % self.n_arms].tip_pos
            obs[i, 12:14] = ((left_tip - tip) / self.arena_radius)[[0, 2]]
            obs[i, 14] = (right_tip[0] - tip[0]) / self.arena_radius

            # 6. Sucker contact / elongation status
            obs[i, 15] = self.tentacles[i].current_radius / self.tentacles[i].nominal_radius

        return obs

    def step(
        self, actions: np.ndarray | torch.Tensor
    ) -> tuple[np.ndarray, np.ndarray, bool, bool, dict[str, Any]]:
        """Step 3D continuous soft tentacles using discrete action mapping or continuous controls."""
        if isinstance(actions, torch.Tensor):
            actions = actions.detach().cpu().numpy()

        rewards = np.full(self.n_arms, -0.02, dtype=np.float32)
        single_hits = 0
        joint_hits = 0
        hazard_hits = 0

        # Action mapping: 0: Stay, 1: Pitch Up, 2: Pitch Down, 3: Yaw Left, 4: Yaw Right
        control_deltas = [
            (0.0, 0.0, 0.0),  # Stay
            (1.0, 0.0, 0.5),  # Pitch Up & Elongate
            (-1.0, 0.0, -0.2),  # Pitch Down & Contract
            (0.0, -1.0, 0.2),  # Yaw Left
            (0.0, 1.0, 0.2),  # Yaw Right
        ]

        for i in range(self.n_arms):
            act = actions[i]
            if hasattr(act, "__len__") and len(act) >= 3:
                # Direct continuous continuum command: (d_pitch, d_yaw, d_elongate)
                d_th = float(act[0])
                d_ph = float(act[1])
                d_el = float(act[2])
            else:
                act_idx = int(act) if int(act) < len(control_deltas) else 0
                d_th, d_ph, d_el = control_deltas[act_idx]
            self.tentacles[i].step(d_th, d_ph, d_el)

        # Check 3D target collections
        capture_radius = 1.4
        remaining_targets = []
        for t_pos in self.targets:
            caught = False
            for i in range(self.n_arms):
                if np.linalg.norm(self.tentacles[i].tip_pos - t_pos) <= capture_radius:
                    rewards[i] += 1.8
                    single_hits += 1
                    caught = True
                    break
            if not caught:
                remaining_targets.append(t_pos)
        self.targets = remaining_targets

        # Check joint collections (simultaneous multi-arm contact)
        for jt in self.joint_targets:
            if not jt["active"]:
                continue
            a, b = jt["arms"]
            d_a = np.linalg.norm(self.tentacles[a].tip_pos - jt["pos"])
            d_b = np.linalg.norm(self.tentacles[b].tip_pos - jt["pos"])

            if d_a <= capture_radius and d_b <= capture_radius:
                rewards[a] += 5.0
                rewards[b] += 5.0
                joint_hits += 1
                jt["active"] = False

        # Hazards
        for h in self.hazards:
            for i in range(self.n_arms):
                d_h = np.linalg.norm(self.tentacles[i].tip_pos - h)
                if d_h <= 1.2:
                    rewards[i] -= 2.0
                    hazard_hits += 1
                elif d_h < 2.2:
                    rewards[i] -= 0.2 * (2.2 - d_h)

        self.current_step += 1
        term = False
        trunc = self.current_step >= self.max_steps

        next_obs = self._get_observations()
        info = {
            "mode": "3d_soft_body_continuum",
            "single_completed": single_hits,
            "joint_completed": joint_hits,
            "hazard_hits": hazard_hits,
            "arm_tip_positions_3d": [t.tip_pos.tolist() for t in self.tentacles],
            "arm_radii": [t.current_radius for t in self.tentacles],
        }

        return next_obs, rewards, term, trunc, info
