"""Unit tests for ReachAndAvoid multi-arm gridworld environment."""

import numpy as np
from envs.reach_and_avoid import ReachAndAvoidEnv
from octopus_brain.config import EnvConfig


def test_env_initialization_and_reset():
    """Verify environment setup, reset shapes, and base placement."""
    config = EnvConfig(grid_size=14, n_arms=8, arm_reach=4)
    env = ReachAndAvoidEnv(config)

    obs, info = env.reset(seed=42)
    assert obs.shape == (8, 16)
    assert len(env.arm_bases) == 8
    assert len(env.arm_tips) == 8
    assert "joint_targets" in info


def test_env_step_mechanics():
    """Verify movements, actions, rewards, and constraints in environment step."""
    config = EnvConfig(grid_size=14, n_arms=6, max_steps=20)
    env = ReachAndAvoidEnv(config)

    obs, info = env.reset(seed=123)
    actions = np.array([1, 2, 3, 4, 0, 1])  # Discrete actions

    next_obs, rewards, term, trunc, step_info = env.step(actions)

    assert next_obs.shape == (6, 16)
    assert rewards.shape == (6,)
    assert not term
    assert not trunc
    assert "single_completed" in step_info
    assert "joint_completed" in step_info
    assert "hazard_hits" in step_info


def test_joint_task_detection_logic():
    """Verify ground truth joint-task detection when arms are near cooperative targets."""
    config = EnvConfig(grid_size=14, n_arms=8)
    env = ReachAndAvoidEnv(config)
    env.reset(seed=999)

    joint_pairs = env.get_active_joint_pairs()
    assert len(joint_pairs) > 0

    # Test physical active check
    for a, b in joint_pairs:
        active = env.is_joint_task_physically_active(a, b)
        assert isinstance(active, bool)
