"""Unit tests for CooperativeHuntingEnv."""

import numpy as np
import pytest

from octopus_brain.config import EnvConfig
from envs.hunting_env import CooperativeHuntingEnv


def test_hunting_env_initialization():
    env = CooperativeHuntingEnv()
    assert env.n_arms == 8
    assert env.obs_dim == 16
    assert len(env.arm_bases) == 8


def test_hunting_env_reset():
    env = CooperativeHuntingEnv()
    obs, info = env.reset(seed=123)
    assert obs.shape == (8, 16)
    assert "evasive_prey" in info
    assert info["hunting_mode"] == "cooperative_pursuit"
    assert len(env.solitary_prey) == env.config.n_single_targets
    assert len(env.evasive_prey) == env.config.n_joint_targets


def test_hunting_env_step_discrete():
    env = CooperativeHuntingEnv()
    obs, _ = env.reset(seed=42)

    # All STAY
    actions = np.zeros(8, dtype=int)
    next_obs, rewards, term, trunc, info = env.step(actions)

    assert next_obs.shape == (8, 16)
    assert rewards.shape == (8,)
    assert not term
    assert not trunc
    assert "coop_captures" in info


def test_hunting_env_prey_evasion_movement():
    env = CooperativeHuntingEnv(prey_speed=0.5, evasion_radius=3.0)
    env.reset(seed=10)

    # Place prey within arm 0 reach
    target_pos = env.arm_bases[0].copy() + np.array([1.5, 0.0], dtype=np.float32)
    env.evasive_prey[0]["pos"] = target_pos.copy()
    initial_prey_pos = target_pos.copy()

    # Place arm 0 tip within reach and within evasion radius of prey
    env.arm_tips[0] = target_pos - np.array([0.8, 0.0], dtype=np.float32)

    # Take step
    actions = np.zeros(8, dtype=int)
    env.step(actions)

    # Prey should have reacted and moved away from arm 0
    updated_prey_pos = env.evasive_prey[0]["pos"]
    assert not np.array_equal(initial_prey_pos, updated_prey_pos)


def test_hunting_env_cooperative_encirclement_reward():
    env = CooperativeHuntingEnv(capture_radius=2.0, encirclement_arms=2)
    env.reset(seed=10)

    midpoint = (env.arm_bases[0] + env.arm_bases[1]) / 2.0
    env.evasive_prey[0]["pos"] = midpoint.copy()

    # Place arm 0 and arm 1 both at capture distance from prey (within reach of their respective bases)
    env.arm_tips[0] = midpoint + np.array([0.3, 0.0], dtype=np.float32)
    env.arm_tips[1] = midpoint - np.array([0.3, 0.0], dtype=np.float32)

    actions = np.zeros(8, dtype=int)
    _, rewards, _, _, info = env.step(actions)

    # Cooperative capture should have triggered
    assert info["coop_captures"] >= 1
    assert rewards[0] > 0
    assert rewards[1] > 0
