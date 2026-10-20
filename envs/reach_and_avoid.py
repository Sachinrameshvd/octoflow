"""ReachAndAvoid: Multi-arm gridworld environment for distributed & cooperative control.

Environment layout:
- N arm bases arranged in a ring around an arena
- Each arm tip moves within reach radius of its base
- Local egocentric observation patch per arm
- Two distinct target types:
    1. Single-arm targets: Foraged independently by individual arms
    2. Joint-arm targets: Require two adjacent arms (i, i+1) to simultaneously act
- Dynamic hazards: Moving danger zones that must be avoided
- Delayed context cues: Supports long-horizon memory testing
"""

from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import torch

from octopus_brain.config import EnvConfig


class ReachAndAvoidEnv:
    """Toy multi-arm gridworld environment simulating octopus arm coordination."""

    def __init__(self, config: Optional[EnvConfig] = None):
        self.config = config or EnvConfig()
        self.grid_size = self.config.grid_size
        self.n_arms = self.config.n_arms
        self.arm_reach = self.config.arm_reach
        self.max_steps = self.config.max_steps
        self.obs_dim = 16  # Fixed feature vector dimension

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

        # Action deltas: 0: Stay/Interact, 1: Up, 2: Down, 3: Left, 4: Right
        self.action_deltas = np.array([
            [0, 0],    # Stay
            [0, 1],    # Up
            [0, -1],   # Down
            [-1, 0],   # Left
            [1, 0],    # Right
        ], dtype=np.float32)

        self.rng = np.random.RandomState(42)
        self.current_step = 0
        self.arm_tips = np.zeros((self.n_arms, 2), dtype=np.float32)
        self.single_targets: List[np.ndarray] = []
        self.joint_targets: List[Dict[str, Any]] = []
        self.hazards: List[np.ndarray] = []
        self.hazard_velocities: List[np.ndarray] = []
        self.delayed_context_cue = 0.0  # +1.0 or -1.0 global cue

    def seed(self, seed: Optional[int] = None) -> None:
        """Set random seed."""
        if seed is not None:
            self.rng = np.random.RandomState(seed)

    def _spawn_targets_and_hazards(self) -> None:
        """Spawn independent targets, joint targets, and moving hazards."""
        # 1. Single-arm targets: spawn 1 target within reach of several arm bases
        self.single_targets = []
        for i in range(self.config.n_single_targets):
            arm_idx = i % self.n_arms
            base = self.arm_bases[arm_idx]
            offset = self.rng.uniform(-self.arm_reach * 0.8, self.arm_reach * 0.8, size=2)
            pos = np.clip(base + offset, 0, self.grid_size - 1)
            self.single_targets.append(pos)

        # 2. Joint targets: spawn between adjacent arms (i, i+1)
        self.joint_targets = []
        for j in range(self.config.n_joint_targets):
            arm_a = (j * 2) % self.n_arms
            arm_b = (arm_a + 1) % self.n_arms
            # Midpoint between bases with slight radial jitter
            mid = (self.arm_bases[arm_a] + self.arm_bases[arm_b]) / 2.0
            jitter = self.rng.uniform(-0.5, 0.5, size=2)
            pos = np.clip(mid + jitter, 0, self.grid_size - 1)
            self.joint_targets.append({
                "pos": pos,
                "arms": (arm_a, arm_b),
                "active": True,
            })

        # 3. Hazards
        self.hazards = []
        self.hazard_velocities = []
        for _ in range(self.config.n_hazards):
            pos = self.rng.uniform(2, self.grid_size - 2, size=2)
            vel = self.rng.choice([-0.5, 0.5], size=2)
            self.hazards.append(pos)
            self.hazard_velocities.append(vel)

    def reset(self, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Reset environment to initial state."""
        if seed is not None:
            self.seed(seed)

        self.current_step = 0
        # Arm tips start at their bases
        self.arm_tips = self.arm_bases.copy()

        # Set delayed context cue (+1 or -1)
        self.delayed_context_cue = float(self.rng.choice([-1.0, 1.0]))

        self._spawn_targets_and_hazards()
        obs = self._get_observations()
        info = {
            "joint_targets": self.joint_targets,
            "joint_task_active_pairs": self.get_active_joint_pairs(),
        }
        return obs, info

    def get_active_joint_pairs(self) -> List[Tuple[int, int]]:
        """Return list of arm pairs (i, j) that currently have an active joint target near them."""
        active_pairs = []
        for jt in self.joint_targets:
            if jt["active"]:
                active_pairs.append(jt["arms"])
        return active_pairs

    def is_joint_task_physically_active(self, arm_a: int, arm_b: int) -> bool:
        """Ground-truth query: is a joint task currently requiring arm_a and arm_b coordination?"""
        pair = (min(arm_a, arm_b), max(arm_a, arm_b))
        for jt in self.joint_targets:
            if jt["active"]:
                jt_pair = (min(jt["arms"][0], jt["arms"][1]), max(jt["arms"][0], jt["arms"][1]))
                if pair == jt_pair:
                    # Check if either arm is close enough to target to trigger joint requirement
                    dist_a = np.linalg.norm(self.arm_tips[arm_a] - jt["pos"])
                    dist_b = np.linalg.norm(self.arm_tips[arm_b] - jt["pos"])
                    if dist_a <= self.arm_reach or dist_b <= self.arm_reach:
                        return True
        return False

    def _get_observations(self) -> np.ndarray:
        """Construct local egocentric observation vectors for all N arms.

        Each observation is a 16-dimensional vector:
        - [0:2]: Relative vector from arm tip to its base (dx, dy) / arm_reach
        - [2:4]: Relative vector to closest single-arm target (dx, dy) / grid_size
        - [4]: Distance to closest single-arm target / grid_size
        - [5:7]: Relative vector to closest joint target (dx, dy) / grid_size
        - [7]: Distance to closest joint target / grid_size
        - [8]: Is this arm assigned to the closest joint target? (1.0 or 0.0)
        - [9:11]: Relative vector to closest hazard (dx, dy) / grid_size
        - [11]: Distance to closest hazard / grid_size
        - [12:14]: Relative vector to left neighbor arm tip (i-1)
        - [14]: Relative vector to right neighbor arm tip (i+1) x-offset
        - [15]: Delayed contextual cue (visible only at t <= 2 if delayed_cue_mode)
        """
        obs = np.zeros((self.n_arms, self.obs_dim), dtype=np.float32)

        # Context cue visibility (flashes at t <= 2)
        cue_val = self.delayed_context_cue
        if self.config.delayed_cue_mode and self.current_step > 2:
            cue_val = 0.0

        for i in range(self.n_arms):
            tip = self.arm_tips[i]
            base = self.arm_bases[i]

            # 1. Base offset
            base_offset = (base - tip) / float(self.arm_reach)
            obs[i, 0:2] = np.clip(base_offset, -2.0, 2.0)

            # 2. Closest single-arm target
            if len(self.single_targets) > 0:
                dists_s = [np.linalg.norm(tip - st) for st in self.single_targets]
                min_idx_s = int(np.argmin(dists_s))
                st_offset = (self.single_targets[min_idx_s] - tip) / float(self.grid_size)
                obs[i, 2:4] = st_offset
                obs[i, 4] = dists_s[min_idx_s] / float(self.grid_size)
            else:
                obs[i, 2:5] = 0.0

            # 3. Closest joint target
            active_jts = [jt for jt in self.joint_targets if jt["active"]]
            if len(active_jts) > 0:
                dists_j = [np.linalg.norm(tip - jt["pos"]) for jt in active_jts]
                min_idx_j = int(np.argmin(dists_j))
                best_jt = active_jts[min_idx_j]
                jt_offset = (best_jt["pos"] - tip) / float(self.grid_size)
                obs[i, 5:7] = jt_offset
                obs[i, 7] = dists_j[min_idx_j] / float(self.grid_size)
                obs[i, 8] = 1.0 if (i in best_jt["arms"]) else 0.0
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

            # 5. Neighbor tips (left: i-1, right: i+1)
            left_tip = self.arm_tips[(i - 1) % self.n_arms]
            right_tip = self.arm_tips[(i + 1) % self.n_arms]
            obs[i, 12:14] = (left_tip - tip) / float(self.grid_size)
            obs[i, 14] = (right_tip[0] - tip[0]) / float(self.grid_size)

            # 6. Context cue
            obs[i, 15] = cue_val

        return obs

    def step(
        self, actions: Union[np.ndarray, torch.Tensor]
    ) -> Tuple[np.ndarray, np.ndarray, bool, bool, Dict[str, Any]]:
        """Execute one environment step.

        Args:
            actions: (N,) discrete actions in {0, 1, 2, 3, 4} for all N arms.

        Returns:
            (next_obs, rewards, terminated, truncated, info)
        """
        if isinstance(actions, torch.Tensor):
            actions = actions.detach().cpu().numpy()

        rewards = np.full(self.n_arms, self.config.step_penalty, dtype=np.float32)
        single_completed = 0
        joint_completed = 0
        hazard_hits = 0

        # 1. Update arm tip positions
        for i in range(self.n_arms):
            act = int(actions[i])
            delta = self.action_deltas[act]
            new_pos = self.arm_tips[i] + delta

            # Enforce arm physical reach constraint from base
            dist_to_base = np.linalg.norm(new_pos - self.arm_bases[i])
            if dist_to_base <= self.arm_reach:
                self.arm_tips[i] = np.clip(new_pos, 0, self.grid_size - 1)
            else:
                # Arm stretched to maximum reach
                direction = (new_pos - self.arm_bases[i]) / max(dist_to_base, 1e-4)
                self.arm_tips[i] = np.clip(
                    self.arm_bases[i] + direction * self.arm_reach, 0, self.grid_size - 1
                )

        # 2. Update dynamic hazards
        for k in range(len(self.hazards)):
            self.hazards[k] += self.hazard_velocities[k]
            # Bounce off arena walls
            for dim in [0, 1]:
                if self.hazards[k][dim] <= 1.0 or self.hazards[k][dim] >= self.grid_size - 1.0:
                    self.hazard_velocities[k][dim] *= -1.0
                    self.hazards[k][dim] = np.clip(self.hazards[k][dim], 1.0, self.grid_size - 1.0)

        # 3. Check Single-Arm Target Collections
        capture_radius = 1.2
        remaining_singles = []
        for st in self.single_targets:
            collected = False
            for i in range(self.n_arms):
                if np.linalg.norm(self.arm_tips[i] - st) <= capture_radius:
                    # In delayed cue mode, reward depends on cue consistency
                    cue_mult = 1.0
                    if self.config.delayed_cue_mode:
                        cue_mult = 1.0 if (self.delayed_context_cue > 0) else 0.5
                    rewards[i] += self.config.single_reward * cue_mult
                    collected = True
                    single_completed += 1
                    break
            if not collected:
                remaining_singles.append(st)

        # Respawn collected single targets
        while len(remaining_singles) < self.config.n_single_targets:
            arm_idx = self.rng.randint(0, self.n_arms)
            base = self.arm_bases[arm_idx]
            offset = self.rng.uniform(-self.arm_reach * 0.8, self.arm_reach * 0.8, size=2)
            pos = np.clip(base + offset, 0, self.grid_size - 1)
            remaining_singles.append(pos)
        self.single_targets = remaining_singles

        # 4. Check Joint-Arm Target Collections
        for jt in self.joint_targets:
            if not jt["active"]:
                continue
            arm_a, arm_b = jt["arms"]
            dist_a = np.linalg.norm(self.arm_tips[arm_a] - jt["pos"])
            dist_b = np.linalg.norm(self.arm_tips[arm_b] - jt["pos"])

            # Mutual coordination shaping bonus when both arms converge on joint target
            if dist_a <= self.arm_reach and dist_b <= self.arm_reach:
                coordination_potential = max(0.0, 5.0 - (dist_a + dist_b))
                rewards[arm_a] += 0.03 * coordination_potential
                rewards[arm_b] += 0.03 * coordination_potential

            if dist_a <= capture_radius and dist_b <= capture_radius:
                # Joint success! Both arms acted simultaneously
                rewards[arm_a] += self.config.cooperation_reward
                rewards[arm_b] += self.config.cooperation_reward
                joint_completed += 1
                # Respawn joint target
                mid = (self.arm_bases[arm_a] + self.arm_bases[arm_b]) / 2.0
                jitter = self.rng.uniform(-0.5, 0.5, size=2)
                jt["pos"] = np.clip(mid + jitter, 0, self.grid_size - 1)
            elif (dist_a <= capture_radius) ^ (dist_b <= capture_radius):
                # Uncoordinated attempt: only one arm arrived
                uncoord_arm = arm_a if (dist_a <= capture_radius) else arm_b
                rewards[uncoord_arm] += -0.05  # Slight penalty for uncoordinated push

        # 5. Check Hazard Collisions & Repulsive Proximity Potential
        hazard_radius = 1.0
        for h in self.hazards:
            for i in range(self.n_arms):
                dist_h = np.linalg.norm(self.arm_tips[i] - h)
                if dist_h <= hazard_radius:
                    rewards[i] += self.config.hazard_penalty
                    hazard_hits += 1
                elif dist_h < 2.0:
                    # Smooth repulsive artificial potential field: penalize approaching hazards
                    proximity_penalty = -0.25 * (2.0 - dist_h)
                    rewards[i] += proximity_penalty

        self.current_step += 1
        terminated = False
        truncated = self.current_step >= self.max_steps

        next_obs = self._get_observations()
        info = {
            "single_completed": single_completed,
            "single_target_hits": single_completed,
            "joint_completed": joint_completed,
            "joint_target_hits": joint_completed,
            "hazard_hits": hazard_hits,
            "hazard_collisions": hazard_hits,
            "active_joint_pairs": self.get_active_joint_pairs(),
            "joint_ground_truth": [
                self.is_joint_task_physically_active(i, (i + 1) % self.n_arms)
                for i in range(self.n_arms)
            ],
            "delayed_cue": self.delayed_context_cue,
        }

        return next_obs, rewards, terminated, truncated, info
