"""Unit tests for Curriculum learning and environment transitions."""

import numpy as np
import pytest

from envs.curriculum import CurriculumScheduler, CurriculumEnv


def test_curriculum_scheduler_graduation():
    scheduler = CurriculumScheduler(
        window_size=3,
        advance_reward_thresholds=[10.0, 20.0],
        max_hazard_thresholds=[2.0, 2.0],
    )
    assert scheduler.stage == 0

    # Low rewards should not graduate
    assert not scheduler.record_episode(reward=5.0, hazard_hits=0.0, episode_idx=1)
    assert not scheduler.record_episode(reward=5.0, hazard_hits=0.0, episode_idx=2)
    assert not scheduler.record_episode(reward=5.0, hazard_hits=0.0, episode_idx=3)
    assert scheduler.stage == 0

    # High rewards meeting threshold should graduate from stage 0 -> 1
    assert not scheduler.record_episode(reward=12.0, hazard_hits=0.0, episode_idx=4)
    assert not scheduler.record_episode(reward=12.0, hazard_hits=0.0, episode_idx=5)
    graduated = scheduler.record_episode(reward=12.0, hazard_hits=0.0, episode_idx=6)
    assert graduated
    assert scheduler.stage == 1


def test_curriculum_env_stepping():
    scheduler = CurriculumScheduler(window_size=2, advance_reward_thresholds=[5.0, 10.0])
    env = CurriculumEnv(scheduler=scheduler)

    # Start at stage 0
    obs, info = env.reset(seed=42)
    assert obs.shape == (8, 16)
    assert info["curriculum_stage"] == 0

    # Step in stage 0
    actions = np.zeros(8, dtype=int)
    next_obs, rewards, term, trunc, info = env.step(actions)
    assert next_obs.shape == (8, 16)
    assert rewards.shape == (8,)

    # Manually advance to stage 1
    scheduler.set_stage(1)
    obs, info = env.reset(seed=43)
    assert info["curriculum_stage"] == 1

    # Manually advance to stage 2
    scheduler.set_stage(2)
    obs, info = env.reset(seed=44)
    assert info["curriculum_stage"] == 2
    assert "hunting_mode" in info
