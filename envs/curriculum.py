"""Curriculum Learning System for OctopusBrain.

Provides a progressive multi-stage curriculum that transitions the agent from
isolated motor control to multi-arm cooperative hunting under high hazard pressure:

- Stage 0 (Nursery): Pure foraging. 0 hazards, stationary targets, generous reach.
- Stage 1 (Reef): Standard Reach & Avoid. 3 hazards, 2 joint targets, sparse communication.
- Stage 2 (Pelagic Hunt): Dynamic pursuit with evasive fleeing prey, 4 moving hazards,
  and delayed context cues requiring central memory retention.
"""

from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
# Optional torch import for environments; fallback to None if unavailable
try:
    import torch  # noqa: F401
except ImportError:
    torch = None

from octopus_brain.config import EnvConfig
from envs.reach_and_avoid import ReachAndAvoidEnv
from envs.hunting_env import CooperativeHuntingEnv


class CurriculumScheduler:
    """Manages progression across progressive difficulty stages."""

    STAGE_NAMES = [
        "Stage 0: Nursery (Motor Control & Reaching)",
        "Stage 1: Reef (Standard Reach & Avoid)",
        "Stage 2: Pelagic Hunt (Cooperative Pursuit & Memory)",
    ]

    def __init__(
        self,
        window_size: int = 10,
        advance_reward_thresholds: Optional[List[float]] = None,
        max_hazard_thresholds: Optional[List[float]] = None,
    ):
        self.window_size = window_size
        self.stage = 0
        self.max_stage = 2
        # Thresholds to graduate from stage 0 -> 1, and 1 -> 2
        self.advance_reward_thresholds = advance_reward_thresholds or [8.0, 14.0]
        self.max_hazard_thresholds = max_hazard_thresholds or [1.0, 3.0]

        self.reward_history: List[float] = []
        self.hazard_history: List[float] = []
        self.stage_transitions: List[Dict[str, Any]] = []

    def record_episode(self, reward: float, hazard_hits: float, episode_idx: int) -> bool:
        """Record episode outcome and check if agent should graduate to next stage."""
        self.reward_history.append(reward)
        self.hazard_history.append(hazard_hits)

        if len(self.reward_history) > self.window_size:
            self.reward_history.pop(0)
            self.hazard_history.pop(0)

        # Check graduation
        if len(self.reward_history) >= self.window_size and self.stage < self.max_stage:
            mean_rew = float(np.mean(self.reward_history))
            mean_haz = float(np.mean(self.hazard_history))

            target_rew = self.advance_reward_thresholds[self.stage]
            max_haz = self.max_hazard_thresholds[self.stage]

            if mean_rew >= target_rew and mean_haz <= max_haz:
                self.stage += 1
                self.reward_history.clear()
                self.hazard_history.clear()
                self.stage_transitions.append({
                    "to_stage": self.stage,
                    "at_episode": episode_idx,
                    "mean_reward": mean_rew,
                    "mean_hazards": mean_haz,
                })
                return True
        return False

    def set_stage(self, stage: int) -> None:
        """Manually pin a curriculum stage."""
        self.stage = max(0, min(self.max_stage, stage))
        self.reward_history.clear()
        self.hazard_history.clear()

    @property
    def current_stage_name(self) -> str:
        return self.STAGE_NAMES[self.stage]


class CurriculumEnv:
    """Environment wrapper that dynamically switches environments and configs based on curriculum stage."""

    def __init__(
        self,
        base_config: Optional[EnvConfig] = None,
        scheduler: Optional[CurriculumScheduler] = None,
    ):
        self.base_config = base_config or EnvConfig()
        self.scheduler = scheduler or CurriculumScheduler()

        # Build environments for each stage
        # Stage 0: 0 hazards, 6 single targets, 2 joint targets, no penalties
        cfg_stage0 = EnvConfig(
            grid_size=self.base_config.grid_size,
            n_arms=self.base_config.n_arms,
            arm_reach=self.base_config.arm_reach,
            n_single_targets=6,
            n_joint_targets=2,
            n_hazards=0,
            max_steps=self.base_config.max_steps,
            step_penalty=-0.005,
            hazard_penalty=0.0,
        )
        self.env_stage0 = ReachAndAvoidEnv(cfg_stage0)

        # Stage 1: Standard Reach and Avoid
        self.env_stage1 = ReachAndAvoidEnv(self.base_config)

        # Stage 2: Cooperative Hunting with dynamic evasive prey and delayed context cue
        cfg_stage2 = EnvConfig(
            grid_size=self.base_config.grid_size,
            n_arms=self.base_config.n_arms,
            arm_reach=self.base_config.arm_reach,
            n_single_targets=3,
            n_joint_targets=3,
            n_hazards=4,
            max_steps=self.base_config.max_steps,
            delayed_cue_mode=True,
        )
        self.env_stage2 = CooperativeHuntingEnv(cfg_stage2, prey_speed=0.55, evasion_radius=2.5)

        self.envs = [self.env_stage0, self.env_stage1, self.env_stage2]

    @property
    def active_env(self) -> Union[ReachAndAvoidEnv, CooperativeHuntingEnv]:
        return self.envs[self.scheduler.stage]

    @property
    def n_arms(self) -> int:
        return self.active_env.n_arms

    @property
    def obs_dim(self) -> int:
        return self.active_env.obs_dim

    @property
    def max_steps(self) -> int:
        return self.active_env.max_steps

    @property
    def grid_size(self) -> int:
        return self.active_env.grid_size

    def seed(self, seed: Optional[int] = None) -> None:
        for e in self.envs:
            e.seed(seed)

    def reset(self, seed: Optional[int] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
        obs, info = self.active_env.reset(seed=seed)
        info["curriculum_stage"] = self.scheduler.stage
        info["curriculum_stage_name"] = self.scheduler.current_stage_name
        return obs, info

    def step(
        self, actions: Union[np.ndarray, Any]
    ) -> Tuple[np.ndarray, np.ndarray, bool, bool, Dict[str, Any]]:
        obs, rewards, term, trunc, info = self.active_env.step(actions)
        info["curriculum_stage"] = self.scheduler.stage
        info["curriculum_stage_name"] = self.scheduler.current_stage_name
        return obs, rewards, term, trunc, info
