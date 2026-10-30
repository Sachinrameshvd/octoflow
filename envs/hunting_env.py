"""CooperativeHuntingEnv: Dynamic multi-agent pursuit-evasion environment for OctopusBrain.

In this underwater reef environment:
- Fast evasive prey (crabs/fish) actively flee when a single arm approaches.
- Catching evasive prey requires multi-arm encirclement coalitions (e.g. 2-3 adjacent arms
  pinning the prey from complementary angles).
- Dynamic marine hazards (e.g. predatory moray eels / stingrays) move unpredictably.
- The environment conforms to the standard OctopusBrain observation (16D) and action (5D) spaces.
"""

from typing import Any

import numpy as np

# Optional torch import for environments; fallback to None if unavailable
try:
    import torch  # noqa: F401
except ImportError:
    torch = None

from octopus_brain.config import EnvConfig


class CooperativeHuntingEnv:
    """Cooperative multi-arm pursuit-evasion environment with intelligent fleeing prey."""

    def __init__(
        self,
        config: EnvConfig | None = None,
        prey_speed: float = 0.6,
        evasion_radius: float = 2.5,
        capture_radius: float = 1.3,
        encirclement_arms: int = 2,
    ):
        self.config = config or EnvConfig()
        self.grid_size = self.config.grid_size
        self.n_arms = self.config.n_arms
        self.arm_reach = self.config.arm_reach
        self.max_steps = self.config.max_steps
        self.obs_dim = 16  # Matches OctopusBrain local input

        self.prey_speed = prey_speed
        self.evasion_radius = evasion_radius
        self.capture_radius = capture_radius
        self.encirclement_arms = encirclement_arms

        # Precompute arm base positions on a ring
        center = self.grid_size / 2.0
        ring_radius = (self.grid_size / 2.0) - self.arm_reach - 0.5
        angles = np.linspace(0, 2 * np.pi, self.n_arms, endpoint=False)
        self.arm_bases = np.zeros((self.n_arms, 2), dtype=np.float32)
        for i, theta in enumerate(angles):
            self.arm_bases[i] = [
                center + ring_radius * np.cos(theta),
                center + ring_radius * np.sin(theta),
            ]

        # Action deltas: 0: Stay, 1: Up, 2: Down, 3: Left, 4: Right
        self.action_deltas = np.array(
            [
                [0.0, 0.0],
                [0.0, 1.0],
                [0.0, -1.0],
                [-1.0, 0.0],
                [1.0, 0.0],
            ],
            dtype=np.float32,
        )

        self.rng = np.random.RandomState(42)
        self.current_step = 0
        self.arm_tips = np.zeros((self.n_arms, 2), dtype=np.float32)

        # Entities
        self.solitary_prey: list[np.ndarray] = []
        self.evasive_prey: list[dict[str, Any]] = []
        self.hazards: list[np.ndarray] = []
        self.hazard_velocities: list[np.ndarray] = []

    def seed(self, seed: int | None = None) -> None:
        """Set random seed."""
        if seed is not None:
            self.rng = np.random.RandomState(seed)

    def _spawn_entities(self) -> None:
        """Spawn solitary prey, intelligent evasive prey, and moving hazards."""
        center = self.grid_size / 2.0

        # 1. Solitary prey (slower, caught by single arm)
        self.solitary_prey = []
        for i in range(self.config.n_single_targets):
            arm_idx = i % self.n_arms
            base = self.arm_bases[arm_idx]
            offset = self.rng.uniform(-self.arm_reach * 0.7, self.arm_reach * 0.7, size=2)
            pos = np.clip(base + offset, 1.0, self.grid_size - 2.0)
            self.solitary_prey.append(pos)

        # 2. Evasive cooperative prey (requires pincer encirclement)
        self.evasive_prey = []
        for j in range(self.config.n_joint_targets):
            arm_a = (j * 2) % self.n_arms
            arm_b = (arm_a + 1) % self.n_arms
            mid = (self.arm_bases[arm_a] + self.arm_bases[arm_b]) / 2.0
            jitter = self.rng.uniform(-0.6, 0.6, size=2)
            pos = np.clip(mid + jitter, 1.0, self.grid_size - 2.0)
            self.evasive_prey.append(
                {
                    "pos": pos.astype(np.float32),
                    "target_arms": (arm_a, arm_b),
                    "active": True,
                    "encircle_count": 0,
                }
            )

        # 3. Dynamic marine hazards (e.g. predators)
        self.hazards = []
        self.hazard_velocities = []
        for _ in range(self.config.n_hazards):
            pos = self.rng.uniform(2.0, self.grid_size - 2.0, size=2).astype(np.float32)
            vel = self.rng.choice([-0.6, 0.6], size=2).astype(np.float32)
            self.hazards.append(pos)
            self.hazard_velocities.append(vel)

    def reset(self, seed: int | None = None) -> tuple[np.ndarray, dict[str, Any]]:
        """Reset the environment to start a new hunting episode."""
        if seed is not None:
            self.seed(seed)

        self.current_step = 0
        self.arm_tips = self.arm_bases.copy()
        self._spawn_entities()
        obs = self._get_observations()
        info = {
            "evasive_prey": self.evasive_prey,
            "hunting_mode": "cooperative_pursuit",
        }
        return obs, info

    def _update_evasive_prey_movement(self) -> None:
        """Update prey AI: escape from nearby arms if not fully surrounded."""
        for prey in self.evasive_prey:
            if not prey["active"]:
                continue

            pos = prey["pos"]
            # Detect approaching arm tips
            dists = [np.linalg.norm(self.arm_tips[i] - pos) for i in range(self.n_arms)]
            close_arms = [i for i, d in enumerate(dists) if d <= self.evasion_radius]

            prey["encircle_count"] = len(close_arms)

            if len(close_arms) == 1:
                # Flee directly away from the single approaching arm
                arm_idx = close_arms[0]
                diff = pos - self.arm_tips[arm_idx]
                norm = np.linalg.norm(diff)
                if norm > 1e-4:
                    flee_dir = diff / norm
                    new_pos = pos + flee_dir * self.prey_speed
                    prey["pos"] = np.clip(new_pos, 1.0, self.grid_size - 2.0)
            elif len(close_arms) > 1:
                # Multiple arms closing in: if vectors cancel out, prey is cornered
                flee_vectors = []
                for arm_idx in close_arms:
                    diff = pos - self.arm_tips[arm_idx]
                    norm = np.linalg.norm(diff)
                    if norm > 1e-4:
                        flee_vectors.append(diff / norm)
                if len(flee_vectors) > 0:
                    net_flee = np.mean(flee_vectors, axis=0)
                    net_speed = np.linalg.norm(net_flee)
                    if net_speed > 0.4:
                        # Escape through gap
                        new_pos = pos + (net_flee / net_speed) * (self.prey_speed * 0.7)
                        prey["pos"] = np.clip(new_pos, 1.0, self.grid_size - 2.0)
                    # Else net_speed is small: arms have surrounded the prey from opposite sides!

    def _get_observations(self) -> np.ndarray:
        """Build 16D egocentric observations for all 8 arms."""
        obs = np.zeros((self.n_arms, self.obs_dim), dtype=np.float32)

        for i in range(self.n_arms):
            tip = self.arm_tips[i]
            base = self.arm_bases[i]

            # 1. Base offset
            base_offset = (base - tip) / float(self.arm_reach)
            obs[i, 0:2] = np.clip(base_offset, -2.0, 2.0)

            # 2. Closest solitary prey
            if len(self.solitary_prey) > 0:
                dists_s = [np.linalg.norm(tip - sp) for sp in self.solitary_prey]
                min_idx_s = int(np.argmin(dists_s))
                sp_offset = (self.solitary_prey[min_idx_s] - tip) / float(self.grid_size)
                obs[i, 2:4] = sp_offset
                obs[i, 4] = dists_s[min_idx_s] / float(self.grid_size)
            else:
                obs[i, 2:5] = 0.0

            # 3. Closest evasive cooperative prey
            active_evasive = [ep for ep in self.evasive_prey if ep["active"]]
            if len(active_evasive) > 0:
                dists_e = [np.linalg.norm(tip - ep["pos"]) for ep in active_evasive]
                min_idx_e = int(np.argmin(dists_e))
                best_ep = active_evasive[min_idx_e]
                ep_offset = (best_ep["pos"] - tip) / float(self.grid_size)
                obs[i, 5:7] = ep_offset
                obs[i, 7] = dists_e[min_idx_e] / float(self.grid_size)
                obs[i, 8] = 1.0 if (i in best_ep["target_arms"]) else 0.0
            else:
                obs[i, 5:9] = 0.0

            # 4. Closest hazard
            if len(self.hazards) > 0:
                dists_h = [np.linalg.norm(tip - h) for h in self.hazards]
                min_idx_h = int(np.argmin(dists_h))
                h_offset = (self.hazards[min_idx_h] - tip) / float(self.grid_size)
                obs[i, 9:11] = h_offset
                obs[i, 11] = dists_h[min_idx_h] / float(self.grid_size)
            else:
                obs[i, 9:12] = 0.0

            # 5. Neighbor arm tips (left: i-1, right: i+1)
            left_tip = self.arm_tips[(i - 1) % self.n_arms]
            right_tip = self.arm_tips[(i + 1) % self.n_arms]
            obs[i, 12:14] = (left_tip - tip) / float(self.grid_size)
            obs[i, 14] = (right_tip[0] - tip[0]) / float(self.grid_size)

            # 6. Environmental sensory cue
            obs[i, 15] = (
                1.0
                if (len(active_evasive) > 0 and active_evasive[0]["encircle_count"] >= 2)
                else 0.0
            )

        return obs

    def step(
        self, actions: np.ndarray | Any
    ) -> tuple[np.ndarray, np.ndarray, bool, bool, dict[str, Any]]:
        """Advance simulation by one time step."""
        if torch is not None and isinstance(actions, torch.Tensor):
            actions = actions.detach().cpu().numpy()

        rewards = np.full(self.n_arms, self.config.step_penalty, dtype=np.float32)
        single_completed = 0
        coop_captures = 0
        hazard_hits = 0

        # 1. Update arm tips
        for i in range(self.n_arms):
            act = int(actions[i])
            delta = self.action_deltas[act]
            new_pos = self.arm_tips[i] + delta

            dist_to_base = np.linalg.norm(new_pos - self.arm_bases[i])
            if dist_to_base <= self.arm_reach:
                self.arm_tips[i] = np.clip(new_pos, 0.0, self.grid_size - 1.0)
            else:
                direction = (new_pos - self.arm_bases[i]) / max(dist_to_base, 1e-4)
                self.arm_tips[i] = np.clip(
                    self.arm_bases[i] + direction * self.arm_reach, 0.0, self.grid_size - 1.0
                )

        # 2. Prey evasion update
        self._update_evasive_prey_movement()

        # 3. Dynamic hazards
        for k in range(len(self.hazards)):
            self.hazards[k] += self.hazard_velocities[k]
            for dim in [0, 1]:
                if self.hazards[k][dim] <= 1.0 or self.hazards[k][dim] >= self.grid_size - 1.0:
                    self.hazard_velocities[k][dim] *= -1.0
                    self.hazards[k][dim] = np.clip(self.hazards[k][dim], 1.0, self.grid_size - 1.0)

        # 4. Solitary prey captures
        remaining_solitary = []
        for sp in self.solitary_prey:
            caught = False
            for i in range(self.n_arms):
                if np.linalg.norm(self.arm_tips[i] - sp) <= self.capture_radius:
                    rewards[i] += self.config.single_reward
                    caught = True
                    single_completed += 1
                    break
            if not caught:
                remaining_solitary.append(sp)

        # Respawn solitary prey
        while len(remaining_solitary) < self.config.n_single_targets:
            arm_idx = self.rng.randint(0, self.n_arms)
            base = self.arm_bases[arm_idx]
            offset = self.rng.uniform(-self.arm_reach * 0.7, self.arm_reach * 0.7, size=2)
            pos = np.clip(base + offset, 1.0, self.grid_size - 2.0)
            remaining_solitary.append(pos)
        self.solitary_prey = remaining_solitary

        # 5. Cooperative evasive prey captures (requires encirclement)
        for ep in self.evasive_prey:
            if not ep["active"]:
                continue

            # Check how many arms are within capture radius
            close_arms = [
                i
                for i in range(self.n_arms)
                if np.linalg.norm(self.arm_tips[i] - ep["pos"]) <= self.capture_radius
            ]

            if len(close_arms) >= self.encirclement_arms:
                # Cooperative capture success! Distribute bounty to coalition
                for arm_idx in close_arms:
                    rewards[arm_idx] += self.config.cooperation_reward * 1.2
                coop_captures += 1

                # Respawn evasive prey
                arm_a = self.rng.randint(0, self.n_arms)
                arm_b = (arm_a + 1) % self.n_arms
                mid = (self.arm_bases[arm_a] + self.arm_bases[arm_b]) / 2.0
                jitter = self.rng.uniform(-0.6, 0.6, size=2)
                ep["pos"] = np.clip(mid + jitter, 1.0, self.grid_size - 2.0)
                ep["target_arms"] = (arm_a, arm_b)
            elif len(close_arms) == 1:
                # Lone arm attempt: penalty for scaring prey without coalition
                rewards[close_arms[0]] -= 0.05

        # 6. Hazards collisions & Repulsive Proximity Potential
        hazard_radius = 1.0
        for h in self.hazards:
            for i in range(self.n_arms):
                dist_h = np.linalg.norm(self.arm_tips[i] - h)
                if dist_h <= hazard_radius:
                    rewards[i] += self.config.hazard_penalty
                    hazard_hits += 1
                elif dist_h < 2.0:
                    # Smooth repulsive proximity penalty
                    proximity_penalty = -0.25 * (2.0 - dist_h)
                    rewards[i] += proximity_penalty

        self.current_step += 1
        terminated = False
        truncated = self.current_step >= self.max_steps

        next_obs = self._get_observations()
        info = {
            "single_completed": single_completed,
            "single_target_hits": single_completed,
            "joint_completed": coop_captures,
            "joint_target_hits": coop_captures,
            "coop_captures": coop_captures,
            "hazard_hits": hazard_hits,
            "hazard_collisions": hazard_hits,
            "hunting_mode": "cooperative_pursuit",
        }

        return next_obs, rewards, terminated, truncated, info
